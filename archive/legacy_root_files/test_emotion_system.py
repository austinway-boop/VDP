
# Test the speech emotion analyzer
from speech_emotion_analyzer import SpeechEmotionAnalyzer

print("Initializing Speech Emotion Analyzer...")
analyzer = SpeechEmotionAnalyzer()
print(f"✅ Loaded {len(analyzer.word_cache)} words")

# Test text analysis
test_text = "I am very happy and excited about this new project"
print(f"\nTesting with: '{test_text}'")
result = analyzer.analyze_phrase_emotion(test_text)

print(f"Primary emotion: {result['overall_emotion']}")
print(f"Confidence: {result['confidence']:.1%}")
print(f"Sentiment: {result['sentiment']['polarity']}")
print("✅ Text analysis working!")
