#!/usr/bin/env python3
"""
Dynamic Word Processor - Processes words on-demand with DeepSeek thinking
Builds the emotion database as words are encountered in real speech
"""

import json
import requests
import threading
from pathlib import Path
import time
from typing import Dict, Optional

class DynamicWordProcessor:
    def __init__(self):
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.api_key = "your-api-key-here"
        self.model = "deepseek-chat"
        
        # Cache for processed words (in-memory for speed)
        self.word_cache = {}
        self.processing_queue = set()  # Words currently being processed
        
        # Thread safety
        self.cache_lock = threading.Lock()
        self.file_locks = {}
        
        # Create file locks for each letter
        for letter in 'abcdefghijklmnopqrstuvwxyz':
            self.file_locks[f"{letter}.json"] = threading.Lock()
        self.file_locks["numbers.json"] = threading.Lock()
        self.file_locks["symbols.json"] = threading.Lock()
        
        # Load existing words into cache
        self.load_existing_words()
        
        print(f"🚀 Dynamic Word Processor initialized with {len(self.word_cache)} existing words")
    
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
    
    def process_word_with_thinking(self, word: str) -> Optional[Dict]:
        """Process word through DeepSeek with deep thinking for accurate emotion analysis"""
        
        prompt = f"""Think deeply about the word "{word}" and analyze its emotional connotations.

Consider:
- What emotions does this word typically evoke?
- What is the valence (positive/negative feeling)?
- What is the arousal level (energy/activation)?
- What is the dominance (power/control feeling)?
- What sentiment does it convey?
- Any social/cultural associations?

Think through this carefully, then provide your analysis in this exact JSON format:

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
- vad values are 0.0 to 1.0
- social_axes values are -1.0 to 1.0
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
                    "max_tokens": 600
                },
                timeout=30
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
                
                print(f"💾 Saved '{word}' to {filename}")
                return True
                
            except Exception as e:
                print(f"❌ Error saving '{word}': {e}")
                return False
    
    def get_word_emotion(self, word: str) -> Optional[Dict]:
        """Get emotion data for word - process if not found"""
        word = word.lower().strip()
        
        # Remove punctuation
        clean_word = ''.join(c for c in word if c.isalnum())
        if not clean_word:
            return None
        
        # Check cache first
        with self.cache_lock:
            if clean_word in self.word_cache:
                return self.word_cache[clean_word]
            
            # Check if currently being processed
            if clean_word in self.processing_queue:
                return None  # Return None for now, will be available later
        
        # Process the word
        print(f"🔍 Processing new word: '{clean_word}'")
        
        with self.cache_lock:
            self.processing_queue.add(clean_word)
        
        try:
            # Process through DeepSeek with thinking
            word_data = self.process_word_with_thinking(clean_word)
            
            if word_data:
                # Save to file
                if self.save_word_to_file(word_data):
                    # Add to cache
                    with self.cache_lock:
                        self.word_cache[clean_word] = word_data['stats']
                        self.processing_queue.discard(clean_word)
                    
                    return word_data['stats']
            
        except Exception as e:
            print(f"❌ Error processing '{clean_word}': {e}")
        
        finally:
            with self.cache_lock:
                self.processing_queue.discard(clean_word)
        
        return None
    
    def analyze_phrase_dynamic(self, text: str) -> Dict:
        """Analyze phrase with dynamic word processing"""
        words = text.split()
        found_words = []
        word_emotions = []
        word_analysis = []
        
        print(f"🔍 Analyzing phrase: '{text}'")
        
        # Process each word
        for word in words:
            clean_word = word.lower().strip('.,!?;:"()[]')
            emotion_data = self.get_word_emotion(clean_word)
            
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
                # Word not found or being processed
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
        
        # Calculate phrase emotion if we have data
        if word_emotions:
            # Aggregate emotions
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
            
            # Get dominant emotion
            dominant_emotion = max(emotions, key=emotions.get)
            confidence = emotions[dominant_emotion]
            
        else:
            # No words found - use neutral
            emotions = {emotion: 0.125 for emotion in ["joy", "trust", "anticipation", "surprise", "anger", "fear", "sadness", "disgust"]}
            vad = {"valence": 0.5, "arousal": 0.5, "dominance": 0.5}
            sentiment_polarity = "neutral"
            sentiment_strength = 0.5
            dominant_emotion = "neutral"
            confidence = 0.125
        
        return {
            "text": text,
            "word_count": len(words),
            "analyzed_words": len(found_words),
            "coverage": len(found_words) / len(words) if words else 0,
            "found_words": found_words,
            "word_analysis": word_analysis,
            "emotions": emotions,
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
                "processing_queue": len(self.processing_queue),
                "queue_words": list(self.processing_queue)[:10]  # First 10 for debugging
            }

# Global processor instance
dynamic_processor = DynamicWordProcessor()

def process_text_dynamic(text: str) -> Dict:
    """Process text with dynamic word learning"""
    return dynamic_processor.analyze_phrase_dynamic(text)

def get_word_emotion_dynamic(word: str) -> Optional[Dict]:
    """Get emotion for a single word with dynamic processing"""
    return dynamic_processor.get_word_emotion(word)

if __name__ == "__main__":
    # Test the dynamic processor
    test_phrases = [
        "I am very happy today",
        "This is absolutely amazing",
        "I feel terrible and sad",
        "What a wonderful surprise"
    ]
    
    print("🧪 Testing Dynamic Word Processor")
    print("="*50)
    
    for phrase in test_phrases:
        print(f"\n🔍 Testing: '{phrase}'")
        result = process_text_dynamic(phrase)
        
        print(f"Primary emotion: {result['overall_emotion']} ({result['confidence']:.1%})")
        print(f"Coverage: {result['analyzed_words']}/{result['word_count']} words ({result['coverage']:.1%})")
        
        # Show word analysis
        for word_data in result['word_analysis']:
            status = "✓" if word_data['found'] else "⏳" if word_data['clean_word'] in dynamic_processor.processing_queue else "➕"
            print(f"  {status} '{word_data['word']}' → {word_data['emotion']}")
    
    stats = dynamic_processor.get_cache_stats()
    print(f"\n📊 Final stats: {stats['cached_words']} words cached, {stats['processing_queue']} in queue")
