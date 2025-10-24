#!/usr/bin/env python3
"""
Batch Word Processor - Processes ALL words in a phrase simultaneously through DeepSeek thinking
"""

import json
import os
import requests
import concurrent.futures
import threading
from pathlib import Path
import time
from typing import Dict, List, Optional

class BatchWordProcessor:
    def __init__(self):
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "your-deepseek-api-key-here")
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
        # Look for words directory in parent directory (main project root)
        words_dir = Path(__file__).parent.parent / "words"
        if not words_dir.exists():
            words_dir = Path("words")  # Fallback to current directory
        
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

GOAL: Create ACCURATE and DISTINCTIVE emotion predictions that clearly differentiate between emotions.

Think deeply about:
1. What emotions does this word typically evoke in people?
2. Is it positive, negative, or neutral in feeling (valence)?
3. How energetic or calm does it make people feel (arousal)?
4. Does it convey power/control or submission (dominance)?
5. What is the overall sentiment and strength?
6. Any social or cultural associations?

EMOTION ASSIGNMENT RULES:
- BE DECISIVE: If a word has emotional content, make it CLEAR in the probabilities
- NEUTRAL words (pronouns, articles, prepositions): Use equal probabilities (0.125 each)
- EMOTIONAL words: Give the primary emotion 0.4-0.7, secondary 0.1-0.3, others 0.01-0.05
- STRONG emotional words: Primary emotion should be 0.6+
- MODERATE emotional words: Primary emotion should be 0.4-0.6
- WEAK emotional words: Primary emotion should be 0.25-0.4

EXAMPLES:
- "happy" → joy: 0.7, trust: 0.1, anticipation: 0.1, others: 0.025 each
- "angry" → anger: 0.65, disgust: 0.15, fear: 0.1, others: 0.025 each  
- "the" → all emotions: 0.125 each (neutral)
- "love" → joy: 0.6, trust: 0.2, anticipation: 0.1, others: 0.025 each
- "terrible" → sadness: 0.4, disgust: 0.3, fear: 0.2, others: 0.025 each

CRITICAL: Make emotion predictions DISTINCTIVE and ACCURATE. Avoid giving everything 0.125 - be decisive!

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
        # Use the same words directory logic
        words_dir = Path(__file__).parent.parent / "words"
        if not words_dir.exists():
            words_dir = Path("words")
        filepath = words_dir / filename
        
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
        
        # Enhanced emotion calculation with confidence filtering and amplification
        if word_emotions:
            # Filter out low-confidence words (basically neutral/uncertain words)
            CONFIDENCE_THRESHOLD = 0.25  # Only include words with >25% confidence in their dominant emotion
            
            confident_words = []
            filtered_words = []
            
            for word_data in word_emotions:
                word_probs = word_data["emotion_probs"]
                dominant_emotion = max(word_probs, key=word_probs.get)
                dominant_score = word_probs[dominant_emotion]
                
                if dominant_score > CONFIDENCE_THRESHOLD:
                    confident_words.append(word_data)
                    print(f"✅ Including '{word_data.get('word', 'unknown')}': {dominant_emotion} ({dominant_score:.1%})")
                else:
                    filtered_words.append(word_data.get('word', 'unknown'))
                    print(f"🚫 Filtering out '{word_data.get('word', 'unknown')}': too uncertain ({dominant_score:.1%})")
            
            if filtered_words:
                print(f"📝 Filtered out {len(filtered_words)} low-confidence words: {filtered_words}")
            
            # Only use confident words for emotion calculation
            if confident_words:
                print(f"🎯 Using {len(confident_words)} confident words out of {len(word_emotions)} total")
                
                # Method 1: Weighted emotion scoring with only confident words
                emotion_weights = {"joy": 0, "trust": 0, "anticipation": 0, "surprise": 0, "anger": 0, "fear": 0, "sadness": 0, "disgust": 0}
                
                for word_data in confident_words:
                    word_probs = word_data["emotion_probs"]
                    
                    # Find the dominant emotion for this word
                    dominant_emotion = max(word_probs, key=word_probs.get)
                    dominant_score = word_probs[dominant_emotion]
                    
                    # Amplify strong emotions even more since we're only using confident words
                    if dominant_score > 0.5:  # Very strong emotional word
                        amplification_factor = 3.0
                    elif dominant_score > 0.3:  # Strong emotional word
                        amplification_factor = 2.5
                    else:  # Moderate emotional word (still above threshold)
                        amplification_factor = 2.0
                    
                    # Apply weighted scoring
                    for emotion in emotion_weights:
                        base_score = word_probs[emotion]
                        if emotion == dominant_emotion:
                            # Amplify the dominant emotion
                            weighted_score = base_score * amplification_factor
                        else:
                            # Normal scoring for non-dominant emotions
                            weighted_score = base_score
                        
                        emotion_weights[emotion] += weighted_score
            
                # Normalize the weighted scores
                total_weight = sum(emotion_weights.values())
                if total_weight > 0:
                    emotions = {emotion: weight / total_weight for emotion, weight in emotion_weights.items()}
                else:
                    emotions = {emotion: 0.125 for emotion in emotion_weights}
                
                # Apply context-based adjustments
                emotions = self.apply_context_adjustments(emotions, found_words, text)
                
                # Re-normalize after adjustments
                total_emotion = sum(emotions.values())
                if total_emotion > 0:
                    emotions = {emotion: score / total_emotion for emotion, score in emotions.items()}
                
                # Get the strongest emotion
                dominant_emotion = max(emotions, key=emotions.get)
                confidence = emotions[dominant_emotion]
                
                print(f"🎯 CONFIDENT WORDS method: {dominant_emotion} ({confidence:.1%})")
                print(f"📊 Final emotion scores: {dict(sorted(emotions.items(), key=lambda x: x[1], reverse=True))}")
                
            else:
                # No confident words found - return neutral
                print("🚫 No confident words found - returning neutral analysis")
                emotions = {"joy": 0.125, "trust": 0.125, "anticipation": 0.125, "surprise": 0.125, "anger": 0.125, "fear": 0.125, "sadness": 0.125, "disgust": 0.125}
                dominant_emotion = "neutral"
                confidence = 0.125
            
            # Count-based verification for consistency (only confident words)
            emotion_counts = {"joy": 0, "trust": 0, "anticipation": 0, "surprise": 0, "anger": 0, "fear": 0, "sadness": 0, "disgust": 0}
            for word_data in confident_words:
                word_dominant = max(word_data["emotion_probs"], key=word_data["emotion_probs"].get)
                emotion_counts[word_dominant] += 1
            
            print(f"📊 Confident word counts: {emotion_counts}")
            
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
            
        else:
            # No words processed - use neutral
            emotions = {emotion: 0.125 for emotion in ["joy", "trust", "anticipation", "surprise", "anger", "fear", "sadness", "disgust"]}
            vad = {"valence": 0.5, "arousal": 0.5, "dominance": 0.5}
            sentiment_polarity = "neutral"
            sentiment_strength = 0.5
            dominant_emotion = "neutral"
            confidence = 0.125
        
        # Add emotion word counts and prepare word analysis for display
        emotion_word_counts = {}
        display_word_analysis = []
        
        if word_emotions:
            emotion_word_counts = {"joy": 0, "trust": 0, "anticipation": 0, "surprise": 0, "anger": 0, "fear": 0, "sadness": 0, "disgust": 0}
            
            # Include ALL words in display analysis (for UI word breakdown)
            for word_data in word_analysis:
                if word_data.get('found', False):
                    # Count confident words for statistics only
                    word_confidence = word_data.get('confidence', 0)
                    if word_confidence > 0.25:  # Statistics threshold
                        emotion_word_counts[word_data['emotion']] += 1
                    
                    # But include ALL found words in display
                    display_word_analysis.append(word_data)
                else:
                    # Keep unfound words as-is
                    display_word_analysis.append(word_data)
        else:
            # No emotions found, but still show all words as neutral for display
            display_word_analysis = word_analysis
        
        return {
            "text": text,
            "word_count": len(original_words),
            "analyzed_words": len(found_words),
            "confident_words": len([w for w in display_word_analysis if w.get('emotion') not in ['neutral', 'filtered']]),
            "coverage": len(found_words) / len(original_words) if original_words else 0,
            "found_words": found_words,
            "word_analysis": display_word_analysis,  # All words for display
            "emotions": emotions,
            "emotion_word_counts": emotion_word_counts,  # Only confident word counts
            "vad": vad,
            "sentiment": {"polarity": sentiment_polarity, "strength": sentiment_strength},
            "overall_emotion": dominant_emotion,
            "confidence": confidence,
            "social_axes": {"good_bad": 0.0, "warmth_cold": 0.0, "competence_incompetence": 0.0, "active_passive": 0.0},
            "toxicity": 0.0
        }
    
    def apply_context_adjustments(self, emotions: Dict[str, float], found_words: List[str], text: str) -> Dict[str, float]:
        """Apply context-based adjustments to improve accuracy"""
        adjusted_emotions = emotions.copy()
        
        # Convert to lowercase for pattern matching
        text_lower = text.lower()
        found_words_lower = [word.lower() for word in found_words]
        
        # Context patterns that boost specific emotions
        context_patterns = {
            "anger": [
                ["hate", "angry", "mad", "furious", "rage", "pissed"],
                ["damn", "shit", "fuck", "stupid", "idiot"],
                ["kill", "destroy", "break", "smash"]
            ],
            "joy": [
                ["love", "happy", "excited", "amazing", "wonderful", "great"],
                ["yes", "awesome", "fantastic", "perfect", "brilliant"],
                ["laugh", "smile", "fun", "celebrate", "party"]
            ],
            "sadness": [
                ["sad", "cry", "tears", "depressed", "miserable", "awful"],
                ["sorry", "apologize", "regret", "disappointed"],
                ["death", "died", "gone", "lost", "miss"]
            ],
            "fear": [
                ["scared", "afraid", "terrified", "worried", "anxious"],
                ["danger", "threat", "risk", "unsafe", "panic"],
                ["help", "emergency", "urgent", "crisis"]
            ],
            "surprise": [
                ["wow", "omg", "incredible", "unbelievable", "shocking"],
                ["sudden", "unexpected", "surprised", "amazed"],
                ["what", "how", "really", "seriously"]
            ],
            "disgust": [
                ["gross", "disgusting", "nasty", "awful", "terrible"],
                ["sick", "vomit", "puke", "yuck", "ew"],
                ["dirty", "filthy", "contaminated"]
            ],
            "trust": [
                ["trust", "believe", "reliable", "honest", "faithful"],
                ["friend", "loyal", "dependable", "confident"],
                ["sure", "certain", "guarantee", "promise"]
            ],
            "anticipation": [
                ["excited", "can't wait", "looking forward", "expecting"],
                ["soon", "coming", "about to", "ready", "prepare"],
                ["hope", "wish", "want", "need", "desire"]
            ]
        }
        
        # Apply pattern-based boosts
        for emotion, pattern_groups in context_patterns.items():
            boost_factor = 0.0
            
            for patterns in pattern_groups:
                matches = sum(1 for pattern in patterns if pattern in text_lower)
                if matches > 0:
                    # Boost based on number of matches
                    boost_factor += matches * 0.15
            
            # Apply boost
            if boost_factor > 0:
                adjusted_emotions[emotion] = min(adjusted_emotions[emotion] + boost_factor, 0.8)
                print(f"🔥 Context boost for {emotion}: +{boost_factor:.2f}")
        
        # Intensity modifiers
        intensity_boosters = ["very", "extremely", "really", "so", "totally", "absolutely", "completely"]
        intensity_dampeners = ["slightly", "somewhat", "kind of", "sort of", "a bit", "maybe"]
        
        intensity_multiplier = 1.0
        for booster in intensity_boosters:
            if booster in text_lower:
                intensity_multiplier += 0.2
        
        for dampener in intensity_dampeners:
            if dampener in text_lower:
                intensity_multiplier -= 0.1
        
        # Apply intensity adjustments to the dominant emotion
        if intensity_multiplier != 1.0:
            dominant_emotion = max(adjusted_emotions, key=adjusted_emotions.get)
            adjusted_emotions[dominant_emotion] *= intensity_multiplier
            adjusted_emotions[dominant_emotion] = min(adjusted_emotions[dominant_emotion], 0.9)
            print(f"🎚️ Intensity adjustment for {dominant_emotion}: {intensity_multiplier:.2f}x")
        
        return adjusted_emotions
    
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
    print(f"\n🔍 BATCH PROCESSOR DEBUG - process_text_batch")
    print(f"   Input text: '{text}'")
    print(f"   Text length: {len(text) if text else 0}")
    
    result = batch_processor.process_phrase_batch(text)
    
    print(f"   📊 Batch processor result:")
    print(f"      Word count: {result.get('word_count', 0)}")
    print(f"      Analyzed words: {result.get('analyzed_words', 0)}")
    print(f"      Word analysis length: {len(result.get('word_analysis', []))}")
    print(f"      Coverage: {result.get('coverage', 0):.1%}")
    print(f"      Primary emotion: {result.get('overall_emotion', 'unknown')}")
    print(f"🔍 BATCH PROCESSOR DEBUG - process_text_batch COMPLETE")
    
    return result

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
