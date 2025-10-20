#!/usr/bin/env python3
"""
Batch Word Processor - Processes ALL words in a phrase simultaneously through DeepSeek thinking
"""

import json
import requests
import concurrent.futures
import threading
from pathlib import Path
import time
from typing import Dict, List, Optional

class BatchWordProcessor:
    def __init__(self):
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.api_key = "your-api-key-here"
        self.model = "deepseek-chat"
        
        # Cache for processed words
        self.word_cache = {}
        self.cache_lock = threading.Lock()
        
        # File locks for thread-safe saving
        self.file_locks = {}
        for letter in 'abcdefghijklmnopqrstuvwxyz':
            self.file_locks[f"{letter}.json"] = threading.Lock()
        self.file_locks["numbers.json"] = threading.Lock()
        self.file_locks["symbols.json"] = threading.Lock()
        
        # Load existing words
        self.load_existing_words()
        
        print(f"🚀 Batch Word Processor initialized with {len(self.word_cache)} existing words")
    
    def load_existing_words(self):
        """Load existing words into cache"""
        words_dir = Path("words")
        
        for json_file in words_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for entry in data.get('words', []):
                        word = entry.get('word', '').lower()
                        if word:
                            self.word_cache[word] = entry['stats']
            except:
                continue
    
    def get_filename_for_word(self, word: str) -> str:
        """Get filename for a word"""
        first_char = word[0].lower()
        if first_char.isalpha():
            return f"{first_char}.json"
        elif first_char.isdigit():
            return "numbers.json"
        else:
            return "symbols.json"
    
    def process_single_word_with_thinking(self, word: str) -> Optional[Dict]:
        """Process single word through DeepSeek with deep thinking"""
        
        prompt = f"""Analyze the word "{word}" for its emotional connotations and psychological impact.

Think deeply about:
1. What emotions does this word typically evoke in people?
2. Is it positive, negative, or neutral in feeling (valence)?
3. How energetic or calm does it make people feel (arousal)?
4. Does it convey power/control or submission (dominance)?
5. What is the overall sentiment and strength?
6. Any social or cultural associations?

Based on your analysis, provide the emotion data in this exact JSON format:

{{
  "word": "{word}",
  "stats": {{
    "pos": ["noun"],
    "vad": {{
      "valence": 0.5,
      "arousal": 0.5,
      "dominance": 0.5
    }},
    "emotion_probs": {{
      "joy": 0.125,
      "trust": 0.125,
      "anticipation": 0.125,
      "surprise": 0.125,
      "anger": 0.125,
      "fear": 0.125,
      "sadness": 0.125,
      "disgust": 0.125
    }},
    "sentiment": {{
      "polarity": "neutral",
      "strength": 0.5
    }},
    "social_axes": {{
      "good_bad": 0.0,
      "warmth_cold": 0.0,
      "competence_incompetence": 0.0,
      "active_passive": 0.0
    }},
    "toxicity": 0.0,
    "dynamics": {{
      "negation_flip_probability": 0.0,
      "sarcasm_flip_probability": 0.0
    }}
  }}
}}

Rules:
- emotion_probs must sum to 1.0
- vad values: 0.0 to 1.0 (valence: negative to positive, arousal: calm to energetic, dominance: submissive to dominant)
- social_axes values: -1.0 to 1.0
- Return ONLY the JSON, no explanation"""

        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 800
                },
                timeout=45  # Longer timeout for thinking
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content'].strip()
                
                # Clean response
                if content.startswith('```json'):
                    content = content.replace('```json', '').replace('```', '').strip()
                elif content.startswith('```'):
                    lines = content.split('\n')
                    for line in lines:
                        if line.strip().startswith('{"word"'):
                            content = line.strip()
                            break
                
                word_data = json.loads(content)
                return word_data
                
        except Exception as e:
            print(f"❌ Error processing '{word}': {e}")
            return None
    
    def save_word_to_file(self, word_data: Dict) -> bool:
        """Save word data to appropriate file"""
        word = word_data.get('word', '')
        if not word:
            return False
        
        filename = self.get_filename_for_word(word)
        filepath = Path("words") / filename
        
        with self.file_locks[filename]:
            try:
                # Load existing data
                if filepath.exists():
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    data = {"words": []}
                
                # Check if word already exists
                existing_words = {entry.get('word', '') for entry in data.get('words', [])}
                if word in existing_words:
                    return True  # Already exists
                
                # Add new word
                data['words'].append(word_data)
                
                # Sort words alphabetically
                data['words'].sort(key=lambda x: x.get('word', '').lower())
                
                # Save
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                return True
                
            except Exception as e:
                print(f"❌ Error saving '{word}': {e}")
                return False
    
    def process_phrase_batch(self, text: str) -> Dict:
        """Process ALL words in phrase simultaneously through DeepSeek thinking"""
        words = text.split()
        clean_words = []
        
        # Get unique clean words that need processing
        for word in words:
            clean_word = ''.join(c for c in word.lower() if c.isalnum())
            if clean_word and len(clean_word) > 1:  # Skip very short words
                clean_words.append(clean_word)
        
        # Remove duplicates while preserving order
        unique_words = list(dict.fromkeys(clean_words))
        
        # Check which words need processing
        words_to_process = []
        with self.cache_lock:
            for word in unique_words:
                if word not in self.word_cache:
                    words_to_process.append(word)
        
        print(f"🔍 Processing phrase: '{text}'")
        print(f"📊 Words to analyze: {len(words_to_process)} new words")
        
        # Process all new words simultaneously
        if words_to_process:
            print(f"🚀 BATCH PROCESSING: Analyzing {len(words_to_process)} words simultaneously...")
            
            # Use ThreadPoolExecutor for parallel processing
            processed_words = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(words_to_process)) as executor:
                # Submit all words for processing
                future_to_word = {
                    executor.submit(self.process_single_word_with_thinking, word): word 
                    for word in words_to_process
                }
                
                # Collect results
                for future in concurrent.futures.as_completed(future_to_word):
                    word = future_to_word[future]
                    try:
                        word_data = future.result()
                        if word_data:
                            processed_words[word] = word_data
                            print(f"✅ Processed '{word}' → {word_data['stats']['emotion_probs']}")
                        else:
                            print(f"❌ Failed to process '{word}'")
                    except Exception as e:
                        print(f"❌ Error with '{word}': {e}")
            
            # Save all processed words to files
            print(f"💾 BATCH SAVING: Saving {len(processed_words)} words to files...")
            for word, word_data in processed_words.items():
                if self.save_word_to_file(word_data):
                    # Add to cache
                    with self.cache_lock:
                        self.word_cache[word] = word_data['stats']
                    print(f"💾 Saved '{word}' to {self.get_filename_for_word(word)}")
        
        # Now analyze the phrase with all available data
        return self.analyze_phrase_with_cache(text, words)
    
    def analyze_phrase_with_cache(self, text: str, original_words: List[str]) -> Dict:
        """Analyze phrase using cached word data"""
        found_words = []
        word_emotions = []
        word_analysis = []
        
        # Analyze each word
        for word in original_words:
            clean_word = ''.join(c for c in word.lower() if c.isalnum())
            
            with self.cache_lock:
                emotion_data = self.word_cache.get(clean_word)
            
            if emotion_data:
                found_words.append(clean_word)
                word_emotions.append(emotion_data)
                
                # Get dominant emotion
                dominant_emotion = max(emotion_data["emotion_probs"], key=emotion_data["emotion_probs"].get)
                confidence = emotion_data["emotion_probs"][dominant_emotion]
                
                word_analysis.append({
                    "word": word,
                    "clean_word": clean_word,
                    "emotion": dominant_emotion,
                    "confidence": confidence,
                    "valence": emotion_data["vad"]["valence"],
                    "arousal": emotion_data["vad"]["arousal"],
                    "sentiment": emotion_data["sentiment"]["polarity"],
                    "found": True
                })
            else:
                # Word not processed
                word_analysis.append({
                    "word": word,
                    "clean_word": clean_word,
                    "emotion": "neutral",
                    "confidence": 0.125,
                    "valence": 0.5,
                    "arousal": 0.5,
                    "sentiment": "neutral",
                    "found": False
                })
        
        # Calculate phrase emotion based on WORD COUNT (not percentages)
        if word_emotions:
            # Count which emotion is dominant for each word
            emotion_counts = {"joy": 0, "trust": 0, "anticipation": 0, "surprise": 0, "anger": 0, "fear": 0, "sadness": 0, "disgust": 0}
            
            for word_data in word_emotions:
                # Find the dominant emotion for this word
                word_dominant = max(word_data["emotion_probs"], key=word_data["emotion_probs"].get)
                emotion_counts[word_dominant] += 1
            
            # The phrase emotion is the one with the most words
            dominant_emotion = max(emotion_counts, key=emotion_counts.get)
            dominant_word_count = emotion_counts[dominant_emotion]
            
            # Calculate confidence as ratio of dominant words to total words
            confidence = dominant_word_count / len(word_emotions) if word_emotions else 0
            
            # Still calculate average emotions for detailed breakdown
            emotions = {}
            for emotion in ["joy", "trust", "anticipation", "surprise", "anger", "fear", "sadness", "disgust"]:
                values = [w["emotion_probs"][emotion] for w in word_emotions]
                emotions[emotion] = sum(values) / len(values)
            
            # Aggregate VAD
            vad = {}
            for vad_dim in ["valence", "arousal", "dominance"]:
                values = [w["vad"][vad_dim] for w in word_emotions]
                vad[vad_dim] = sum(values) / len(values)
            
            # Determine sentiment
            positive_words = sum(1 for w in word_emotions if w["sentiment"]["polarity"] == "positive")
            negative_words = sum(1 for w in word_emotions if w["sentiment"]["polarity"] == "negative")
            
            if positive_words > negative_words:
                sentiment_polarity = "positive"
            elif negative_words > positive_words:
                sentiment_polarity = "negative"
            else:
                sentiment_polarity = "neutral"
            
            strength_values = [w["sentiment"]["strength"] for w in word_emotions]
            sentiment_strength = sum(strength_values) / len(strength_values)
            
            print(f"📊 Emotion word counts: {emotion_counts}")
            print(f"🎯 Dominant emotion: {dominant_emotion} ({dominant_word_count}/{len(word_emotions)} words = {confidence:.1%})")
            
        else:
            # No words processed - use neutral
            emotions = {emotion: 0.125 for emotion in ["joy", "trust", "anticipation", "surprise", "anger", "fear", "sadness", "disgust"]}
            vad = {"valence": 0.5, "arousal": 0.5, "dominance": 0.5}
            sentiment_polarity = "neutral"
            sentiment_strength = 0.5
            dominant_emotion = "neutral"
            confidence = 0.125
        
        # Add emotion word counts to the response
        emotion_word_counts = {}
        if word_emotions:
            emotion_word_counts = {"joy": 0, "trust": 0, "anticipation": 0, "surprise": 0, "anger": 0, "fear": 0, "sadness": 0, "disgust": 0}
            for word_data in word_emotions:
                word_dominant = max(word_data["emotion_probs"], key=word_data["emotion_probs"].get)
                emotion_word_counts[word_dominant] += 1
        
        return {
            "text": text,
            "word_count": len(original_words),
            "analyzed_words": len(found_words),
            "coverage": len(found_words) / len(original_words) if original_words else 0,
            "found_words": found_words,
            "word_analysis": word_analysis,
            "emotions": emotions,
            "emotion_word_counts": emotion_word_counts,  # NEW: Show word counts per emotion
            "vad": vad,
            "sentiment": {"polarity": sentiment_polarity, "strength": sentiment_strength},
            "overall_emotion": dominant_emotion,
            "confidence": confidence,
            "social_axes": {"good_bad": 0.0, "warmth_cold": 0.0, "competence_incompetence": 0.0, "active_passive": 0.0},
            "toxicity": 0.0
        }
    
    def get_cache_stats(self) -> Dict:
        """Get current cache statistics"""
        with self.cache_lock:
            return {
                "cached_words": len(self.word_cache),
                "processing_queue": 0
            }

# Global batch processor instance
batch_processor = BatchWordProcessor()

def process_text_batch(text: str) -> Dict:
    """Process text with batch word analysis"""
    return batch_processor.process_phrase_batch(text)

def get_batch_stats() -> Dict:
    """Get batch processor statistics"""
    return batch_processor.get_cache_stats()

if __name__ == "__main__":
    # Test the batch processor
    test_phrases = [
        "I am very happy and excited today",
        "This is absolutely amazing and wonderful",
        "I feel terrible and sad about this",
        "What a fantastic surprise this is"
    ]
    
    print("🧪 Testing Batch Word Processor")
    print("="*60)
    
    for phrase in test_phrases:
        print(f"\n🔍 Testing: '{phrase}'")
        start_time = time.time()
        
        result = process_text_batch(phrase)
        
        elapsed = time.time() - start_time
        print(f"⏱️  Processing time: {elapsed:.1f} seconds")
        print(f"Primary emotion: {result['overall_emotion']} ({result['confidence']:.1%})")
        print(f"Coverage: {result['analyzed_words']}/{result['word_count']} words ({result['coverage']:.1%})")
        
        # Show word analysis
        for word_data in result['word_analysis']:
            status = "✅" if word_data['found'] else "❌"
            print(f"  {status} '{word_data['word']}' → {word_data['emotion']} ({word_data['confidence']:.1%})")
    
    stats = get_batch_stats()
    print(f"\n📊 Final stats: {stats['cached_words']} words in database")
