#!/usr/bin/env python3
"""
Test the actual API call that the UI makes
"""

import requests
import json
from pathlib import Path

def test_api():
    """Test the analyze-audio API with a real audio file"""
    
    # Find an audio file to test with
    audio_files = list(Path("training_data/uncertain_clips").glob("*.wav"))
    if not audio_files:
        print("❌ No audio files found for testing")
        return
    
    test_file = audio_files[0]
    print(f"🎤 Testing API with: {test_file}")
    
    try:
        # Make the same API call the UI makes
        with open(test_file, 'rb') as f:
            files = {'audio': f}
            
            print("📡 Making API call to analyze-audio...")
            response = requests.post(
                'http://localhost:5003/api/analyze-audio',
                files=files,
                timeout=30
            )
            
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ API call successful!")
                
                if result.get('success'):
                    data = result['result']
                    print(f"\n📝 Transcription: '{data.get('transcription', 'None')}'")
                    print(f"🎯 Confidence: {data.get('confidence', 0):.2%}")
                    print(f"⚠️  Needs review: {data.get('needs_review', False)}")
                    
                    emotion_analysis = data.get('emotion_analysis', {})
                    print(f"🎭 Overall emotion: {emotion_analysis.get('overall_emotion', 'unknown')}")
                    print(f"📊 Coverage: {emotion_analysis.get('analyzed_words', 0)}/{emotion_analysis.get('word_count', 0)} words")
                    
                    # Show word analysis
                    word_analysis = emotion_analysis.get('word_analysis', [])
                    if word_analysis:
                        print(f"\n🔍 Word-by-word analysis:")
                        for word_data in word_analysis:
                            status = "✅" if word_data.get('found', False) else "❌"
                            confidence = word_data.get('confidence', 0)
                            emotion = word_data.get('emotion', 'unknown')
                            print(f"   {status} '{word_data.get('word', '')}' → {emotion} ({confidence:.1%})")
                    else:
                        print("❌ No word analysis data returned")
                        
                else:
                    print(f"❌ API returned error: {result.get('error', 'Unknown error')}")
            else:
                print(f"❌ HTTP error: {response.status_code}")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Error testing API: {e}")

if __name__ == "__main__":
    test_api()
