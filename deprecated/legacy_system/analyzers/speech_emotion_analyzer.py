#!/usr/bin/env python3
"""
Speech Emotion Analyzer
Integrates speech-to-text with word emotion analysis for 10-second phrase emotional analysis
"""

import json
import os
import time
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import speech_recognition as sr
import numpy as np
from batch_word_processor import process_text_batch

class SpeechEmotionAnalyzer:
    def __init__(self):
        self.words_dir = Path("words")
        self.word_cache = {}
        self.recognizer = sr.Recognizer()
        
        # Load all word emotion data into memory for fast lookup
        self.load_word_data()
        
        # Emotion categories from the word data
        self.emotions = ["joy", "trust", "anticipation", "surprise", "anger", "fear", "sadness", "disgust"]
        
    def load_word_data(self):
        """Load all word emotion data from JSON files into memory"""
        print("Loading word emotion database...")
        
        for json_file in self.words_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for word_entry in data.get('words', []):
                    word = word_entry['word'].lower()
                    self.word_cache[word] = word_entry['stats']
                    
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
                
        print(f"Loaded emotion data for {len(self.word_cache)} words")
    
    def transcribe_audio(self, audio_file_path: str) -> str:
        """Convert audio file to text using speech recognition"""
        try:
            print(f"Attempting to transcribe: {audio_file_path}")
            
            # Check if file exists and has content
            if not os.path.exists(audio_file_path):
                print(f"Audio file does not exist: {audio_file_path}")
                return ""
            
            file_size = os.path.getsize(audio_file_path)
            print(f"Audio file size: {file_size} bytes")
            
            if file_size < 1000:  # Very small file, likely empty
                print("Audio file too small, likely empty")
                return ""
            
            with sr.AudioFile(audio_file_path) as source:
                print(f"Audio file info - Duration: {source.DURATION}, Sample rate: {source.SAMPLE_RATE}")
                
                # Adjust for ambient noise with shorter duration for short clips
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                
                # Record the audio
                audio_data = self.recognizer.record(source)
                print(f"Audio data recorded, attempting recognition...")
                
                # Try multiple recognition services for better results
                try:
                    # First try Google (most accurate)
                    text = self.recognizer.recognize_google(audio_data, language='en-US')
                    print(f"Google recognition successful: '{text}'")
                    return text.lower()
                except sr.UnknownValueError:
                    print("Google couldn't understand audio, trying Sphinx...")
                    try:
                        # Fallback to offline Sphinx
                        text = self.recognizer.recognize_sphinx(audio_data)
                        print(f"Sphinx recognition successful: '{text}'")
                        return text.lower()
                    except:
                        print("Sphinx recognition also failed")
                        return ""
                
        except sr.UnknownValueError:
            print("Speech recognition could not understand audio")
            return ""
        except sr.RequestError as e:
            print(f"Speech recognition service error: {e}")
            return ""
        except Exception as e:
            print(f"Audio transcription error: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def get_word_emotion(self, word: str) -> Optional[Dict]:
        """Get emotion data for a specific word"""
        word = word.lower().strip()
        
        # Direct lookup
        if word in self.word_cache:
            return self.word_cache[word]
        
        # Try without punctuation
        clean_word = ''.join(c for c in word if c.isalnum())
        if clean_word in self.word_cache:
            return self.word_cache[clean_word]
            
        return None
    
    def analyze_phrase_emotion(self, text: str) -> Dict:
        """Analyze emotion using batch word processing"""
        print(f"🔍 Batch analysis of: '{text}'")
        return process_text_batch(text)
    
    def get_neutral_emotion_result(self, text: str) -> Dict:
        """Return neutral emotion result when no words are found"""
        words = text.split()
        word_analysis = []
        
        # Create word analysis for all words as not found
        for word in words:
            word_analysis.append({
                "word": word,
                "clean_word": word.lower().strip('.,!?;:"()[]'),
                "emotion": "neutral",
                "confidence": 0.125,
                "valence": 0.5,
                "arousal": 0.5,
                "sentiment": "neutral",
                "found": False
            })
        
        return {
            "text": text,
            "word_count": len(words),
            "analyzed_words": 0,
            "coverage": 0.0,
            "found_words": [],
            "word_analysis": word_analysis,
            "emotions": {emotion: 0.125 for emotion in self.emotions},  # Equal probability
            "vad": {"valence": 0.5, "arousal": 0.5, "dominance": 0.5},
            "sentiment": {"polarity": "neutral", "strength": 0.5},
            "social_axes": {"good_bad": 0.0, "warmth_cold": 0.0, "competence_incompetence": 0.0, "active_passive": 0.0},
            "overall_emotion": "neutral",
            "confidence": 0.125,
            "toxicity": 0.0
        }
    
    def analyze_audio_file(self, audio_file_path: str) -> Dict:
        """Complete analysis pipeline: audio -> text -> emotion analysis"""
        print(f"Analyzing audio file: {audio_file_path}")
        
        # Step 1: Transcribe audio to text
        print("Transcribing audio...")
        text = self.transcribe_audio(audio_file_path)
        
        if not text:
            print("No speech detected or transcription failed")
            return {
                "transcription": "",
                "emotion_analysis": self.get_neutral_emotion_result(""),
                "processing_time": 0,
                "success": False,
                "error": "No speech detected or transcription failed"
            }
        
        print(f"Transcribed text: '{text}'")
        
        # Step 2: Analyze emotion
        print("Analyzing emotions...")
        start_time = time.time()
        emotion_analysis = self.analyze_phrase_emotion(text)
        processing_time = time.time() - start_time
        
        result = {
            "transcription": text,
            "emotion_analysis": emotion_analysis,
            "processing_time": processing_time,
            "success": True,
            "error": None
        }
        
        return result
    
    def get_emotion_summary(self, analysis: Dict) -> str:
        """Generate a human-readable emotion summary"""
        if not analysis["success"]:
            return f"Analysis failed: {analysis['error']}"
        
        emotion_data = analysis["emotion_analysis"]
        
        summary_parts = [
            f"Text: \"{emotion_data['text']}\"",
            f"Primary Emotion: {emotion_data['overall_emotion'].title()} ({emotion_data['confidence']:.1%} confidence)",
            f"Sentiment: {emotion_data['sentiment']['polarity'].title()} (strength: {emotion_data['sentiment']['strength']:.1%})",
            f"VAD Scores: Valence={emotion_data['vad']['valence']:.2f}, Arousal={emotion_data['vad']['arousal']:.2f}, Dominance={emotion_data['vad']['dominance']:.2f}",
            f"Word Coverage: {emotion_data['analyzed_words']}/{emotion_data['word_count']} words ({emotion_data['coverage']:.1%})"
        ]
        
        if emotion_data['toxicity'] > 0.1:
            summary_parts.append(f"⚠️ Toxicity Level: {emotion_data['toxicity']:.1%}")
        
        return "\n".join(summary_parts)


def main():
    """CLI interface for testing"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python speech_emotion_analyzer.py <audio_file>")
        print("Supported formats: WAV, FLAC, AIFF")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    
    if not os.path.exists(audio_file):
        print(f"Error: Audio file '{audio_file}' not found")
        sys.exit(1)
    
    # Initialize analyzer
    analyzer = SpeechEmotionAnalyzer()
    
    # Analyze audio
    result = analyzer.analyze_audio_file(audio_file)
    
    # Print results
    print("\n" + "="*60)
    print("SPEECH EMOTION ANALYSIS RESULTS")
    print("="*60)
    print(analyzer.get_emotion_summary(result))
    
    if result["success"]:
        print(f"\nProcessing time: {result['processing_time']:.2f} seconds")
        
        # Detailed emotion breakdown
        emotions = result["emotion_analysis"]["emotions"]
        print(f"\nDetailed Emotion Breakdown:")
        for emotion, prob in sorted(emotions.items(), key=lambda x: x[1], reverse=True):
            print(f"  {emotion.title()}: {prob:.1%}")


if __name__ == "__main__":
    main()
