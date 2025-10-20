#!/usr/bin/env python3
"""
Local Speech Recognition Model
Trains on user corrections to provide fallback speech recognition for uncertain cases
"""

import json
import os
import time
import pickle
import hashlib
import librosa
import soundfile as sf
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

try:
    import vosk
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("⚠️ Vosk not available. Local model will use feature-based matching only.")

class LocalSpeechModel:
    def __init__(self, model_dir: Path = None):
        """Initialize the local speech recognition model"""
        self.model_dir = model_dir or Path(__file__).parent / "local_model"
        self.model_dir.mkdir(exist_ok=True)
        
        # Model components
        self.vosk_model = None
        self.vosk_recognizer = None
        self.audio_features_model = None
        self.text_vectorizer = None
        self.feature_scaler = None
        
        # Training data
        self.training_data = []
        self.audio_features_cache = {}
        
        # Model files
        self.model_files = {
            'training_data': self.model_dir / 'training_data.json',
            'audio_features': self.model_dir / 'audio_features.pkl',
            'text_vectorizer': self.model_dir / 'text_vectorizer.pkl',
            'feature_scaler': self.model_dir / 'feature_scaler.pkl',
            'audio_model': self.model_dir / 'audio_model.pkl'
        }
        
        # Initialize components
        self._initialize_vosk()
        self._load_training_data()
        self._load_models()
        
        print(f"🤖 Local Speech Model initialized")
        print(f"   Training samples: {len(self.training_data)}")
        print(f"   Vosk available: {VOSK_AVAILABLE and self.vosk_model is not None}")
    
    def _initialize_vosk(self):
        """Initialize Vosk model for local speech recognition"""
        if not VOSK_AVAILABLE:
            return
        
        try:
            # Try to find a Vosk model (user would need to download one)
            vosk_model_paths = [
                Path.home() / "voyour-api-key-here",
                Path("/usr/local/share/voyour-api-key-here"),
                self.model_dir / "voyour-api-key-here"
            ]
            
            for model_path in vosk_model_paths:
                if model_path.exists():
                    self.vosk_model = vosk.Model(str(model_path))
                    self.vosk_recognizer = vosk.KaldiRecognizer(self.vosk_model, 16000)
                    print(f"✅ Vosk model loaded from: {model_path}")
                    return
            
            print("ℹ️ No Vosk model found. Download a model for enhanced local recognition.")
            print("   Example: wget https://alphacephei.com/vosk/models/voyour-api-key-here.22.zip")
            
        except Exception as e:
            print(f"⚠️ Error initializing Vosk: {e}")
    
    def _load_training_data(self):
        """Load existing training data"""
        if self.model_files['training_data'].exists():
            try:
                with open(self.model_files['training_data'], 'r') as f:
                    self.training_data = json.load(f)
                print(f"📚 Loaded {len(self.training_data)} training samples")
            except Exception as e:
                print(f"⚠️ Error loading training data: {e}")
                self.training_data = []
    
    def _load_models(self):
        """Load trained models"""
        try:
            # Load text vectorizer
            if self.model_files['text_vectorizer'].exists():
                with open(self.model_files['text_vectorizer'], 'rb') as f:
                    self.text_vectorizer = pickle.load(f)
            
            # Load feature scaler
            if self.model_files['feature_scaler'].exists():
                with open(self.model_files['feature_scaler'], 'rb') as f:
                    self.feature_scaler = pickle.load(f)
            
            # Load audio features model
            if self.model_files['audio_model'].exists():
                with open(self.model_files['audio_model'], 'rb') as f:
                    self.audio_features_model = pickle.load(f)
                    
            print("🔧 Loaded existing models")
            
        except Exception as e:
            print(f"⚠️ Error loading models: {e}")
    
    def extract_audio_features(self, audio_file_path: str) -> np.ndarray:
        """Extract audio features for matching"""
        try:
            # Load audio
            y, sr = librosa.load(audio_file_path, sr=16000)
            
            # Extract features
            features = []
            
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            features.extend([
                np.mean(spectral_centroids),
                np.std(spectral_centroids),
                np.max(spectral_centroids),
                np.min(spectral_centroids)
            ])
            
            # MFCC features
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            for i in range(13):
                features.extend([
                    np.mean(mfccs[i]),
                    np.std(mfccs[i])
                ])
            
            # Rhythm features
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            features.append(tempo)
            
            # Energy features
            rms = librosa.feature.rms(y=y)[0]
            features.extend([
                np.mean(rms),
                np.std(rms)
            ])
            
            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            features.extend([
                np.mean(zcr),
                np.std(zcr)
            ])
            
            return np.array(features)
            
        except Exception as e:
            print(f"⚠️ Error extracting audio features: {e}")
            return np.zeros(32)  # Return zero features if extraction fails
    
    def add_training_sample(self, audio_file_path: str, correct_text: str, 
                          original_transcription: str = "", confidence: float = 0.0):
        """Add a new training sample from user correction"""
        try:
            # Calculate audio hash
            with open(audio_file_path, 'rb') as f:
                audio_hash = hashlib.md5(f.read()).hexdigest()
            
            # Extract audio features
            audio_features = self.extract_audio_features(audio_file_path)
            
            # Create training sample
            sample = {
                'audio_hash': audio_hash,
                'audio_file': str(audio_file_path),
                'correct_text': correct_text.lower().strip(),
                'original_transcription': original_transcription.lower().strip(),
                'confidence': confidence,
                'timestamp': int(time.time()),
                'audio_features': audio_features.tolist()
            }
            
            # Check for duplicates
            existing_hashes = {s['audio_hash'] for s in self.training_data}
            if audio_hash not in existing_hashes:
                self.training_data.append(sample)
                print(f"📚 Added training sample: '{correct_text}' (hash: {audio_hash[:8]})")
                
                # Save training data
                self._save_training_data()
                return True
            else:
                print(f"⚠️ Training sample already exists for audio hash: {audio_hash[:8]}")
                return False
                
        except Exception as e:
            print(f"⚠️ Error adding training sample: {e}")
            return False
    
    def _save_training_data(self):
        """Save training data to file"""
        try:
            with open(self.model_files['training_data'], 'w') as f:
                json.dump(self.training_data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving training data: {e}")
    
    def train_model(self):
        """Train the local speech recognition model"""
        if len(self.training_data) < 5:
            print(f"⚠️ Need at least 5 training samples (have {len(self.training_data)})")
            return False
        
        print(f"🎯 Training local model with {len(self.training_data)} samples...")
        
        try:
            # Prepare training data
            texts = [sample['correct_text'] for sample in self.training_data]
            audio_features = np.array([sample['audio_features'] for sample in self.training_data])
            
            # Train text vectorizer
            self.text_vectorizer = TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 2),
                lowercase=True
            )
            text_features = self.text_vectorizer.fit_transform(texts)
            
            # Train feature scaler
            self.feature_scaler = StandardScaler()
            audio_features_scaled = self.feature_scaler.fit_transform(audio_features)
            
            # Combine features
            combined_features = np.hstack([
                audio_features_scaled,
                text_features.toarray()
            ])
            
            # Train classification model (for feature similarity)
            self.audio_features_model = RandomForestClassifier(
                n_estimators=100,
                random_state=42
            )
            
            # Create labels based on text similarity groups
            labels = self._create_similarity_labels(texts)
            self.audio_features_model.fit(combined_features, labels)
            
            # Save models
            self._save_models()
            
            print("✅ Local model training completed!")
            return True
            
        except Exception as e:
            print(f"⚠️ Error training model: {e}")
            return False
    
    def _create_similarity_labels(self, texts: List[str]) -> List[int]:
        """Create similarity-based labels for training"""
        # Simple clustering based on text similarity
        vectorizer = TfidfVectorizer()
        text_vectors = vectorizer.fit_transform(texts)
        
        # Use cosine similarity to group similar texts
        similarity_matrix = cosine_similarity(text_vectors)
        
        # Simple clustering: assign same label to very similar texts
        labels = []
        current_label = 0
        assigned = set()
        
        for i, text in enumerate(texts):
            if i in assigned:
                continue
                
            labels.append(current_label)
            assigned.add(i)
            
            # Find similar texts
            for j in range(i + 1, len(texts)):
                if j not in assigned and similarity_matrix[i][j] > 0.7:
                    labels.append(current_label)
                    assigned.add(j)
            
            current_label += 1
        
        # Fill remaining with unique labels
        while len(labels) < len(texts):
            labels.append(current_label)
            current_label += 1
        
        return labels[:len(texts)]
    
    def _save_models(self):
        """Save trained models"""
        try:
            # Save text vectorizer
            with open(self.model_files['text_vectorizer'], 'wb') as f:
                pickle.dump(self.text_vectorizer, f)
            
            # Save feature scaler
            with open(self.model_files['feature_scaler'], 'wb') as f:
                pickle.dump(self.feature_scaler, f)
            
            # Save audio model
            with open(self.model_files['audio_model'], 'wb') as f:
                pickle.dump(self.audio_features_model, f)
                
            print("💾 Models saved successfully")
            
        except Exception as e:
            print(f"⚠️ Error saving models: {e}")
    
    def recognize_speech(self, audio_file_path: str) -> Tuple[str, float, Dict]:
        """Recognize speech using the local model"""
        try:
            results = []
            
            # Method 1: Vosk recognition (if available)
            if self.vosk_model and self.vosk_recognizer:
                vosk_result = self._recognize_with_vosk(audio_file_path)
                if vosk_result[0]:
                    results.append({
                        'method': 'vosk',
                        'text': vosk_result[0],
                        'confidence': vosk_result[1]
                    })
            
            # Method 2: Audio feature matching
            if self.audio_features_model and len(self.training_data) > 0:
                feature_result = self._recognize_with_features(audio_file_path)
                if feature_result[0]:
                    results.append({
                        'method': 'features',
                        'text': feature_result[0],
                        'confidence': feature_result[1]
                    })
            
            # Method 3: Direct audio hash lookup
            hash_result = self._recognize_with_hash(audio_file_path)
            if hash_result[0]:
                results.append({
                    'method': 'hash',
                    'text': hash_result[0],
                    'confidence': hash_result[1]
                })
            
            # Select best result
            if results:
                best_result = max(results, key=lambda x: x['confidence'])
                return best_result['text'], best_result['confidence'], {
                    'method': best_result['method'],
                    'all_results': results,
                    'source': 'local_model'
                }
            else:
                return "", 0.0, {'error': 'No recognition methods available'}
                
        except Exception as e:
            print(f"⚠️ Error in local speech recognition: {e}")
            return "", 0.0, {'error': str(e)}
    
    def _recognize_with_vosk(self, audio_file_path: str) -> Tuple[str, float]:
        """Recognize speech using Vosk"""
        try:
            # Load and resample audio
            y, sr = librosa.load(audio_file_path, sr=16000)
            audio_data = (y * 32767).astype(np.int16).tobytes()
            
            # Reset recognizer
            self.vosk_recognizer.Reset()
            
            # Process audio
            if self.vosk_recognizer.AcceptWaveform(audio_data):
                result = json.loads(self.vosk_recognizer.Result())
                text = result.get('text', '').strip()
                confidence = 0.8  # Vosk doesn't provide confidence, use default
                return text, confidence
            else:
                partial = json.loads(self.vosk_recognizer.PartialResult())
                text = partial.get('partial', '').strip()
                confidence = 0.6  # Lower confidence for partial results
                return text, confidence
                
        except Exception as e:
            print(f"⚠️ Vosk recognition error: {e}")
            return "", 0.0
    
    def _recognize_with_features(self, audio_file_path: str) -> Tuple[str, float]:
        """Recognize speech using audio feature matching"""
        try:
            if not self.audio_features_model or not self.feature_scaler:
                return "", 0.0
            
            # Extract features from input audio
            input_features = self.extract_audio_features(audio_file_path)
            input_features_scaled = self.feature_scaler.transform([input_features])
            
            # Find most similar training sample
            best_match = None
            best_similarity = 0.0
            
            for sample in self.training_data:
                sample_features = np.array(sample['audio_features'])
                sample_features_scaled = self.feature_scaler.transform([sample_features])
                
                # Calculate cosine similarity
                similarity = cosine_similarity(input_features_scaled, sample_features_scaled)[0][0]
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = sample
            
            if best_match and best_similarity > 0.7:  # Threshold for similarity
                confidence = min(best_similarity, 0.9)  # Cap confidence
                return best_match['correct_text'], confidence
            
            return "", 0.0
            
        except Exception as e:
            print(f"⚠️ Feature matching error: {e}")
            return "", 0.0
    
    def _recognize_with_hash(self, audio_file_path: str) -> Tuple[str, float]:
        """Recognize speech using exact audio hash matching"""
        try:
            # Calculate audio hash
            with open(audio_file_path, 'rb') as f:
                audio_hash = hashlib.md5(f.read()).hexdigest()
            
            # Look for exact match
            for sample in self.training_data:
                if sample['audio_hash'] == audio_hash:
                    return sample['correct_text'], 1.0  # Perfect confidence for exact match
            
            return "", 0.0
            
        except Exception as e:
            print(f"⚠️ Hash matching error: {e}")
            return "", 0.0
    
    def get_training_stats(self) -> Dict:
        """Get statistics about the training data"""
        if not self.training_data:
            return {
                'total_samples': 0,
                'unique_texts': 0,
                'avg_confidence': 0.0,
                'model_trained': False
            }
        
        texts = [sample['correct_text'] for sample in self.training_data]
        confidences = [sample['confidence'] for sample in self.training_data]
        
        return {
            'total_samples': len(self.training_data),
            'unique_texts': len(set(texts)),
            'avg_confidence': np.mean(confidences) if confidences else 0.0,
            'model_trained': self.audio_features_model is not None,
            'vosk_available': self.vosk_model is not None,
            'oldest_sample': min(sample['timestamp'] for sample in self.training_data),
            'newest_sample': max(sample['timestamp'] for sample in self.training_data)
        }
    
    def clear_training_data(self):
        """Clear all training data (use with caution!)"""
        self.training_data = []
        self._save_training_data()
        
        # Remove model files
        for model_file in self.model_files.values():
            if model_file.exists():
                model_file.unlink()
        
        print("🗑️ Training data and models cleared")


if __name__ == "__main__":
    # Test the local model
    model = LocalSpeechModel()
    stats = model.get_training_stats()
    print(f"Training stats: {stats}")
