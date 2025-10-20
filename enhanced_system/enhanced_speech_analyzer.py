#!/usr/bin/env python3
"""
Enhanced Speech Emotion Analyzer with Confidence-Based Training
Integrates speech-to-text with confidence scoring and training data collection
"""

import json
import os
import time
import statistics
import hashlib
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import speech_recognition as sr
import numpy as np
from batch_word_processor import process_text_batch
import shutil

# Import local speech model
try:
    from local_speech_model import LocalSpeechModel
    LOCAL_MODEL_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Local speech model not available: {e}")
    LOCAL_MODEL_AVAILABLE = False

# Import laughter detector
try:
    from laughter_detector import detect_laughter_in_audio, get_laughter_summary
    LAUGHTER_DETECTION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Laughter detection not available: {e}")
    LAUGHTER_DETECTION_AVAILABLE = False

class EnhancedSpeechAnalyzer:
    def __init__(self, confidence_threshold: float = 0.7):
        # Look for words directory in parent directory (main project root)
        self.words_dir = Path(__file__).parent.parent / "words"
        if not self.words_dir.exists():
            self.words_dir = Path("words")  # Fallback to current directory
        self.word_cache = {}
        self.recognizer = sr.Recognizer()
        self.confidence_threshold = confidence_threshold
        
        # Training data directories
        self.training_dir = Path("training_data")
        self.uncertain_dir = self.training_dir / "uncertain_clips"
        self.reviewed_dir = self.training_dir / "reviewed_clips"
        self.uncertain_words_dir = self.training_dir / "uncertain_words"
        self.reviewed_words_dir = self.training_dir / "reviewed_words"
        self.corrections_file = self.training_dir / "corrections.json"
        
        # Create directories
        self.training_dir.mkdir(exist_ok=True)
        self.uncertain_dir.mkdir(exist_ok=True)
        self.reviewed_dir.mkdir(exist_ok=True)
        self.uncertain_words_dir.mkdir(exist_ok=True)
        self.reviewed_words_dir.mkdir(exist_ok=True)
        
        # Load corrections database
        self.corrections = self.load_corrections()
        
        # Initialize local speech model
        self.local_model = None
        if LOCAL_MODEL_AVAILABLE:
            try:
                self.local_model = LocalSpeechModel()
                print("🤖 Local speech model initialized")
            except Exception as e:
                print(f"⚠️ Could not initialize local model: {e}")
        
        # Load all word emotion data into memory for fast lookup
        self.load_word_data()
        
        # Emotion categories from the word data
        self.emotions = ["joy", "trust", "anticipation", "surprise", "anger", "fear", "sadness", "disgust"]
        
        # Custom vocabulary for improved recognition
        self.custom_vocabulary = self.load_custom_vocabulary()
        
    def load_corrections(self) -> Dict:
        """Load the corrections database"""
        if self.corrections_file.exists():
            try:
                with open(self.corrections_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading corrections: {e}")
        
        return {"corrections": [], "audio_hashes": {}, "vocabulary_improvements": {}}
    
    def save_corrections(self):
        """Save corrections to file"""
        try:
            with open(self.corrections_file, 'w', encoding='utf-8') as f:
                json.dump(self.corrections, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving corrections: {e}")
    
    def load_custom_vocabulary(self) -> Dict[str, str]:
        """Load custom vocabulary from corrections"""
        vocab = {}
        for correction in self.corrections.get("corrections", []):
            if "audio_hash" in correction and "corrected_text" in correction:
                vocab[correction["audio_hash"]] = correction["corrected_text"]
        return vocab
    
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
    
    def calculate_audio_hash(self, audio_file_path: str) -> str:
        """Calculate hash of audio file for deduplication"""
        try:
            with open(audio_file_path, 'rb') as f:
                audio_data = f.read()
                return hashlib.md5(audio_data).hexdigest()
        except Exception as e:
            print(f"Error calculating audio hash: {e}")
            return str(uuid.uuid4())
    
    def estimate_transcription_confidence(self, audio_data, text: str) -> float:
        """Estimate confidence in transcription using multiple methods"""
        if not text:
            return 0.0
        
        confidence_factors = []
        
        # Factor 1: Text length (longer text often more reliable)
        length_confidence = min(len(text.split()) / 10.0, 1.0)  # Normalize to 0-1
        confidence_factors.append(length_confidence)
        
        # Factor 2: Word recognition in our database
        words = text.split()
        known_words = sum(1 for word in words if word.lower().strip('.,!?;:"()[]') in self.word_cache)
        word_confidence = known_words / len(words) if words else 0.0
        confidence_factors.append(word_confidence)
        
        # Factor 3: Audio quality indicators (simplified)
        try:
            # This is a simplified audio quality check
            # In a real implementation, you'd use more sophisticated audio analysis
            audio_confidence = 0.7  # Placeholder - would analyze SNR, clarity, etc.
            confidence_factors.append(audio_confidence)
        except:
            confidence_factors.append(0.5)
        
        # Factor 4: Grammar and coherence check (simplified)
        # Check for common speech recognition errors
        grammar_confidence = 1.0
        error_patterns = ['uh', 'um', 'ah', '...', 'inaudible']
        for pattern in error_patterns:
            if pattern in text.lower():
                grammar_confidence -= 0.2
        grammar_confidence = max(0.0, grammar_confidence)
        confidence_factors.append(grammar_confidence)
        
        # Calculate weighted average
        weights = [0.2, 0.4, 0.2, 0.2]  # Emphasize word recognition
        weighted_confidence = sum(f * w for f, w in zip(confidence_factors, weights))
        
        return min(max(weighted_confidence, 0.0), 1.0)
    
    def transcribe_audio_with_confidence(self, audio_file_path: str) -> Tuple[str, float, Dict]:
        """Convert audio file to text with confidence estimation"""
        try:
            print(f"Attempting to transcribe: {audio_file_path}")
            
            # Check if file exists and has content
            if not os.path.exists(audio_file_path):
                print(f"Audio file does not exist: {audio_file_path}")
                return "", 0.0, {"error": "File not found"}
            
            file_size = os.path.getsize(audio_file_path)
            print(f"Audio file size: {file_size} bytes")
            
            if file_size < 1000:  # Lowered threshold - very small files might still have speech
                print(f"⚠️ Audio file quite small ({file_size} bytes) - may have recognition issues")
            
            if file_size < 100:  # Only reject extremely small files
                print("Audio file too small, likely empty")
                return "", 0.0, {"error": "File too small"}
            
            # Convert WebM to WAV if needed
            converted_path = self.convert_audio_if_needed(audio_file_path)
            if converted_path != audio_file_path:
                print(f"Converted audio format: {audio_file_path} → {converted_path}")
                audio_file_path = converted_path
            
            # Calculate audio hash for deduplication
            audio_hash = self.calculate_audio_hash(audio_file_path)
            
            # Check if we have a custom correction for this audio
            if audio_hash in self.custom_vocabulary:
                corrected_text = self.custom_vocabulary[audio_hash]
                print(f"Using custom vocabulary: '{corrected_text}'")
                return corrected_text, 1.0, {"source": "custom_vocabulary", "audio_hash": audio_hash}
            
            with sr.AudioFile(audio_file_path) as source:
                print(f"Audio file info - Duration: {source.DURATION}, Sample rate: {source.SAMPLE_RATE}")
                
                # Enhanced audio preprocessing for better recognition
                if source.DURATION < 1.0:
                    # Very short clips - minimal noise adjustment
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.1)
                elif source.DURATION < 5.0:
                    # Short clips - quick noise adjustment  
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                else:
                    # Longer clips - more thorough noise adjustment
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Adjust recognizer settings for better accuracy
                self.recognizer.energy_threshold = 200  # Even lower threshold for quiet speech
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 0.5  # Shorter pause detection for better capture
                self.recognizer.phrase_threshold = 0.3  # Lower phrase threshold
                self.recognizer.non_speaking_duration = 0.5  # Shorter non-speaking duration
                
                # Record the audio
                audio_data = self.recognizer.record(source)
                print(f"Audio data recorded, attempting recognition with enhanced settings...")
                
                transcription_results = []
                
                # Try multiple recognition services and collect results
                try:
                    # Google Speech Recognition with enhanced parameters
                    text = self.recognizer.recognize_google(
                        audio_data, 
                        language='en-US', 
                        show_all=True,
                        with_confidence=True
                    )
                    if isinstance(text, dict) and 'alternative' in text:
                        # Google returns confidence scores in full response
                        best_result = text['alternative'][0]
                        google_text = best_result.get('transcript', '').lower()
                        google_confidence = best_result.get('confidence', 0.5)
                        transcription_results.append({
                            "service": "google",
                            "text": google_text,
                            "confidence": google_confidence
                        })
                        print(f"Google recognition: '{google_text}' (confidence: {google_confidence:.2f})")
                    elif isinstance(text, str):
                        google_text = text.lower()
                        google_confidence = 0.8  # Default confidence when not provided
                        transcription_results.append({
                            "service": "google", 
                            "text": google_text,
                            "confidence": google_confidence
                        })
                        print(f"Google recognition: '{google_text}' (default confidence: {google_confidence:.2f})")
                        
                except sr.UnknownValueError:
                    print("Google couldn't understand audio - trying with different settings...")
                    # Try again with different parameters and languages
                    fallback_attempts = [
                        {'language': 'en-US', 'name': 'US English'},
                        {'language': 'en-GB', 'name': 'UK English'},
                        {'language': 'en', 'name': 'Generic English'},
                    ]
                    
                    for attempt in fallback_attempts:
                        try:
                            simple_text = self.recognizer.recognize_google(
                                audio_data, 
                                language=attempt['language']
                            )
                            if simple_text and simple_text.strip():
                                transcription_results.append({
                                    "service": f"google_{attempt['language']}",
                                    "text": simple_text.lower(),
                                    "confidence": 0.6
                                })
                                print(f"✅ Google {attempt['name']}: '{simple_text.lower()}'")
                                break
                        except:
                            print(f"❌ Google {attempt['name']} failed")
                    
                    if not transcription_results:
                        print("🔍 Google recognition completely failed - checking audio quality...")
                        # Audio quality diagnostics
                        try:
                            import numpy as np
                            audio_array = np.frombuffer(audio_data.get_raw_data(), dtype=np.int16)
                            audio_level = np.sqrt(np.mean(audio_array**2))
                            print(f"📊 Audio level: {audio_level:.2f} (should be >100 for clear speech)")
                            if audio_level < 50:
                                print("⚠️ Audio level very low - try speaking louder or closer to microphone")
                            elif audio_level > 10000:
                                print("⚠️ Audio level very high - may be clipping or distorted")
                        except:
                            print("Could not analyze audio quality")
                except sr.RequestError as e:
                    print(f"Google recognition error: {e}")
                
                # Try Sphinx as fallback (if available)
                try:
                    sphinx_text = self.recognizer.recognize_sphinx(audio_data).lower()
                    if sphinx_text and sphinx_text.strip():
                        sphinx_confidence = 0.6  # Sphinx typically less accurate
                        transcription_results.append({
                            "service": "sphinx",
                            "text": sphinx_text, 
                            "confidence": sphinx_confidence
                        })
                        print(f"✅ Sphinx recognition: '{sphinx_text}' (confidence: {sphinx_confidence:.2f})")
                except Exception as e:
                    print(f"❌ Sphinx recognition failed: {e}")
                
                # If still no results, try more aggressive Google settings
                if not transcription_results:
                    print("🔄 No recognition results yet - trying aggressive Google settings...")
                    try:
                        # Try with very liberal settings
                        aggressive_text = self.recognizer.recognize_google(
                            audio_data, 
                            language='en',
                            show_all=False  # Just get the best guess
                        )
                        if aggressive_text and aggressive_text.strip():
                            transcription_results.append({
                                "service": "google_aggressive",
                                "text": aggressive_text.lower(),
                                "confidence": 0.4  # Lower confidence since we're being aggressive
                            })
                            print(f"🎯 Google aggressive: '{aggressive_text.lower()}'")
                    except Exception as e:
                        print(f"❌ Google aggressive failed: {e}")
                
                # Select best result
                if not transcription_results:
                    # Try local model as final fallback
                    if self.local_model:
                        print("🤖 Trying local speech model as fallback...")
                        local_text, local_confidence, local_metadata = self.local_model.recognize_speech(audio_file_path)
                        if local_text:
                            transcription_results.append({
                                "service": "local_model",
                                "text": local_text,
                                "confidence": local_confidence,
                                "metadata": local_metadata
                            })
                            print(f"🎯 Local model result: '{local_text}' (confidence: {local_confidence:.2f})")
                    
                    if not transcription_results:
                        return "", 0.0, {"error": "All recognition services failed"}
                
                # Choose result with highest confidence
                best_result = max(transcription_results, key=lambda x: x['confidence'])
                final_text = best_result['text']
                service_confidence = best_result['confidence']
                
                # If confidence is low, try local model as additional option
                if service_confidence < 0.6 and self.local_model and best_result['service'] != 'local_model':
                    print("🤖 Low confidence detected, trying local model...")
                    local_text, local_confidence, local_metadata = self.local_model.recognize_speech(audio_file_path)
                    if local_text and local_confidence > service_confidence:
                        print(f"🎯 Local model provides better result: '{local_text}' ({local_confidence:.2f} > {service_confidence:.2f})")
                        final_text = local_text
                        service_confidence = local_confidence
                        transcription_results.append({
                            "service": "local_model_fallback",
                            "text": local_text,
                            "confidence": local_confidence,
                            "metadata": local_metadata
                        })
                
                # Calculate our own confidence estimate
                estimated_confidence = self.estimate_transcription_confidence(audio_data, final_text)
                
                # Combine service confidence with our estimate
                final_confidence = (service_confidence * 0.6 + estimated_confidence * 0.4)
                
                metadata = {
                    "service": best_result['service'],
                    "service_confidence": service_confidence,
                    "estimated_confidence": estimated_confidence,
                    "final_confidence": final_confidence,
                    "audio_hash": audio_hash,
                    "all_results": transcription_results
                }
                
                return final_text, final_confidence, metadata
                
        except Exception as e:
            print(f"Audio transcription error: {e}")
            import traceback
            traceback.print_exc()
            return "", 0.0, {"error": str(e)}
    
    def convert_audio_if_needed(self, audio_file_path: str) -> str:
        """Convert audio file to WAV format if needed"""
        try:
            # Try to read with speech_recognition first
            with sr.AudioFile(audio_file_path) as source:
                # If this works, no conversion needed
                print(f"Audio file format is compatible: {audio_file_path}")
                return audio_file_path
        except ValueError as e:
            # File format not supported, try to convert
            print(f"Audio format not compatible ({e}), attempting conversion...")
            
            try:
                import subprocess
                import tempfile
                
                # Create temporary WAV file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                    temp_wav_path = temp_wav.name
                
                # Try pydub first (more reliable for WebM)
                try:
                    from pydub import AudioSegment
                    
                    print(f"Converting with pydub: {audio_file_path} → {temp_wav_path}")
                    
                    # Load audio file with pydub (supports WebM)
                    audio = AudioSegment.from_file(audio_file_path)
                    
                    # Convert to WAV format with speech recognition compatible settings
                    audio = audio.set_frame_rate(16000).set_channels(1)
                    audio.export(temp_wav_path, format="wav")
                    
                    # Verify the converted file works
                    try:
                        with sr.AudioFile(temp_wav_path) as test_source:
                            print(f"✅ Successfully converted and verified: {temp_wav_path}")
                            return temp_wav_path
                    except Exception as verify_error:
                        print(f"Converted file verification failed: {verify_error}")
                        
                except Exception as pydub_error:
                    print(f"Pydub conversion failed: {pydub_error}")
                    
                    # Fallback: try local ffmpeg if available
                    try:
                        # Try local ffmpeg first
                        ffmpeg_path = str(Path(__file__).parent.parent / "ffmpeg")
                        if not os.path.exists(ffmpeg_path):
                            ffmpeg_path = "ffmpeg"  # Try system ffmpeg
                        
                        result = subprocess.run([
                            ffmpeg_path, '-i', audio_file_path, 
                            '-ar', '16000',  # 16kHz sample rate
                            '-ac', '1',      # mono
                            '-f', 'wav',     # force WAV format
                            '-y',            # overwrite output
                            temp_wav_path
                        ], check=True, capture_output=True, text=True)
                        
                        print(f"✅ Successfully converted with ffmpeg: {temp_wav_path}")
                        return temp_wav_path
                        
                    except (subprocess.CalledProcessError, FileNotFoundError) as ffmpeg_error:
                        print(f"FFmpeg conversion failed: {ffmpeg_error}")
                
                # If conversion fails, return original and let it fail gracefully
                print(f"❌ All conversion attempts failed, returning original file")
                return audio_file_path
                
            except Exception as e:
                print(f"Audio conversion error: {e}")
                return audio_file_path
    
    def save_uncertain_clip(self, audio_file_path: str, text: str, confidence: float, metadata: Dict) -> str:
        """Save audio clip with low confidence for review"""
        try:
            # Create unique filename
            timestamp = int(time.time())
            audio_hash = metadata.get('audio_hash', 'unknown')
            clip_id = f"{timestamp}_{audio_hash[:8]}"
            
            # Copy audio file to uncertain clips directory
            audio_extension = Path(audio_file_path).suffix
            new_audio_path = self.uncertain_dir / f"{clip_id}{audio_extension}"
            shutil.copy2(audio_file_path, new_audio_path)
            
            # Create metadata file
            metadata_file = self.uncertain_dir / f"{clip_id}_metadata.json"
            clip_metadata = {
                "clip_id": clip_id,
                "original_path": str(audio_file_path),
                "transcribed_text": text,
                "confidence": confidence,
                "timestamp": timestamp,
                "status": "pending_review",
                "metadata": metadata
            }
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(clip_metadata, f, indent=2, ensure_ascii=False)
            
            print(f"🔍 Saved uncertain clip: {clip_id} (confidence: {confidence:.2f})")
            return clip_id
            
        except Exception as e:
            print(f"Error saving uncertain clip: {e}")
            return ""
    
    def save_uncertain_words(self, audio_file_path: str, text: str, emotion_analysis: Dict, metadata: Dict) -> List[str]:
        """Save individual word snippets for potentially misheard words"""
        uncertain_word_ids = []
        
        try:
            if not text or not text.strip():
                return uncertain_word_ids
            
            words = text.split()
            
            # Identify potentially uncertain words based on various criteria
            uncertain_words = []
            
            for i, word in enumerate(words):
                clean_word = ''.join(c for c in word.lower() if c.isalnum())
                
                # Criteria for uncertain words:
                is_uncertain = False
                uncertainty_reasons = []
                
                # 1. Very short words (often misheard)
                if len(clean_word) <= 2 and clean_word not in ['i', 'a', 'is', 'it', 'to', 'of', 'in', 'on', 'at', 'be', 'we', 'he', 'me', 'my', 'up', 'so', 'no', 'go', 'do']:
                    is_uncertain = True
                    uncertainty_reasons.append("very_short")
                
                # 2. Very long words (often concatenated mistakes)
                if len(clean_word) > 15:
                    is_uncertain = True
                    uncertainty_reasons.append("very_long")
                
                # 3. Repeated words (like "scooby-doo scooby-doo")
                if words.count(word) > 3:
                    is_uncertain = True
                    uncertainty_reasons.append("repeated")
                
                # 4. Contains numbers or mixed alphanumeric (often misheard)
                if any(c.isdigit() for c in word) and any(c.isalpha() for c in word):
                    is_uncertain = True
                    uncertainty_reasons.append("mixed_chars")
                
                # 5. Unusual character patterns
                if len(set(word.lower())) == 1 and len(word) > 2:  # Same character repeated
                    is_uncertain = True
                    uncertainty_reasons.append("repeated_chars")
                
                # 6. Words with unusual consonant clusters
                consonant_clusters = ['xz', 'qw', 'zx', 'bx', 'cx', 'dx', 'fx', 'gx', 'hx', 'jx', 'kx', 'lx', 'mx', 'nx', 'px', 'rx', 'sx', 'tx', 'vx', 'wx']
                if any(cluster in clean_word for cluster in consonant_clusters):
                    is_uncertain = True
                    uncertainty_reasons.append("unusual_clusters")
                
                # 7. Low overall transcription confidence affects all words
                overall_confidence = metadata.get('final_confidence', 1.0)
                if overall_confidence < 0.4:
                    is_uncertain = True
                    uncertainty_reasons.append("low_confidence")
                
                if is_uncertain:
                    uncertain_words.append({
                        'index': i,
                        'word': word,
                        'clean_word': clean_word,
                        'reasons': uncertainty_reasons
                    })
            
            if not uncertain_words:
                print("📚 No uncertain words detected based on speech recognition patterns")
                return uncertain_word_ids
            
            word_descriptions = [f"{w['word']} ({','.join(w['reasons'])})" for w in uncertain_words]
            print(f"🔍 Found {len(uncertain_words)} potentially misheard words: {word_descriptions}")
            
            # Save word snippets for review
            for uncertain_word in uncertain_words:
                word_id = self.save_word_snippet(
                    audio_file_path, 
                    uncertain_word, 
                    text, 
                    metadata,
                    len(words)
                )
                if word_id:
                    uncertain_word_ids.append(word_id)
            
            return uncertain_word_ids
            
        except Exception as e:
            print(f"Error saving uncertain words: {e}")
            return uncertain_word_ids
    
    def save_word_snippet(self, audio_file_path: str, unknown_word: Dict, full_text: str, metadata: Dict, total_words: int) -> str:
        """Save individual word snippet for review"""
        try:
            timestamp = int(time.time())
            word = unknown_word['word']
            clean_word = unknown_word['clean_word']
            word_index = unknown_word['index']
            
            # Create unique word ID
            word_hash = hashlib.md5(f"{word}_{timestamp}".encode()).hexdigest()[:8]
            word_id = f"{timestamp}_{clean_word}_{word_hash}"
            
            # Copy the full audio file (in future versions, we could extract word segments)
            audio_extension = Path(audio_file_path).suffix
            new_audio_path = self.uncertain_words_dir / f"{word_id}{audio_extension}"
            shutil.copy2(audio_file_path, new_audio_path)
            
            # Create word metadata
            word_metadata_file = self.uncertain_words_dir / f"{word_id}_metadata.json"
            word_metadata = {
                "word_id": word_id,
                "original_word": word,
                "clean_word": clean_word,
                "word_index": word_index,
                "total_words": total_words,
                "full_text": full_text,
                "original_audio_path": str(audio_file_path),
                "timestamp": timestamp,
                "status": "pending_word_review",
                "audio_metadata": metadata,
                "estimated_position": f"Word {word_index + 1} of {total_words}",
                "context": self.get_word_context(full_text.split(), word_index),
                "uncertainty_reasons": unknown_word.get('reasons', []),
                "detection_type": "speech_recognition_uncertainty"
            }
            
            with open(word_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(word_metadata, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Saved uncertain word: '{word}' → {word_id}")
            return word_id
            
        except Exception as e:
            print(f"Error saving word snippet for '{unknown_word.get('word', 'unknown')}': {e}")
            return ""
    
    def get_word_context(self, words: List[str], word_index: int, context_size: int = 2) -> Dict:
        """Get surrounding context for a word"""
        start_idx = max(0, word_index - context_size)
        end_idx = min(len(words), word_index + context_size + 1)
        
        before_words = words[start_idx:word_index]
        target_word = words[word_index] if word_index < len(words) else ""
        after_words = words[word_index + 1:end_idx]
        
        return {
            "before": " ".join(before_words),
            "target": target_word,
            "after": " ".join(after_words),
            "full_context": " ".join(words[start_idx:end_idx])
        }
    
    def analyze_audio_file_with_training(self, audio_file_path: str) -> Dict:
        """Complete analysis pipeline with confidence-based training data collection"""
        print(f"Analyzing audio file: {audio_file_path}")
        
        # Step 1: Transcribe audio with confidence
        print("Transcribing audio...")
        text, confidence, metadata = self.transcribe_audio_with_confidence(audio_file_path)
        
        if not text:
            print("No speech detected or transcription failed")
            return {
                "transcription": "",
                "confidence": 0.0,
                "metadata": metadata,
                "emotion_analysis": self.get_neutral_emotion_result(""),
                "laughter_analysis": {"error": "No audio to analyze"},
                "processing_time": 0,
                "success": False,
                "error": metadata.get("error", "Unknown error"),
                "needs_review": False
            }
        
        print(f"Transcribed text: '{text}' (confidence: {confidence:.2f})")
        
        # Step 2: Check if confidence is below threshold
        needs_review = confidence < self.confidence_threshold
        clip_id = None
        
        if needs_review:
            print(f"⚠️ Low confidence ({confidence:.2f} < {self.confidence_threshold}), saving for review...")
            clip_id = self.save_uncertain_clip(audio_file_path, text, confidence, metadata)
        
        # Step 3: Detect laughter first (affects emotion analysis)
        print("Detecting laughter...")
        laughter_analysis = {}
        if LAUGHTER_DETECTION_AVAILABLE:
            try:
                laughter_analysis = detect_laughter_in_audio(audio_file_path)
                if laughter_analysis.get('laughter_segments'):
                    print(f"😄 Laughter detected: {len(laughter_analysis['laughter_segments'])} segments")
                    print(get_laughter_summary(laughter_analysis))
                else:
                    print("😐 No laughter detected")
            except Exception as e:
                print(f"⚠️ Laughter detection error: {e}")
                laughter_analysis = {'error': str(e)}
        else:
            laughter_analysis = {'error': 'Laughter detection not available'}
        
        # Step 4: Analyze emotion (with laughter influence)
        print("Analyzing emotions...")
        start_time = time.time()
        emotion_analysis = self.analyze_phrase_emotion(text, laughter_analysis)
        processing_time = time.time() - start_time
        
        # Step 5: Check for unknown words and save word snippets
        print("Checking for unknown words...")
        unknown_word_ids = self.save_uncertain_words(audio_file_path, text, emotion_analysis, metadata)
        
        result = {
            "transcription": text,
            "confidence": confidence,
            "metadata": metadata,
            "emotion_analysis": emotion_analysis,
            "laughter_analysis": laughter_analysis,
            "processing_time": processing_time,
            "success": True,
            "error": None,
            "needs_review": needs_review,
            "clip_id": clip_id,
            "unknown_words": len(unknown_word_ids),
            "unknown_word_ids": unknown_word_ids
        }
        
        return result
    
    def analyze_phrase_emotion(self, text: str, laughter_data: Dict = None) -> Dict:
        """Analyze emotion using batch word processing with laughter influence"""
        print(f"🔍 Batch analysis of: '{text}'")
        emotion_result = process_text_batch(text)
        
        # Apply laughter influence to emotion scores
        if laughter_data and laughter_data.get('laughter_segments'):
            emotion_result = self._apply_laughter_influence(emotion_result, laughter_data)
        
        return emotion_result
    
    def _apply_laughter_influence(self, emotion_result: Dict, laughter_data: Dict) -> Dict:
        """Apply laughter influence to emotion analysis"""
        try:
            laughter_percentage = laughter_data.get('laughter_percentage', 0)
            num_segments = len(laughter_data.get('laughter_segments', []))
            
            if laughter_percentage > 0:
                print(f"😄 Applying laughter influence: {laughter_percentage:.1f}% laughter detected")
                
                # Calculate laughter boost factor (0.1 to 0.5 based on amount of laughter)
                laughter_boost = min(laughter_percentage / 100 * 0.5, 0.5)
                
                # Boost joy and positive emotions
                emotions = emotion_result.get('emotions', {}).copy()
                
                # Apply laughter boost to joy
                original_joy = emotions.get('joy', 0)
                boosted_joy = min(original_joy + laughter_boost, 1.0)
                emotions['joy'] = boosted_joy
                
                # Slightly boost trust and surprise (common with laughter)
                emotions['trust'] = min(emotions.get('trust', 0) + laughter_boost * 0.3, 1.0)
                emotions['surprise'] = min(emotions.get('surprise', 0) + laughter_boost * 0.2, 1.0)
                
                # Reduce negative emotions when laughter is present
                negative_emotions = ['anger', 'fear', 'sadness', 'disgust']
                reduction_factor = laughter_boost * 0.5
                
                for emotion in negative_emotions:
                    emotions[emotion] = max(emotions.get(emotion, 0) - reduction_factor, 0.0)
                
                # Renormalize to ensure probabilities sum to 1.0
                total = sum(emotions.values())
                if total > 0:
                    emotions = {k: v / total for k, v in emotions.items()}
                
                # Update the result
                emotion_result['emotions'] = emotions
                emotion_result['laughter_influence'] = {
                    'applied': True,
                    'boost_factor': laughter_boost,
                    'original_joy': original_joy,
                    'boosted_joy': emotions['joy'],
                    'laughter_percentage': laughter_percentage
                }
                
                # Update overall emotion if joy is now dominant
                max_emotion = max(emotions, key=emotions.get)
                if max_emotion != emotion_result.get('overall_emotion'):
                    print(f"🎭 Overall emotion changed due to laughter: {emotion_result.get('overall_emotion')} → {max_emotion}")
                    emotion_result['overall_emotion'] = max_emotion
                
                print(f"🎭 Laughter boosted joy: {original_joy:.3f} → {emotions['joy']:.3f} (+{laughter_boost:.3f})")
                
            return emotion_result
            
        except Exception as e:
            print(f"⚠️ Error applying laughter influence: {e}")
            return emotion_result
    
    def get_neutral_emotion_result(self, text: str) -> Dict:
        """Return neutral emotion result when no words are found"""
        words = text.split() if text else []
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
    
    def get_pending_reviews(self) -> List[Dict]:
        """Get all clips pending review"""
        pending_clips = []
        
        for metadata_file in self.uncertain_dir.glob("*_metadata.json"):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    clip_data = json.load(f)
                    if clip_data.get('status') == 'pending_review':
                        pending_clips.append(clip_data)
            except Exception as e:
                print(f"Error reading {metadata_file}: {e}")
        
        # Sort by timestamp (newest first)
        pending_clips.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        return pending_clips
    
    def get_pending_word_reviews(self) -> List[Dict]:
        """Get all word snippets pending review"""
        pending_words = []
        
        for metadata_file in self.uncertain_words_dir.glob("*_metadata.json"):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    word_data = json.load(f)
                    if word_data.get('status') == 'pending_word_review':
                        pending_words.append(word_data)
            except Exception as e:
                print(f"Error reading word metadata {metadata_file}: {e}")
        
        # Sort by timestamp (newest first)
        pending_words.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        return pending_words
    
    def submit_word_correction(self, word_id: str, corrected_word: str, emotion_data: Dict = None, user_id: str = "admin") -> bool:
        """Submit correction for a word and add it to the vocabulary"""
        try:
            metadata_file = self.uncertain_words_dir / f"{word_id}_metadata.json"
            
            if not metadata_file.exists():
                print(f"Word metadata file not found for: {word_id}")
                return False
            
            # Load existing metadata
            with open(metadata_file, 'r', encoding='utf-8') as f:
                word_data = json.load(f)
            
            # Update metadata
            word_data['status'] = 'word_corrected'
            word_data['corrected_word'] = corrected_word
            word_data['corrected_by'] = user_id
            word_data['correction_timestamp'] = int(time.time())
            
            if emotion_data:
                word_data['emotion_data'] = emotion_data
            
            # Save updated metadata
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(word_data, f, indent=2, ensure_ascii=False)
            
            # Add to corrections database
            correction_entry = {
                "word_id": word_id,
                "original_word": word_data['original_word'],
                "corrected_word": corrected_word,
                "context": word_data.get('context', {}),
                "full_text": word_data.get('full_text', ''),
                "user_id": user_id,
                "timestamp": word_data['correction_timestamp'],
                "type": "word_correction"
            }
            
            if 'word_corrections' not in self.corrections:
                self.corrections['word_corrections'] = []
            
            self.corrections['word_corrections'].append(correction_entry)
            
            # Save corrections
            self.save_corrections()
            
            # Add to local model training data
            if self.local_model:
                audio_file = None
                for ext in ['.wav', '.flac', '.aiff', '.mp3', '.webm']:
                    potential_file = self.uncertain_words_dir / f"{word_id}{ext}"
                    if potential_file.exists():
                        audio_file = str(potential_file)
                        break
                
                if audio_file:
                    # For word corrections, use the corrected word as the full text
                    success = self.local_model.add_training_sample(
                        audio_file_path=audio_file,
                        correct_text=corrected_word,
                        original_transcription=word_data['original_word'],
                        confidence=word_data.get('audio_metadata', {}).get('final_confidence', 0.0)
                    )
                    if success:
                        print("🤖 Added word correction to local model training data")
            
            # Move to reviewed directory
            self.move_word_to_reviewed(word_id)
            
            print(f"✅ Word correction submitted: '{word_data['original_word']}' → '{corrected_word}'")
            return True
            
        except Exception as e:
            print(f"Error submitting word correction: {e}")
            return False
    
    def move_word_to_reviewed(self, word_id: str):
        """Move corrected word to reviewed directory"""
        try:
            # Move audio file
            for ext in ['.wav', '.flac', '.aiff', '.mp3', '.webm']:
                audio_file = self.uncertain_words_dir / f"{word_id}{ext}"
                if audio_file.exists():
                    new_audio_path = self.reviewed_words_dir / f"{word_id}{ext}"
                    shutil.move(str(audio_file), str(new_audio_path))
                    break
            
            # Move metadata file
            metadata_file = self.uncertain_words_dir / f"{word_id}_metadata.json"
            if metadata_file.exists():
                new_metadata_path = self.reviewed_words_dir / f"{word_id}_metadata.json"
                shutil.move(str(metadata_file), str(new_metadata_path))
                
        except Exception as e:
            print(f"Error moving word files for {word_id}: {e}")
    
    def submit_correction(self, clip_id: str, corrected_text: str, user_id: str = "admin") -> bool:
        """Submit correction for a clip and enhance the training system"""
        try:
            metadata_file = self.uncertain_dir / f"{clip_id}_metadata.json"
            
            if not metadata_file.exists():
                print(f"Metadata file not found for clip: {clip_id}")
                return False
            
            # Load existing metadata
            with open(metadata_file, 'r', encoding='utf-8') as f:
                clip_data = json.load(f)
            
            # Update metadata
            clip_data['status'] = 'corrected'
            clip_data['corrected_text'] = corrected_text
            clip_data['corrected_by'] = user_id
            clip_data['correction_timestamp'] = int(time.time())
            
            # Save updated metadata
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(clip_data, f, indent=2, ensure_ascii=False)
            
            # Add to corrections database
            correction_entry = {
                "clip_id": clip_id,
                "original_text": clip_data['transcribed_text'],
                "corrected_text": corrected_text,
                "audio_hash": clip_data['metadata'].get('audio_hash'),
                "confidence": clip_data['confidence'],
                "user_id": user_id,
                "timestamp": clip_data['correction_timestamp']
            }
            
            self.corrections['corrections'].append(correction_entry)
            
            # ENHANCED: Update audio hash mapping for exact audio recognition
            if correction_entry['audio_hash']:
                self.corrections['audio_hashes'][correction_entry['audio_hash']] = corrected_text
            
            # ENHANCED: Advanced vocabulary learning
            self._enhance_vocabulary_learning(clip_data['transcribed_text'], corrected_text, clip_data['confidence'])
            
            # ENHANCED: Update confidence calibration
            self._update_confidence_calibration(clip_data['confidence'], True)  # True = was incorrect
            
            # Save corrections
            self.save_corrections()
            
            # Update custom vocabulary
            self.custom_vocabulary = self.load_custom_vocabulary()
            
            # Add to local model training data
            if self.local_model:
                audio_file = None
                for ext in ['.wav', '.flac', '.aiff', '.mp3', '.webm']:
                    potential_file = self.uncertain_dir / f"{clip_id}{ext}"
                    if potential_file.exists():
                        audio_file = str(potential_file)
                        break
                
                if audio_file:
                    success = self.local_model.add_training_sample(
                        audio_file_path=audio_file,
                        correct_text=corrected_text,
                        original_transcription=clip_data['transcribed_text'],
                        confidence=clip_data['confidence']
                    )
                    if success:
                        print("🤖 Added correction to local model training data")
            
            # Move files to reviewed directory
            self.move_to_reviewed(clip_id)
            
            print(f"✅ Enhanced correction submitted for clip {clip_id}")
            print(f"🧠 Learning: '{clip_data['transcribed_text']}' → '{corrected_text}'")
            return True
            
        except Exception as e:
            print(f"Error submitting correction: {e}")
            return False
    
    def move_to_reviewed(self, clip_id: str):
        """Move corrected clip to reviewed directory"""
        try:
            # Move audio file
            for ext in ['.wav', '.flac', '.aiff', '.mp3']:
                audio_file = self.uncertain_dir / f"{clip_id}{ext}"
                if audio_file.exists():
                    new_audio_path = self.reviewed_dir / f"{clip_id}{ext}"
                    shutil.move(str(audio_file), str(new_audio_path))
                    break
            
            # Move metadata file
            metadata_file = self.uncertain_dir / f"{clip_id}_metadata.json"
            if metadata_file.exists():
                new_metadata_path = self.reviewed_dir / f"{clip_id}_metadata.json"
                shutil.move(str(metadata_file), str(new_metadata_path))
                
        except Exception as e:
            print(f"Error moving files for clip {clip_id}: {e}")
    
    def _enhance_vocabulary_learning(self, original_text: str, corrected_text: str, confidence: float):
        """Advanced vocabulary learning from corrections"""
        original_words = set(original_text.lower().split())
        corrected_words = set(corrected_text.lower().split())
        
        # Track new words that were missed
        new_words = corrected_words - original_words
        for word in new_words:
            if word not in self.corrections['vocabulary_improvements']:
                self.corrections['vocabulary_improvements'][word] = {
                    'count': 0,
                    'confidence_levels': [],
                    'patterns': []
                }
            
            self.corrections['vocabulary_improvements'][word]['count'] += 1
            self.corrections['vocabulary_improvements'][word]['confidence_levels'].append(confidence)
            
            # Track patterns of misrecognition
            for orig_word in original_words:
                if self._words_similar(orig_word, word):
                    pattern = f"{orig_word}→{word}"
                    if pattern not in self.corrections['vocabulary_improvements'][word]['patterns']:
                        self.corrections['vocabulary_improvements'][word]['patterns'].append(pattern)
        
        # Track words that were incorrectly recognized
        removed_words = original_words - corrected_words
        for word in removed_words:
            if 'misrecognitions' not in self.corrections:
                self.corrections['misrecognitions'] = {}
            
            if word not in self.corrections['misrecognitions']:
                self.corrections['misrecognitions'][word] = {
                    'count': 0,
                    'confidence_levels': [],
                    'correct_alternatives': []
                }
            
            self.corrections['misrecognitions'][word]['count'] += 1
            self.corrections['misrecognitions'][word]['confidence_levels'].append(confidence)
            
            # Find what it should have been
            for correct_word in corrected_words:
                if self._words_similar(word, correct_word):
                    if correct_word not in self.corrections['misrecognitions'][word]['correct_alternatives']:
                        self.corrections['misrecognitions'][word]['correct_alternatives'].append(correct_word)
    
    def _words_similar(self, word1: str, word2: str) -> bool:
        """Check if two words are phonetically or visually similar"""
        if len(word1) == 0 or len(word2) == 0:
            return False
        
        # Simple similarity check - could be enhanced with phonetic algorithms
        if abs(len(word1) - len(word2)) > 2:
            return False
        
        # Check for common character patterns
        common_chars = set(word1.lower()) & set(word2.lower())
        min_len = min(len(word1), len(word2))
        
        return len(common_chars) >= min_len * 0.6
    
    def _update_confidence_calibration(self, predicted_confidence: float, was_incorrect: bool):
        """Update confidence calibration based on correction feedback"""
        if 'confidence_calibration' not in self.corrections:
            self.corrections['confidence_calibration'] = {
                'samples': [],
                'accuracy_by_confidence': {}
            }
        
        # Add sample for calibration
        self.corrections['confidence_calibration']['samples'].append({
            'confidence': predicted_confidence,
            'correct': not was_incorrect,
            'timestamp': int(time.time())
        })
        
        # Keep only recent samples (last 1000)
        if len(self.corrections['confidence_calibration']['samples']) > 1000:
            self.corrections['confidence_calibration']['samples'] = \
                self.corrections['confidence_calibration']['samples'][-1000:]
        
        # Update accuracy statistics by confidence bins
        confidence_bin = int(predicted_confidence * 10) / 10  # Round to nearest 0.1
        if confidence_bin not in self.corrections['confidence_calibration']['accuracy_by_confidence']:
            self.corrections['confidence_calibration']['accuracy_by_confidence'][confidence_bin] = {
                'correct': 0,
                'total': 0
            }
        
        self.corrections['confidence_calibration']['accuracy_by_confidence'][confidence_bin]['total'] += 1
        if not was_incorrect:
            self.corrections['confidence_calibration']['accuracy_by_confidence'][confidence_bin]['correct'] += 1
    
    def get_confidence_accuracy(self, confidence: float) -> float:
        """Get expected accuracy for a given confidence level based on historical data"""
        if 'confidence_calibration' not in self.corrections:
            return confidence  # Default to predicted confidence
        
        confidence_bin = int(confidence * 10) / 10
        calibration_data = self.corrections['confidence_calibration']['accuracy_by_confidence']
        
        if confidence_bin in calibration_data:
            stats = calibration_data[confidence_bin]
            if stats['total'] >= 5:  # Minimum samples for reliability
                return stats['correct'] / stats['total']
        
        # Fallback: interpolate from nearby bins or use predicted confidence
        return confidence
    
    def get_training_stats(self) -> Dict:
        """Get enhanced statistics about training data"""
        pending_count = len(self.get_pending_reviews())
        corrected_count = len(list(self.reviewed_dir.glob("*_metadata.json")))
        
        # Word-level statistics
        pending_words_count = len(self.get_pending_word_reviews())
        corrected_words_count = len(list(self.reviewed_words_dir.glob("*_metadata.json")))
        
        # Calculate learning statistics
        vocab_improvements = self.corrections.get('vocabulary_improvements', {})
        total_new_words = len(vocab_improvements)
        total_learning_instances = sum(
            item['count'] if isinstance(item, dict) else item 
            for item in vocab_improvements.values()
        )
        
        # Word corrections
        word_corrections = self.corrections.get('word_corrections', [])
        total_word_corrections = len(word_corrections)
        
        # Calculate confidence calibration accuracy
        calibration_accuracy = 0.0
        if 'confidence_calibration' in self.corrections:
            samples = self.corrections['confidence_calibration']['samples']
            if samples:
                correct_predictions = sum(1 for s in samples if s['correct'])
                calibration_accuracy = correct_predictions / len(samples)
        
        # Get local model statistics
        local_model_stats = {}
        if self.local_model:
            local_model_stats = self.local_model.get_training_stats()

        return {
            "pending_reviews": pending_count,
            "completed_corrections": corrected_count,
            "total_corrections": len(self.corrections.get('corrections', [])),
            "pending_words": pending_words_count,
            "completed_word_corrections": corrected_words_count,
            "total_word_corrections": total_word_corrections,
            "vocabulary_improvements": total_new_words,
            "learning_instances": total_learning_instances,
            "confidence_threshold": self.confidence_threshold,
            "calibration_accuracy": calibration_accuracy,
            "misrecognition_patterns": len(self.corrections.get('misrecognitions', {})),
            "local_model": local_model_stats
        }
    
    def train_local_model(self) -> bool:
        """Train the local speech recognition model"""
        if not self.local_model:
            print("⚠️ Local model not available")
            return False
        
        print("🎯 Training local speech recognition model...")
        success = self.local_model.train_model()
        
        if success:
            print("✅ Local model training completed successfully!")
        else:
            print("❌ Local model training failed")
        
        return success
    
    def get_local_model_info(self) -> Dict:
        """Get information about the local model"""
        if not self.local_model:
            return {
                "available": False,
                "error": "Local model not initialized"
            }
        
        stats = self.local_model.get_training_stats()
        return {
            "available": True,
            "stats": stats,
            "can_train": stats['total_samples'] >= 5,
            "training_recommendation": self._get_training_recommendation(stats)
        }
    
    def _get_training_recommendation(self, stats: Dict) -> str:
        """Get recommendation for local model training"""
        total_samples = stats.get('total_samples', 0)
        
        if total_samples == 0:
            return "No training data available. Submit some corrections first."
        elif total_samples < 5:
            return f"Need {5 - total_samples} more corrections to start training."
        elif total_samples < 20:
            return "Ready to train! More corrections will improve accuracy."
        elif not stats.get('model_trained', False):
            return "Good training data available. Ready to train model!"
        else:
            return "Model trained and ready. Add more corrections to improve further."


def main():
    """CLI interface for testing"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python enhanced_speech_analyzer.py <audio_file>")
        print("Supported formats: WAV, FLAC, AIFF")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    
    if not os.path.exists(audio_file):
        print(f"Error: Audio file '{audio_file}' not found")
        sys.exit(1)
    
    # Initialize analyzer
    analyzer = EnhancedSpeechAnalyzer()
    
    # Analyze audio
    result = analyzer.analyze_audio_file_with_training(audio_file)
    
    # Print results
    print("\n" + "="*60)
    print("ENHANCED SPEECH EMOTION ANALYSIS RESULTS")
    print("="*60)
    print(f"Transcription: '{result['transcription']}'")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Needs Review: {result['needs_review']}")
    if result['clip_id']:
        print(f"Clip ID: {result['clip_id']}")
    
    if result["success"]:
        print(f"Processing time: {result['processing_time']:.2f} seconds")
        
        # Detailed emotion breakdown
        emotions = result["emotion_analysis"]["emotions"]
        print(f"\nDetailed Emotion Breakdown:")
        for emotion, prob in sorted(emotions.items(), key=lambda x: x[1], reverse=True):
            print(f"  {emotion.title()}: {prob:.1%}")


if __name__ == "__main__":
    main()
