#!/usr/bin/env python3
"""
Word Emotion Analyzer using Claude API

This system processes dictionary words through Claude AI to analyze emotional connotations
and saves the results organized by letter/symbol.
"""

import json
import os
import time
import random
import requests
from typing import Dict, List, Optional
from pathlib import Path

class WordEmotionAnalyzer:
    def __init__(self, api_key: str, words_file: str = "VoiceRelatedEmotionPrediction/WordEmotionPrediction/words.json"):
        self.api_key = api_key
        self.words_file = words_file
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-5-sonnet-20241022"
        
        # Create output directory
        self.output_dir = Path("words")
        self.output_dir.mkdir(exist_ok=True)
        
        # Load words
        self.words = self.load_words()
        self.processed_words = self.load_processed_words()
        
        # Error tracking
        self.consecutive_errors = 0
        self.max_consecutive_errors = 100
        
        # Processing stats
        self.total_processed = 0
        self.session_processed = 0
        
        # Current processing state
        self.current_words = []
        
        # Pricing tracking (Claude 3.5 Sonnet pricing)
        self.input_price_per_token = 0.000003  # $3 per million input tokens
        self.output_price_per_token = 0.000015  # $15 per million output tokens
        self.pricing_file = "pricing_data.json"
        self.pricing_data = self.load_pricing_data()
        
    def load_words(self) -> List[str]:
        """Load words from JSON file"""
        try:
            with open(self.words_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('words', [])
        except Exception as e:
            print(f"Error loading words: {e}")
            return []
    
    def load_processed_words(self) -> set:
        """Load already processed words from existing files"""
        processed = set()
        
        for file_path in self.output_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for entry in data.get('words', []):
                        processed.add(entry.get('word', ''))
            except Exception as e:
                print(f"Error loading processed words from {file_path}: {e}")
        
        return processed
    
    def load_pricing_data(self) -> Dict:
        """Load pricing data from file"""
        try:
            with open(self.pricing_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "total_cost": 0.0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "words_processed": 0,
                "sessions": []
            }
    
    def save_pricing_data(self):
        """Save pricing data to file"""
        try:
            with open(self.pricing_file, 'w', encoding='utf-8') as f:
                json.dump(self.pricing_data, f, indent=2)
        except Exception as e:
            print(f"Error saving pricing data: {e}")
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation: ~4 chars per token)"""
        return max(1, len(text) // 4)
    
    def add_word_cost(self, word: str, input_tokens: int, output_tokens: int):
        """Add cost data for a processed word"""
        input_cost = input_tokens * self.input_price_per_token
        output_cost = output_tokens * self.output_price_per_token
        total_word_cost = input_cost + output_cost
        
        self.pricing_data["total_cost"] += total_word_cost
        self.pricing_data["total_input_tokens"] += input_tokens
        self.pricing_data["total_output_tokens"] += output_tokens
        self.pricing_data["words_processed"] += 1
        
        # Add to current session
        session_entry = {
            "word": word,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": total_word_cost,
            "timestamp": str(__import__('datetime').datetime.now())
        }
        
        if not self.pricing_data.get("sessions"):
            self.pricing_data["sessions"] = []
        
        self.pricing_data["sessions"].append(session_entry)
        
        # Keep only last 1000 sessions to prevent file bloat
        if len(self.pricing_data["sessions"]) > 1000:
            self.pricing_data["sessions"] = self.pricing_data["sessions"][-1000:]
        
        self.save_pricing_data()
    
    def get_remaining_words(self) -> List[str]:
        """Get list of words that haven't been processed yet"""
        return [word for word in self.words if word not in self.processed_words]
    
    def get_file_for_word(self, word: str) -> str:
        """Determine which file a word should be saved to based on first character"""
        if not word:
            return "empty.json"
        
        first_char = word[0].lower()
        
        if first_char.isalpha():
            return f"{first_char}.json"
        elif first_char.isdigit():
            return "numbers.json"
        else:
            return "symbols.json"
    
    def make_api_request(self, word: str) -> Optional[Dict]:
        """Make API request to Claude for word emotion analysis"""
        
        prompt = f"""You label ONE English word for emotional connotation.

Output JSON ONLY with exactly two top-level keys: "word" and "stats". No prose, no preamble, no code fences, no extra keys.

Determinism
- Be deterministic; do not use randomness.
- Rate the dominant everyday sense (do not list senses).
- Never output null; provide the best calibrated estimate.

Rounding & ranges
- Two decimals for all floats.
- Unless noted: [0,1]. Axes marked [-1,1] may be negative.
- Probabilities that must sum to 1.00 must do so after rounding (adjust the largest value ±0.01 if needed).

Anchors
- VAD: valence 0.00 very negative, 0.50 neutral, 1.00 very positive; arousal 0.00 calm → 1.00 excited; dominance 0.00 powerless → 1.00 in-control.
- social_axes.* ∈ [-1,1]: good_bad, warmth_cold, competence_incompetence, active_passive.

Schema (fill every field)
{{
  "word": "<string>",
  "stats": {{
    "pos": ["<coarse POS>"],
    "vad": {{ "valence": 0.00, "arousal": 0.00, "dominance": 0.00 }},
    "emotion_probs": {{
      "joy": 0.00, "trust": 0.00, "anticipation": 0.00, "surprise": 0.00,
      "anger": 0.00, "fear": 0.00, "sadness": 0.00, "disgust": 0.00
    }},  // sum = 1.00
    "sentiment": {{ "polarity": "positive|negative|neutral|mixed", "strength": 0.00 }},
    "social_axes": {{
      "good_bad": 0.00, "warmth_cold": 0.00,
      "competence_incompetence": 0.00, "active_passive": 0.00
    }},
    "toxicity": 0.00,
    "dynamics": {{
      "negation_flip_probability": 0.00,
      "sarcasm_flip_probability": 0.00
    }}
  }}
}}

Hard validation (perform before returning)
1) emotion_probs sums to 1.00 after rounding.
2) If sentiment.polarity == "neutral", sentiment.strength ≤ 0.20.
3) Sign consistency with social_axes.good_bad (≥ +0.40 or ≤ −0.40) unless polarity == "mixed".
4) If |good_bad| ≥ 0.40 → negation_flip_probability ≥ 0.60.
Return only the JSON object.

Word: {word}"""

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            response_data = response.json()
            content = response_data.get('content', [])
            
            if content and len(content) > 0:
                text_content = content[0].get('text', '')
                
                # Track token usage for pricing
                usage = response_data.get('usage', {})
                input_tokens = usage.get('input_tokens', self.estimate_tokens(prompt))
                output_tokens = usage.get('output_tokens', self.estimate_tokens(text_content))
                
                # Parse JSON from response
                result = json.loads(text_content)
                # Ensure the word in the result matches the input word
                result['word'] = word
                
                # Add pricing information
                self.add_word_cost(word, input_tokens, output_tokens)
                
                return result
            else:
                print(f"No content in response for word: {word}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"API request error for word '{word}': {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON parsing error for word '{word}': {e}")
            return None
        except Exception as e:
            print(f"Unexpected error for word '{word}': {e}")
            return None
    
    def save_word_result(self, word_data: Dict):
        """Save word analysis result to appropriate file and remove from words.json"""
        word = word_data.get('word', '')
        filename = self.get_file_for_word(word)
        filepath = self.output_dir / filename
        
        # Load existing data or create new
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {
                "file_character": filename.replace('.json', ''),
                "word_count": 0,
                "words": []
            }
        
        # Add new word data
        data['words'].append(word_data)
        data['word_count'] = len(data['words'])
        
        # Sort words alphabetically
        data['words'].sort(key=lambda x: x.get('word', '').lower())
        
        # Save back to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Remove word from words.json
        self.remove_word_from_source(word)
        
        print(f"Saved '{word}' to {filename}")
    
    def remove_word_from_source(self, processed_word: str):
        """Remove processed word from words.json"""
        try:
            # Load current words.json
            with open(self.words_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Remove the processed word
            if processed_word in data['words']:
                data['words'].remove(processed_word)
                data['total_words'] = len(data['words'])
                
                # Save updated words.json
                with open(self.words_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Update our internal words list
                if processed_word in self.words:
                    self.words.remove(processed_word)
                    
        except Exception as e:
            print(f"Error removing word '{processed_word}' from source: {e}")
    
    def process_single_word(self) -> bool:
        """Process a single word. Returns True if successful, False if failed"""
        remaining = self.get_remaining_words()
        
        if not remaining:
            print("No more words to process!")
            return False
        
        word = remaining[0]
        
        # Add to current processing list
        self.current_words.append(word)
        
        print(f"Processing word: '{word}' ({len(remaining)} remaining)")
        
        result = self.make_api_request(word)
        
        # Remove from current processing list
        if word in self.current_words:
            self.current_words.remove(word)
        
        if result:
            self.save_word_result(result)
            self.processed_words.add(word)
            self.total_processed += 1
            self.session_processed += 1
            self.consecutive_errors = 0
            return True
        else:
            self.consecutive_errors += 1
            print(f"Failed to process '{word}' (consecutive errors: {self.consecutive_errors})")
            return False
    
    def process_batch(self, max_words: Optional[int] = None) -> int:
        """Process multiple words with error handling"""
        processed_count = 0
        remaining = self.get_remaining_words()
        
        if not remaining:
            print("No words remaining to process!")
            return 0
        
        total_to_process = min(len(remaining), max_words) if max_words else len(remaining)
        
        print(f"Starting batch processing of up to {total_to_process} words...")
        
        while remaining and (max_words is None or processed_count < max_words):
            if self.consecutive_errors >= self.max_consecutive_errors:
                print(f"Stopping due to {self.consecutive_errors} consecutive errors")
                break
            
            success = self.process_single_word()
            
            if success:
                processed_count += 1
                # Small delay between successful requests
                time.sleep(1)
            else:
                # Random delay on error (10-20 seconds)
                delay = random.randint(10, 20)
                print(f"Error occurred. Waiting {delay} seconds before retry...")
                time.sleep(delay)
            
            remaining = self.get_remaining_words()
        
        print(f"Batch processing completed. Processed {processed_count} words this batch.")
        return processed_count
    
    def get_stats(self) -> Dict:
        """Get processing statistics"""
        remaining = self.get_remaining_words()
        
        # Calculate processed words from original total minus current remaining
        try:
            with open(self.words_file, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
                current_total = len(current_data.get('words', []))
        except:
            current_total = len(self.words)
        
        # Original total was 147,323, so processed = original - current
        original_total = 147323
        processed_count = original_total - current_total
        
        # Calculate average cost per word
        avg_cost_per_word = (self.pricing_data["total_cost"] / self.pricing_data["words_processed"]) if self.pricing_data["words_processed"] > 0 else 0
        
        return {
            "total_words": original_total,
            "processed_words": processed_count,
            "remaining_words": current_total,
            "session_processed": self.session_processed,
            "consecutive_errors": self.consecutive_errors,
            "completion_percentage": (processed_count / original_total) * 100 if original_total > 0 else 0,
            "current_words": self.current_words.copy(),
            "pricing": {
                "total_cost": self.pricing_data["total_cost"],
                "words_processed": self.pricing_data["words_processed"],
                "avg_cost_per_word": avg_cost_per_word,
                "total_input_tokens": self.pricing_data["total_input_tokens"],
                "total_output_tokens": self.pricing_data["total_output_tokens"],
                "estimated_remaining_cost": avg_cost_per_word * current_total if avg_cost_per_word > 0 else 0
            }
        }
    
    def print_stats(self):
        """Print current processing statistics"""
        stats = self.get_stats()
        print("\n" + "="*50)
        print("WORD EMOTION ANALYSIS STATS")
        print("="*50)
        print(f"Total Words: {stats['total_words']:,}")
        print(f"Processed: {stats['processed_words']:,}")
        print(f"Remaining: {stats['remaining_words']:,}")
        print(f"Session Processed: {stats['session_processed']:,}")
        print(f"Completion: {stats['completion_percentage']:.2f}%")
        print(f"Consecutive Errors: {stats['consecutive_errors']}")
        
        # Current words being processed
        if stats['current_words']:
            print(f"Currently Processing: {', '.join(stats['current_words'])}")
        
        # Pricing information
        pricing = stats['pricing']
        print("\n" + "-"*25 + " PRICING " + "-"*25)
        print(f"Total Cost: ${pricing['total_cost']:.4f}")
        print(f"Words Processed for Cost: {pricing['words_processed']:,}")
        if pricing['avg_cost_per_word'] > 0:
            print(f"Average Cost per Word: ${pricing['avg_cost_per_word']:.6f}")
            print(f"Estimated Remaining Cost: ${pricing['estimated_remaining_cost']:.2f}")
        print(f"Total Input Tokens: {pricing['total_input_tokens']:,}")
        print(f"Total Output Tokens: {pricing['total_output_tokens']:,}")
        print("="*50)

def main():
    """Main function for command line usage"""
    import sys
    
    # API key
    API_KEY = "your-anthropic-api-key-here"
    
    analyzer = WordEmotionAnalyzer(API_KEY)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python word_emotion_analyzer.py single    - Process one word")
        print("  python word_emotion_analyzer.py batch     - Process words one after another")
        print("  python word_emotion_analyzer.py all       - Process as many as possible")
        print("  python word_emotion_analyzer.py stats     - Show statistics")
        return
    
    command = sys.argv[1].lower()
    
    if command == "single":
        analyzer.process_single_word()
        analyzer.print_stats()
        
    elif command == "batch":
        # Process one after another until stopped
        try:
            while analyzer.get_remaining_words():
                if analyzer.consecutive_errors >= analyzer.max_consecutive_errors:
                    break
                analyzer.process_single_word()
                time.sleep(1)  # Brief pause between words
        except KeyboardInterrupt:
            print("\nBatch processing stopped by user")
        
        analyzer.print_stats()
        
    elif command == "all":
        # Process as many as possible
        analyzer.process_batch()
        analyzer.print_stats()
        
    elif command == "stats":
        analyzer.print_stats()
        
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
