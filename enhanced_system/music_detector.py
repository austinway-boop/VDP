#!/usr/bin/env python3
"""
Music Detection and Identification Module
Detects background music in audio and identifies songs using Chromaprint + AcoustID
"""

import numpy as np
import librosa
import soundfile as sf
from typing import List, Tuple, Dict, Optional
import json
import requests
import os
from pathlib import Path

try:
    import acoustid
    import chromaprint
    MUSIC_DETECTION_AVAILABLE = True
except ImportError:
    MUSIC_DETECTION_AVAILABLE = False
    print("⚠️ Music detection dependencies not available. Install: pip install pyacoustid chromaprint-python")

class MusicDetector:
    def __init__(self):
        """Initialize the music detection system"""
        self.sample_rate = 22050  # Standard sample rate for analysis
        self.frame_length = 2048
        self.hop_length = 512
        
        # Music detection parameters
        self.music_threshold = 0.6  # Confidence threshold for music detection
        self.min_music_duration = 2.0  # Minimum duration in seconds
        self.acoustid_api_key = os.getenv("ACOUSTID_API_KEY", "your-acoustid-api-key-here")
        
        # Music vs speech characteristics
        self.music_freq_range = (80, 8000)  # Hz range where music typically occurs
        self.harmonic_threshold = 0.7  # Threshold for harmonic content
        
        print("🎵 Music detector initialized")
        if not MUSIC_DETECTION_AVAILABLE:
            print("⚠️ Music identification will be limited without Chromaprint")
    
    def detect_music(self, audio_file_path: str) -> Dict:
        """
        Detect background music in an audio file
        Returns segments with music timing and song identification
        """
        try:
            # Load audio
            y, sr = librosa.load(audio_file_path, sr=self.sample_rate)
            duration = len(y) / sr
            
            print(f"🎵 Analyzing audio for background music: {duration:.2f}s")
            
            # Extract features for music detection
            music_features = self._extract_music_features(y, sr)
            
            # Detect music segments
            music_segments = self._identify_music_segments(music_features, sr)
            
            # Try to identify songs in music segments
            identified_songs = []
            if MUSIC_DETECTION_AVAILABLE and music_segments:
                identified_songs = self._identify_songs(audio_file_path, music_segments, y, sr)
            
            # Calculate overall music statistics
            total_music_time = sum(seg['duration'] for seg in music_segments)
            music_percentage = (total_music_time / duration) * 100 if duration > 0 else 0
            
            # Generate timeline data for visualization
            timeline_data = self._generate_music_timeline_data(music_features, duration)
            
            result = {
                'audio_duration': duration,
                'music_segments': music_segments,
                'identified_songs': identified_songs,
                'total_music_time': total_music_time,
                'music_percentage': music_percentage,
                'num_music_segments': len(music_segments),
                'timeline_data': timeline_data,
                'analysis_method': 'audio_features'
            }
            
            if music_segments:
                print(f"🎵 Found {len(music_segments)} music segments ({music_percentage:.1f}% of audio)")
                if identified_songs:
                    print(f"🎼 Identified {len(identified_songs)} songs")
            else:
                print("🔇 No background music detected")
            
            return result
            
        except Exception as e:
            print(f"❌ Error detecting music: {e}")
            return {
                'audio_duration': 0,
                'music_segments': [],
                'identified_songs': [],
                'total_music_time': 0,
                'music_percentage': 0,
                'num_music_segments': 0,
                'timeline_data': {'points': [], 'max_intensity': 0, 'avg_intensity': 0},
                'error': str(e)
            }
    
    def _extract_music_features(self, y: np.ndarray, sr: int) -> Dict:
        """Extract audio features that indicate music"""
        
        # 1. Harmonic-percussive separation
        y_harmonic, y_percussive = librosa.effects.hpss(y)
        
        # 2. Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=self.hop_length)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=self.hop_length)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr, hop_length=self.hop_length)[0]
        
        # 3. Harmonic content analysis
        harmonic_energy = librosa.feature.rms(y=y_harmonic, hop_length=self.hop_length)[0]
        percussive_energy = librosa.feature.rms(y=y_percussive, hop_length=self.hop_length)[0]
        
        # 4. Chroma features (key indicator of music)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=self.hop_length)
        chroma_variance = np.var(chroma, axis=0)
        
        # 5. Tempo and rhythm analysis
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=self.hop_length)
        
        # 6. MFCC features
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=self.hop_length)
        
        # 7. Spectral contrast
        spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr, hop_length=self.hop_length)
        
        # 8. Zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(y, hop_length=self.hop_length)[0]
        
        # Time axis
        times = librosa.frames_to_time(np.arange(len(spectral_centroids)), sr=sr, hop_length=self.hop_length)
        
        return {
            'times': times,
            'y_harmonic': y_harmonic,
            'y_percussive': y_percussive,
            'spectral_centroids': spectral_centroids,
            'spectral_rolloff': spectral_rolloff,
            'spectral_bandwidth': spectral_bandwidth,
            'harmonic_energy': harmonic_energy,
            'percussive_energy': percussive_energy,
            'chroma_variance': chroma_variance,
            'tempo': tempo,
            'beats': beats,
            'mfccs': mfccs,
            'spectral_contrast': spectral_contrast,
            'zero_crossing_rate': zcr
        }
    
    def _identify_music_segments(self, features: Dict, sr: int) -> List[Dict]:
        """Identify time segments that contain music"""
        times = features['times']
        music_scores = []
        
        # Calculate music likelihood for each time frame
        for i in range(len(times)):
            score = self._calculate_music_score(features, i)
            music_scores.append(score)
        
        music_scores = np.array(music_scores)
        
        # Smooth the scores to reduce noise
        try:
            from scipy.ndimage import gaussian_filter1d
            music_scores_smooth = gaussian_filter1d(music_scores, sigma=3)
        except ImportError:
            # Fallback: simple moving average
            window_size = 7
            music_scores_smooth = np.convolve(music_scores, 
                                            np.ones(window_size)/window_size, 
                                            mode='same')
        
        # Find segments above threshold
        music_mask = music_scores_smooth > self.music_threshold
        
        # Group consecutive music frames into segments
        segments = []
        in_music = False
        start_time = 0
        
        for i, is_music in enumerate(music_mask):
            if is_music and not in_music:
                # Start of music segment
                start_time = times[i]
                in_music = True
            elif not is_music and in_music:
                # End of music segment
                end_time = times[i-1] if i > 0 else times[i]
                duration = end_time - start_time
                
                # Only include segments longer than minimum duration
                if duration >= self.min_music_duration:
                    avg_confidence = np.mean(music_scores_smooth[
                        int(start_time * len(times) / times[-1]):
                        int(end_time * len(times) / times[-1])
                    ]) if len(times) > 0 else 0
                    
                    segments.append({
                        'start_time': round(start_time, 2),
                        'end_time': round(end_time, 2),
                        'duration': round(duration, 2),
                        'confidence': round(float(avg_confidence), 3),
                        'peak_confidence': round(float(np.max(music_scores_smooth[
                            int(start_time * len(times) / times[-1]):
                            int(end_time * len(times) / times[-1])
                        ])), 3) if len(times) > 0 else 0
                    })
                
                in_music = False
        
        # Handle case where music continues to end of audio
        if in_music and len(times) > 0:
            end_time = times[-1]
            duration = end_time - start_time
            if duration >= self.min_music_duration:
                avg_confidence = np.mean(music_scores_smooth[
                    int(start_time * len(times) / times[-1]):
                ]) if len(times) > 0 else 0
                
                segments.append({
                    'start_time': round(start_time, 2),
                    'end_time': round(end_time, 2),
                    'duration': round(duration, 2),
                    'confidence': round(float(avg_confidence), 3),
                    'peak_confidence': round(float(np.max(music_scores_smooth[
                        int(start_time * len(times) / times[-1]):
                    ])), 3) if len(times) > 0 else 0
                })
        
        return segments
    
    def _calculate_music_score(self, features: Dict, frame_idx: int) -> float:
        """Calculate music likelihood score for a specific time frame"""
        try:
            score_components = []
            
            # 1. Harmonic vs percussive energy ratio (music has more harmonic content)
            harmonic_energy = features['harmonic_energy'][frame_idx]
            percussive_energy = features['percussive_energy'][frame_idx]
            total_energy = harmonic_energy + percussive_energy
            
            if total_energy > 0:
                harmonic_ratio = harmonic_energy / total_energy
                harmonic_score = min(harmonic_ratio * 1.5, 1.0)  # Boost harmonic content
                score_components.append(harmonic_score * 0.3)
            
            # 2. Chroma variance (music has consistent harmonic structure)
            chroma_var = features['chroma_variance'][frame_idx]
            chroma_score = min(chroma_var * 2, 1.0)  # Normalize
            score_components.append(chroma_score * 0.25)
            
            # 3. Spectral characteristics
            centroid = features['spectral_centroids'][frame_idx]
            bandwidth = features['spectral_bandwidth'][frame_idx]
            
            # Music typically has broader spectral content
            centroid_score = min(centroid / 2000, 1.0)  # Normalize
            bandwidth_score = min(bandwidth / 1500, 1.0)  # Normalize
            score_components.append(centroid_score * 0.15)
            score_components.append(bandwidth_score * 0.15)
            
            # 4. Spectral contrast (music has more distinct frequency bands)
            if frame_idx < features['spectral_contrast'].shape[1]:
                contrast_mean = np.mean(features['spectral_contrast'][:, frame_idx])
                contrast_score = min(contrast_mean / 25, 1.0)  # Normalize
                score_components.append(contrast_score * 0.15)
            
            # Combine all components
            final_score = sum(score_components)
            
            return min(max(final_score, 0.0), 1.0)  # Clamp to 0-1 range
            
        except Exception as e:
            print(f"❌ Error calculating music score at frame {frame_idx}: {e}")
            return 0.0
    
    def _generate_music_timeline_data(self, features: Dict, duration: float) -> Dict:
        """Generate timeline data for music visualization"""
        try:
            times = features['times']
            music_scores = []
            
            # Calculate music scores for each time frame
            for i in range(len(times)):
                score = self._calculate_music_score(features, i)
                music_scores.append(score)
            
            # Smooth the scores
            try:
                from scipy.ndimage import gaussian_filter1d
                music_scores_smooth = gaussian_filter1d(np.array(music_scores), sigma=3)
            except ImportError:
                # Fallback: simple moving average
                window_size = 7
                music_scores_smooth = np.convolve(music_scores, 
                                                np.ones(window_size)/window_size, 
                                                mode='same')
            
            # Create timeline data points (sample every 0.1 seconds)
            timeline_points = []
            target_interval = 0.1  # 100ms intervals
            
            for target_time in np.arange(0, duration, target_interval):
                # Find closest time index
                closest_idx = np.argmin(np.abs(times - target_time)) if len(times) > 0 else 0
                
                if closest_idx < len(music_scores_smooth):
                    music_intensity = float(music_scores_smooth[closest_idx])
                else:
                    music_intensity = 0.0
                
                timeline_points.append({
                    'time': round(target_time, 2),
                    'music_intensity': round(music_intensity, 3)
                })
            
            return {
                'points': timeline_points,
                'max_intensity': float(np.max(music_scores_smooth)) if len(music_scores_smooth) > 0 else 0.0,
                'avg_intensity': float(np.mean(music_scores_smooth)) if len(music_scores_smooth) > 0 else 0.0,
                'sample_interval': target_interval
            }
            
        except Exception as e:
            print(f"❌ Error generating music timeline data: {e}")
            return {
                'points': [],
                'max_intensity': 0.0,
                'avg_intensity': 0.0,
                'sample_interval': 0.1
            }
    
    def _identify_songs(self, audio_file_path: str, music_segments: List[Dict], y: np.ndarray, sr: int) -> List[Dict]:
        """Identify songs in detected music segments using AcoustID"""
        identified_songs = []
        
        if not MUSIC_DETECTION_AVAILABLE:
            return identified_songs
        
        try:
            for segment in music_segments[:3]:  # Limit to first 3 segments to avoid API limits
                print(f"🔍 Identifying music in segment {segment['start_time']}s-{segment['end_time']}s...")
                
                # Extract audio segment
                start_sample = int(segment['start_time'] * sr)
                end_sample = int(segment['end_time'] * sr)
                segment_audio = y[start_sample:end_sample]
                
                # Isolate music from speech (enhance harmonic content)
                isolated_music = self._isolate_music(segment_audio, sr)
                
                # Generate fingerprint
                fingerprint = self._generate_fingerprint(isolated_music, sr)
                
                if fingerprint:
                    # Query AcoustID
                    song_info = self._query_acoustid(fingerprint, segment['duration'])
                    
                    if song_info:
                        song_info.update({
                            'segment_start': segment['start_time'],
                            'segment_end': segment['end_time'],
                            'segment_confidence': segment['confidence']
                        })
                        identified_songs.append(song_info)
                        print(f"🎼 Found: {song_info.get('title', 'Unknown')} by {song_info.get('artist', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Error identifying songs: {e}")
        
        return identified_songs
    
    def _isolate_music(self, audio_segment: np.ndarray, sr: int) -> np.ndarray:
        """Isolate music from speech using harmonic-percussive separation"""
        try:
            # Use harmonic-percussive separation to isolate music
            y_harmonic, y_percussive = librosa.effects.hpss(audio_segment)
            
            # Enhance harmonic content (where music typically resides)
            isolated_music = y_harmonic + (y_percussive * 0.3)  # Keep some percussion
            
            # Apply spectral filtering to enhance music frequencies
            # Remove very low frequencies (speech fundamentals)
            stft = librosa.stft(isolated_music)
            freqs = librosa.fft_frequencies(sr=sr)
            
            # Create frequency mask (keep music range, reduce speech range)
            freq_mask = np.ones_like(freqs)
            speech_range = (80, 300)  # Typical speech fundamental range
            music_range = (200, 4000)  # Typical music range
            
            for i, freq in enumerate(freqs):
                if speech_range[0] <= freq <= speech_range[1]:
                    freq_mask[i] = 0.3  # Reduce speech frequencies
                elif music_range[0] <= freq <= music_range[1]:
                    freq_mask[i] = 1.2  # Enhance music frequencies
            
            # Apply frequency mask
            stft_filtered = stft * freq_mask[:, np.newaxis]
            isolated_music = librosa.istft(stft_filtered)
            
            return isolated_music
            
        except Exception as e:
            print(f"⚠️ Error isolating music: {e}")
            return audio_segment  # Return original if isolation fails
    
    def _generate_fingerprint(self, audio_segment: np.ndarray, sr: int) -> Optional[str]:
        """Generate Chromaprint fingerprint for song identification"""
        try:
            if not MUSIC_DETECTION_AVAILABLE:
                return None
            
            # Convert to format expected by Chromaprint
            audio_int16 = (audio_segment * 32767).astype(np.int16)
            
            # Generate fingerprint
            fingerprint = acoustid.fingerprint(sr, audio_int16)[1]
            return fingerprint
            
        except Exception as e:
            print(f"⚠️ Error generating fingerprint: {e}")
            return None
    
    def _query_acoustid(self, fingerprint: str, duration: float) -> Optional[Dict]:
        """Query AcoustID database for song identification"""
        try:
            if self.acoustid_api_key == "your-acoustid-api-key-here":
                print("⚠️ AcoustID API key not configured - skipping song identification")
                return None
            
            # Query AcoustID
            results = acoustid.lookup(self.acoustid_api_key, fingerprint, duration)
            
            for score, recording_id, title, artist in results:
                if score > 0.8:  # High confidence match
                    return {
                        'title': title or 'Unknown Title',
                        'artist': artist or 'Unknown Artist', 
                        'recording_id': recording_id,
                        'match_confidence': round(score, 3),
                        'source': 'acoustid'
                    }
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error querying AcoustID: {e}")
            return None
    
    def get_music_summary(self, music_data: Dict) -> str:
        """Generate a human-readable summary of music detection"""
        segments = music_data.get('music_segments', [])
        songs = music_data.get('identified_songs', [])
        
        if not segments:
            return "No background music detected in this audio."
        
        total_time = music_data.get('total_music_time', 0)
        percentage = music_data.get('music_percentage', 0)
        
        summary_parts = [
            f"🎵 {len(segments)} music segment{'s' if len(segments) != 1 else ''} detected",
            f"⏱️ Total music: {total_time:.1f}s ({percentage:.1f}% of audio)"
        ]
        
        if songs:
            summary_parts.append("🎼 Identified songs:")
            for song in songs:
                summary_parts.append(
                    f"   • {song['title']} by {song['artist']} "
                    f"({song['segment_start']:.1f}s-{song['segment_end']:.1f}s)"
                )
        
        return "\n".join(summary_parts)


# Global music detector instance
music_detector = MusicDetector()

def detect_music_in_audio(audio_file_path: str) -> Dict:
    """Detect music in an audio file"""
    return music_detector.detect_music(audio_file_path)

def get_music_summary(music_data: Dict) -> str:
    """Get human-readable music summary"""
    return music_detector.get_music_summary(music_data)


if __name__ == "__main__":
    # Test the music detector
    import sys
    
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        print(f"🎵 Testing music detection on: {audio_file}")
        
        result = detect_music_in_audio(audio_file)
        print(f"📊 Results: {json.dumps(result, indent=2)}")
        print(f"📝 Summary: {get_music_summary(result)}")
    else:
        print("Usage: python3 music_detector.py <audio_file>")
