#!/usr/bin/env python3
"""
Quick test to verify word loading is working
"""

import sys
from pathlib import Path

# Add enhanced_system to path
sys.path.insert(0, str(Path(__file__).parent / "enhanced_system"))

from enhanced_speech_analyzer import EnhancedSpeechAnalyzer

def main():
    print("🧪 Testing Enhanced Speech Analyzer...")
    
    # Initialize analyzer
    analyzer = EnhancedSpeechAnalyzer()
    
    print(f"📊 Loaded {len(analyzer.word_cache)} words")
    
    # Test some words
    test_words = ['hello', 'happy', 'i', 'hope', 'test']
    
    print("\n🔍 Testing word recognition:")
    for word in test_words:
        if word in analyzer.word_cache:
            emotion_data = analyzer.word_cache[word]
            dominant_emotion = max(emotion_data["emotion_probs"], key=emotion_data["emotion_probs"].get)
            confidence = emotion_data["emotion_probs"][dominant_emotion]
            print(f"✅ '{word}' → {dominant_emotion} ({confidence:.1%})")
        else:
            print(f"❌ '{word}' → not found")
    
    # Test phrase analysis
    print("\n🎭 Testing phrase analysis:")
    test_text = "hello i am happy"
    result = analyzer.analyze_phrase_emotion(test_text)
    
    print(f"Text: '{test_text}'")
    print(f"Coverage: {result['analyzed_words']}/{result['word_count']} words")
    print(f"Overall emotion: {result['overall_emotion']} ({result['confidence']:.1%})")
    
    print("\n📝 Word-by-word analysis:")
    for word_data in result['word_analysis']:
        status = "✅" if word_data['found'] else "❌"
        print(f"  {status} '{word_data['word']}' → {word_data['emotion']} ({word_data['confidence']:.1%})")

if __name__ == "__main__":
    main()
