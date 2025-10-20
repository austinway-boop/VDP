#!/usr/bin/env python3
"""
Test speech recognition functionality
"""

import speech_recognition as sr
import tempfile
import os
from pathlib import Path

def test_speech_recognition():
    """Test basic speech recognition"""
    print("🎤 Testing Speech Recognition...")
    
    recognizer = sr.Recognizer()
    
    # Test with a simple audio file if available
    uncertain_clips = Path("training_data/uncertain_clips")
    if uncertain_clips.exists():
        audio_files = list(uncertain_clips.glob("*.wav"))
        if audio_files:
            test_file = audio_files[0]
            print(f"📁 Testing with file: {test_file}")
            
            try:
                with sr.AudioFile(str(test_file)) as source:
                    print(f"✅ Audio file opened successfully")
                    print(f"   Duration: {source.DURATION}")
                    print(f"   Sample rate: {source.SAMPLE_RATE}")
                    
                    # Adjust for ambient noise
                    recognizer.adjust_for_ambient_noise(source, duration=0.2)
                    
                    # Record the audio
                    audio_data = recognizer.record(source)
                    print(f"✅ Audio data recorded")
                    
                    # Try Google recognition
                    try:
                        text = recognizer.recognize_google(audio_data, language='en-US', show_all=True)
                        print(f"✅ Google recognition result: {text}")
                        
                        if isinstance(text, dict) and 'alternative' in text:
                            for i, alt in enumerate(text['alternative'][:3]):
                                conf = alt.get('confidence', 'unknown')
                                transcript = alt.get('transcript', 'unknown')
                                print(f"   Alternative {i+1}: '{transcript}' (confidence: {conf})")
                        
                    except sr.UnknownValueError:
                        print("❌ Google couldn't understand audio")
                    except sr.RequestError as e:
                        print(f"❌ Google recognition error: {e}")
                    
                    # Try Sphinx as fallback
                    try:
                        sphinx_text = recognizer.recognize_sphinx(audio_data)
                        print(f"✅ Sphinx recognition: '{sphinx_text}'")
                    except Exception as e:
                        print(f"❌ Sphinx recognition failed: {e}")
                        
            except Exception as e:
                print(f"❌ Error with audio file: {e}")
        else:
            print("❌ No audio files found in uncertain_clips")
    else:
        print("❌ No uncertain_clips directory found")
    
    # Test recognition engines availability
    print("\n🔍 Testing recognition engines:")
    
    try:
        # Test Google
        print("✅ Google Speech Recognition: Available")
    except:
        print("❌ Google Speech Recognition: Not available")
    
    try:
        # Test Sphinx
        test_audio = sr.AudioData(b'\x00' * 1000, 16000, 2)  # Dummy audio
        recognizer.recognize_sphinx(test_audio)
        print("✅ Sphinx: Available")
    except Exception as e:
        if "no language model" in str(e).lower():
            print("❌ Sphinx: Language model missing")
        else:
            print(f"❌ Sphinx: {e}")

if __name__ == "__main__":
    test_speech_recognition()
