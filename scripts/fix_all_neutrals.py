#!/usr/bin/env python3
"""
More aggressive neutral word fixer - fix ALL words that should be neutral
"""

import json
from pathlib import Path

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

def should_be_neutral(word):
    """Check if a word should be completely neutral"""
    word = word.lower().strip()
    
    # Function words that should always be neutral
    function_words = {
        # Pronouns
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
        'my', 'your', 'his', 'her', 'its', 'our', 'their', 'myself', 'yourself', 
        'himself', 'herself', 'itself', 'ourselves', 'themselves',
        
        # Articles & determiners
        'a', 'an', 'the', 'this', 'that', 'these', 'those', 'some', 'any', 'each', 'every',
        
        # Prepositions
        'in', 'on', 'at', 'to', 'from', 'by', 'with', 'without', 'for', 'of', 'about',
        'over', 'under', 'through', 'between', 'among', 'during', 'before', 'after',
        'into', 'onto', 'upon', 'within', 'beneath', 'beside', 'beyond', 'across',
        
        # Common verbs (auxiliary, modal, linking)
        'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'having',
        'do', 'does', 'did', 'doing', 'done',
        'will', 'would', 'could', 'should', 'can', 'may', 'might', 'must',
        'get', 'got', 'getting', 'go', 'going', 'went', 'come', 'came', 'coming',
        
        # Conjunctions
        'and', 'or', 'but', 'so', 'because', 'if', 'when', 'where', 'while', 'since',
        'although', 'though', 'unless', 'until', 'whether',
        
        # Question words
        'what', 'when', 'where', 'who', 'why', 'how', 'which', 'whose', 'whom',
        
        # Common adverbs
        'very', 'really', 'just', 'only', 'also', 'too', 'quite', 'rather', 'quite',
        'then', 'now', 'here', 'there', 'where', 'everywhere', 'somewhere', 'anywhere',
        
        # Time & place
        'today', 'tomorrow', 'yesterday', 'tonight', 'morning', 'afternoon', 'evening',
        'right', 'left', 'up', 'down', 'back', 'forward',
        
        # Common neutral nouns
        'thing', 'things', 'something', 'anything', 'nothing', 'everything',
        'time', 'day', 'week', 'month', 'year', 'hour', 'minute', 'second',
        'way', 'place', 'person', 'people', 'man', 'woman', 'child',
        'dinner', 'lunch', 'breakfast', 'food', 'water', 'house', 'home', 'room',
        'car', 'phone', 'computer', 'program', 'system', 'work', 'job', 'office',
        'meeting', 'project', 'task', 'service', 'business', 'company',
        
        # Common neutral verbs
        'say', 'said', 'saying', 'tell', 'told', 'ask', 'asked', 'think', 'thought',
        'know', 'knew', 'see', 'saw', 'look', 'looked', 'find', 'found',
        'give', 'gave', 'take', 'took', 'make', 'made', 'put', 'let', 'set',
        'use', 'used', 'try', 'tried', 'need', 'want', 'like', 'seem', 'become',
        
        # Contractions
        "i'm", "you're", "he's", "she's", "it's", "we're", "they're",
        "i've", "you've", "we've", "they've", "i'll", "you'll", "he'll", "she'll",
        "we'll", "they'll", "i'd", "you'd", "he'd", "she'd", "we'd", "they'd",
        "isn't", "aren't", "wasn't", "weren't", "haven't", "hasn't", "hadn't",
        "don't", "doesn't", "didn't", "won't", "wouldn't", "can't", "couldn't",
        "shouldn't", "mustn't", "mightn't", "shan't",
    }
    
    return word in function_words

def main():
    """Fix all words that should be neutral"""
    print("🔧 AGGRESSIVELY fixing neutral words...")
    
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
            updated = False
            for word_entry in data.get('words', []):
                word = word_entry.get('word', '').lower()
                
                if should_be_neutral(word):
                    # Check if it needs fixing
                    emotion_probs = word_entry.get('stats', {}).get('emotion_probs', {})
                    max_emotion = max(emotion_probs.values()) if emotion_probs else 0.125
                    
                    # More aggressive: fix if any emotion > 15% (instead of 20%)
                    if max_emotion > 0.15:
                        word_entry['stats'] = create_neutral_profile()
                        print(f"✅ Fixed '{word}' in {json_file.name} (was {max_emotion:.1%})")
                        fixed_count += 1
                        updated = True
            
            # Save if updated
            if updated:
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                        
        except Exception as e:
            print(f"❌ Error processing {json_file}: {e}")
    
    print(f"\n🎉 Fixed {fixed_count} neutral words!")
    print("📊 ALL function words now have equal emotion probabilities (12.5% each)")

if __name__ == "__main__":
    main()
