#!/usr/bin/env python3
"""
Speech Recognition Debug Tool
Tests various speech recognition methods to diagnose issues
"""

import speech_recognition as sr
import sys
from pathlib import Path

def test_audio_file(audio_path):
    """Test speech recognition on an audio file"""
    print(f"🎵 Testing speech recognition on: {audio_path}")
    
    if not Path(audio_path).exists():
        print(f"❌ File not found: {audio_path}")
        return
    
    r = sr.Recognizer()
    
    try:
        with sr.AudioFile(audio_path) as source:
            print(f"📊 Audio info - Duration: {source.DURATION:.2f}s, Sample rate: {source.SAMPLE_RATE}")
            
            # Adjust for noise
            r.adjust_for_ambient_noise(source, duration=0.2)
            audio_data = r.record(source)
            
            print("🔍 Testing recognition methods...")
            
            # Test Google
            try:
                google_result = r.recognize_google(audio_data, language='en-US')
                print(f"✅ Google: '{google_result}'")
            except sr.UnknownValueError:
                print("❌ Google: Could not understand audio")
            except sr.RequestError as e:
                print(f"❌ Google: Request error - {e}")
            
            # Test Google with show_all
            try:
                google_detailed = r.recognize_google(audio_data, language='en-US', show_all=True)
                if isinstance(google_detailed, dict):
                    alternatives = google_detailed.get('alternative', [])
                    print(f"📝 Google alternatives: {len(alternatives)}")
                    for i, alt in enumerate(alternatives[:3]):
                        print(f"   {i+1}. '{alt.get('transcript', '')}' (confidence: {alt.get('confidence', 'N/A')})")
            except Exception as e:
                print(f"❌ Google detailed: {e}")
            
            # Test Sphinx
            try:
                sphinx_result = r.recognize_sphinx(audio_data)
                print(f"✅ Sphinx: '{sphinx_result}'")
            except Exception as e:
                print(f"❌ Sphinx: {e}")
            
            # Test Whisper if available
            try:
                whisper_result = r.recognize_whisper(audio_data, model="base")
                print(f"✅ Whisper: '{whisper_result}'")
            except Exception as e:
                print(f"❌ Whisper: {e}")
    
    except Exception as e:
        print(f"❌ Error processing audio file: {e}")

def test_microphone():
    """Test microphone input"""
    print("🎤 Testing microphone input...")
    
    r = sr.Recognizer()
    
    try:
        with sr.Microphone() as source:
            print("📊 Adjusting for ambient noise...")
            r.adjust_for_ambient_noise(source)
            print("🗣️ Say something for 3 seconds...")
            audio_data = r.listen(source, timeout=5, phrase_time_limit=3)
            
            print("🔍 Processing microphone audio...")
            try:
                result = r.recognize_google(audio_data)
                print(f"✅ Recognized: '{result}'")
            except sr.UnknownValueError:
                print("❌ Could not understand audio from microphone")
            except sr.RequestError as e:
                print(f"❌ Request error: {e}")
                
    except Exception as e:
        print(f"❌ Microphone error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_audio_file(sys.argv[1])
    else:
        print("Usage: python3 test_speech_debug.py <audio_file>")
        print("   or: python3 test_speech_debug.py mic  (for microphone test)")
        
        if len(sys.argv) > 1 and sys.argv[1] == "mic":
            test_microphone()
