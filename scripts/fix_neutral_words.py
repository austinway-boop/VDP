#!/usr/bin/env python3
"""
Fix neutral words that got incorrect emotional assignments
"""

import json
from pathlib import Path

# Words that should be completely neutral
NEUTRAL_WORDS = {
    # Pronouns
    'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
    'my', 'your', 'his', 'her', 'its', 'our', 'their',
    'myself', 'yourself', 'himself', 'herself', 'itself', 'ourselves', 'themselves',
    
    # Articles
    'a', 'an', 'the',
    
    # Common verbs (to be, to have, etc.)
    'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'having',
    'do', 'does', 'did', 'doing',
    'will', 'would', 'could', 'should', 'can', 'may', 'might',
    
    # Prepositions
    'in', 'on', 'at', 'to', 'from', 'by', 'with', 'without', 'for', 'of', 'about',
    'over', 'under', 'through', 'between', 'among', 'during', 'before', 'after',
    
    # Conjunctions
    'and', 'or', 'but', 'so', 'because', 'if', 'when', 'where', 'while', 'since',
    
    # Common question words (should be neutral)
    'what', 'when', 'where', 'who', 'why', 'how', 'which',
    
    # Common adverbs that are often neutral
    'very', 'really', 'just', 'only', 'also', 'too', 'quite', 'rather', 'quite',
    
    # Numbers and time
    'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
    'today', 'tomorrow', 'yesterday', 'now', 'then', 'here', 'there',
    
    # Common neutral nouns
    'thing', 'things', 'something', 'anything', 'nothing', 'everything',
    'time', 'day', 'week', 'month', 'year',
    'way', 'place', 'person', 'people',
    'dinner', 'lunch', 'breakfast', 'food', 'water', 'house', 'home', 'room',
    'car', 'phone', 'computer', 'program', 'system', 'work', 'job',
    
    # Common neutral verbs
    'say', 'said', 'tell', 'told', 'ask', 'asked', 'think', 'thought',
    'know', 'knew', 'see', 'saw', 'look', 'looked', 'come', 'came', 'go', 'went',
    'get', 'got', 'give', 'gave', 'take', 'took', 'make', 'made', 'put', 'let'
}

def create_neutral_profile():
    """Create a completely neutral emotion profile"""
    return {
        "pos": ["neutral"],
        "vad": {
            "valence": 0.5,
            "arousal": 0.5,
            "dominance": 0.5
        },
        "emotion_probs": {
            "joy": 0.125,
            "trust": 0.125,
            "anticipation": 0.125,
            "surprise": 0.125,
            "anger": 0.125,
            "fear": 0.125,
            "sadness": 0.125,
            "disgust": 0.125
        },
        "sentiment": {
            "polarity": "neutral",
            "strength": 0.5
        },
        "social_axes": {
            "good_bad": 0.0,
            "warmth_cold": 0.0,
            "competence_incompetence": 0.0,
            "active_passive": 0.0
        },
        "toxicity": 0.0,
        "dynamics": {
            "negation_flip_probability": 0.0,
            "sarcasm_flip_probability": 0.0
        }
    }

def fix_word_in_file(filepath, word):
    """Fix a specific word in a JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Find and update the word
        updated = False
        for word_entry in data.get('words', []):
            if word_entry.get('word', '').lower() == word.lower():
                word_entry['stats'] = create_neutral_profile()
                updated = True
                print(f"✅ Fixed '{word}' in {filepath.name}")
                break
        
        if updated:
            # Save the file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        return updated
        
    except Exception as e:
        print(f"❌ Error fixing {word} in {filepath}: {e}")
        return False

def main():
    """Fix all neutral words"""
    print("🔧 Fixing neutral words that got incorrect emotional assignments...")
    
    words_dir = Path("words")
    if not words_dir.exists():
        print("❌ Words directory not found")
        return
    
    fixed_count = 0
    
    # Check all word files
    for json_file in words_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check each word in the file
            for word_entry in data.get('words', []):
                word = word_entry.get('word', '').lower()
                
                if word in NEUTRAL_WORDS:
                    # Check if it needs fixing (has non-neutral emotions)
                    emotion_probs = word_entry.get('stats', {}).get('emotion_probs', {})
                    
                    # Check if any emotion is significantly higher than 0.125 (neutral)
                    max_emotion = max(emotion_probs.values()) if emotion_probs else 0.125
                    
                    if max_emotion > 0.2:  # If any emotion is > 20%, it needs fixing (more aggressive)
                        if fix_word_in_file(json_file, word):
                            fixed_count += 1
                        
        except Exception as e:
            print(f"❌ Error processing {json_file}: {e}")
    
    print(f"\n🎉 Fixed {fixed_count} neutral words!")
    print("📊 Neutral words now have equal emotion probabilities (12.5% each)")
    print("🔄 Restart the server to load the updated word database")

if __name__ == "__main__":
    main()
