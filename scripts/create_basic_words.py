#!/usr/bin/env python3
"""
Create a basic word emotion database for common words
This will allow the system to analyze speech and learn new words through the training system
"""

import json
from pathlib import Path

# Common words with basic emotion profiles
basic_words = {
    'a': [
        {'word': 'a', 'emotion': 'neutral'},
        {'word': 'amazing', 'emotion': 'joy'},
        {'word': 'angry', 'emotion': 'anger'},
        {'word': 'awesome', 'emotion': 'joy'},
        {'word': 'afraid', 'emotion': 'fear'},
        {'word': 'and', 'emotion': 'neutral'},
    ],
    'b': [
        {'word': 'bad', 'emotion': 'sadness'},
        {'word': 'beautiful', 'emotion': 'joy'},
        {'word': 'big', 'emotion': 'neutral'},
        {'word': 'be', 'emotion': 'neutral'},
        {'word': 'but', 'emotion': 'neutral'},
    ],
    'c': [
        {'word': 'can', 'emotion': 'neutral'},
        {'word': 'cool', 'emotion': 'joy'},
        {'word': 'crazy', 'emotion': 'surprise'},
        {'word': 'call', 'emotion': 'neutral'},
    ],
    'd': [
        {'word': 'do', 'emotion': 'neutral'},
        {'word': 'does', 'emotion': 'neutral'},
        {'word': 'did', 'emotion': 'neutral'},
        {'word': 'down', 'emotion': 'neutral'},
        {'word': 'disgusting', 'emotion': 'disgust'},
    ],
    'e': [
        {'word': 'excited', 'emotion': 'joy'},
        {'word': 'excellent', 'emotion': 'joy'},
        {'word': 'every', 'emotion': 'neutral'},
    ],
    'f': [
        {'word': 'fantastic', 'emotion': 'joy'},
        {'word': 'for', 'emotion': 'neutral'},
        {'word': 'from', 'emotion': 'neutral'},
        {'word': 'frightened', 'emotion': 'fear'},
    ],
    'g': [
        {'word': 'good', 'emotion': 'joy'},
        {'word': 'great', 'emotion': 'joy'},
        {'word': 'go', 'emotion': 'neutral'},
        {'word': 'get', 'emotion': 'neutral'},
    ],
    'l': [
        {'word': 'love', 'emotion': 'joy'},
        {'word': 'like', 'emotion': 'joy'},
        {'word': 'look', 'emotion': 'neutral'},
    ],
    'm': [
        {'word': 'me', 'emotion': 'neutral'},
        {'word': 'my', 'emotion': 'neutral'},
        {'word': 'make', 'emotion': 'neutral'},
        {'word': 'meeting', 'emotion': 'neutral'},
    ],
    'n': [
        {'word': 'need', 'emotion': 'neutral'},
        {'word': 'new', 'emotion': 'anticipation'},
        {'word': 'nice', 'emotion': 'joy'},
        {'word': 'no', 'emotion': 'neutral'},
        {'word': 'not', 'emotion': 'neutral'},
    ],
    'o': [
        {'word': 'of', 'emotion': 'neutral'},
        {'word': 'on', 'emotion': 'neutral'},
        {'word': 'okay', 'emotion': 'neutral'},
        {'word': 'ok', 'emotion': 'neutral'},
    ],
    'p': [
        {'word': 'please', 'emotion': 'trust'},
        {'word': 'perfect', 'emotion': 'joy'},
    ],
    's': [
        {'word': 'sad', 'emotion': 'sadness'},
        {'word': 'schedule', 'emotion': 'neutral'},
        {'word': 'so', 'emotion': 'neutral'},
        {'word': 'surprised', 'emotion': 'surprise'},
    ],
    'w': [
        {'word': 'want', 'emotion': 'anticipation'},
        {'word': 'will', 'emotion': 'anticipation'},
        {'word': 'with', 'emotion': 'neutral'},
        {'word': 'wonderful', 'emotion': 'joy'},
        {'word': 'work', 'emotion': 'neutral'},
    ],
    'y': [
        {'word': 'yes', 'emotion': 'joy'},
        {'word': 'you', 'emotion': 'neutral'},
        {'word': 'your', 'emotion': 'neutral'},
    ]
}

# Emotion mappings
emotion_profiles = {
    'joy': {
        'valence': 0.9, 'arousal': 0.7, 'dominance': 0.6,
        'emotion_probs': {'joy': 0.7, 'trust': 0.15, 'anticipation': 0.1, 'surprise': 0.025, 'anger': 0.005, 'fear': 0.005, 'sadness': 0.005, 'disgust': 0.005},
        'sentiment': {'polarity': 'positive', 'strength': 0.8}
    },
    'anger': {
        'valence': 0.1, 'arousal': 0.9, 'dominance': 0.8,
        'emotion_probs': {'anger': 0.7, 'disgust': 0.15, 'fear': 0.1, 'sadness': 0.025, 'joy': 0.005, 'trust': 0.005, 'anticipation': 0.005, 'surprise': 0.005},
        'sentiment': {'polarity': 'negative', 'strength': 0.9}
    },
    'sadness': {
        'valence': 0.2, 'arousal': 0.3, 'dominance': 0.2,
        'emotion_probs': {'sadness': 0.7, 'fear': 0.15, 'anger': 0.1, 'disgust': 0.025, 'joy': 0.005, 'trust': 0.005, 'anticipation': 0.005, 'surprise': 0.005},
        'sentiment': {'polarity': 'negative', 'strength': 0.8}
    },
    'fear': {
        'valence': 0.2, 'arousal': 0.8, 'dominance': 0.1,
        'emotion_probs': {'fear': 0.7, 'sadness': 0.15, 'surprise': 0.1, 'anger': 0.025, 'joy': 0.005, 'trust': 0.005, 'anticipation': 0.005, 'disgust': 0.005},
        'sentiment': {'polarity': 'negative', 'strength': 0.7}
    },
    'surprise': {
        'valence': 0.6, 'arousal': 0.8, 'dominance': 0.4,
        'emotion_probs': {'surprise': 0.6, 'anticipation': 0.2, 'joy': 0.1, 'fear': 0.05, 'trust': 0.025, 'anger': 0.01, 'sadness': 0.01, 'disgust': 0.005},
        'sentiment': {'polarity': 'neutral', 'strength': 0.6}
    },
    'disgust': {
        'valence': 0.1, 'arousal': 0.6, 'dominance': 0.6,
        'emotion_probs': {'disgust': 0.7, 'anger': 0.2, 'sadness': 0.05, 'fear': 0.025, 'joy': 0.005, 'trust': 0.005, 'anticipation': 0.01, 'surprise': 0.005},
        'sentiment': {'polarity': 'negative', 'strength': 0.8}
    },
    'trust': {
        'valence': 0.7, 'arousal': 0.4, 'dominance': 0.6,
        'emotion_probs': {'trust': 0.6, 'joy': 0.2, 'anticipation': 0.1, 'surprise': 0.05, 'anger': 0.01, 'fear': 0.01, 'sadness': 0.01, 'disgust': 0.01},
        'sentiment': {'polarity': 'positive', 'strength': 0.6}
    },
    'anticipation': {
        'valence': 0.6, 'arousal': 0.7, 'dominance': 0.7,
        'emotion_probs': {'anticipation': 0.6, 'joy': 0.2, 'surprise': 0.1, 'trust': 0.05, 'fear': 0.025, 'anger': 0.01, 'sadness': 0.01, 'disgust': 0.005},
        'sentiment': {'polarity': 'positive', 'strength': 0.5}
    },
    'neutral': {
        'valence': 0.5, 'arousal': 0.5, 'dominance': 0.5,
        'emotion_probs': {'joy': 0.125, 'trust': 0.125, 'anticipation': 0.125, 'surprise': 0.125, 'anger': 0.125, 'fear': 0.125, 'sadness': 0.125, 'disgust': 0.125},
        'sentiment': {'polarity': 'neutral', 'strength': 0.5}
    }
}

def create_word_entry(word, emotion):
    """Create a word entry with emotion profile"""
    profile = emotion_profiles[emotion]
    
    return {
        "word": word,
        "stats": {
            "pos": ["unknown"],
            "vad": {
                "valence": profile['valence'],
                "arousal": profile['arousal'],
                "dominance": profile['dominance']
            },
            "emotion_probs": profile['emotion_probs'],
            "sentiment": profile['sentiment'],
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
    }

def main():
    """Create basic word files"""
    words_dir = Path("words")
    words_dir.mkdir(exist_ok=True)
    
    print("🔤 Creating basic word emotion database...")
    
    for letter, words in basic_words.items():
        file_path = words_dir / f"{letter}.json"
        
        word_entries = []
        for word_info in words:
            word_entry = create_word_entry(word_info['word'], word_info['emotion'])
            word_entries.append(word_entry)
        
        file_data = {"words": word_entries}
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(file_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Created {file_path} with {len(word_entries)} words")
    
    # Create empty files for other letters
    for letter in 'efgjklmnopqrstuvwxyz':
        if letter not in basic_words:
            file_path = words_dir / f"{letter}.json"
            if not file_path.exists():
                file_data = {"words": []}
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(file_data, f, indent=2, ensure_ascii=False)
    
    # Create numbers and symbols files
    for filename in ['numbers.json', 'symbols.json']:
        file_path = words_dir / filename
        if not file_path.exists():
            file_data = {"words": []}
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(file_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎉 Basic word database created!")
    print(f"📊 Ready to analyze speech and learn new words through training!")
    print(f"💡 The system will now process words you speak and learn from corrections!")

if __name__ == "__main__":
    main()
