#!/usr/bin/env python3
"""
Laughter Detection Module
Detects laughter in audio clips and provides timing information
"""

import numpy as np
import librosa
import soundfile as sf
from typing import List, Tuple, Dict
import json
from pathlib import Path

class LaughterDetector:
    def __init__(self):
        """Initialize the laughter detection system"""
        self.sample_rate = 22050  # Standard sample rate for analysis
        self.frame_length = 2048
        self.hop_length = 512
        
        # Laughter characteristics (based on research)
        self.laughter_freq_range = (200, 4000)  # Hz range where laughter typically occurs
        self.min_laughter_duration = 0.3  # Minimum duration in seconds
        self.laughter_threshold = 0.6  # Confidence threshold for laughter detection
        
        print("😄 Laughter detector initialized")
    
    def detect_laughter(self, audio_file_path: str) -> Dict:
        """
        Detect laughter in an audio file
        Returns segments with laughter timing and confidence
        """
        try:
            # Load audio
            y, sr = librosa.load(audio_file_path, sr=self.sample_rate)
            duration = len(y) / sr
            
            print(f"🎵 Analyzing audio for laughter: {duration:.2f}s")
            
            # Extract features for laughter detection
            laughter_features = self._extract_laughter_features(y, sr)
            
            # Detect laughter segments
            laughter_segments = self._identify_laughter_segments(laughter_features, sr)
            
            # Calculate overall laughter statistics
            total_laughter_time = sum(seg['duration'] for seg in laughter_segments)
            laughter_percentage = (total_laughter_time / duration) * 100 if duration > 0 else 0
            
            # Generate timeline data for graphing
            timeline_data = self._generate_timeline_data(laughter_features, duration)
            
            result = {
                'audio_duration': duration,
                'laughter_segments': laughter_segments,
                'total_laughter_time': total_laughter_time,
                'laughter_percentage': laughter_percentage,
                'num_laughter_bursts': len(laughter_segments),
                'timeline_data': timeline_data,
                'analysis_method': 'audio_features'
            }
            
            print(f"😄 Found {len(laughter_segments)} laughter segments ({laughter_percentage:.1f}% of audio)")
            
            return result
            
        except Exception as e:
            print(f"❌ Error detecting laughter: {e}")
            return {
                'audio_duration': 0,
                'laughter_segments': [],
                'total_laughter_time': 0,
                'laughter_percentage': 0,
                'num_laughter_bursts': 0,
                'error': str(e)
            }
    
    def _extract_laughter_features(self, y: np.ndarray, sr: int) -> Dict:
        """Extract audio features that indicate laughter"""
        
        # 1. Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=self.hop_length)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, hop_length=self.hop_length)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr, hop_length=self.hop_length)[0]
        
        # 2. Energy features
        rms_energy = librosa.feature.rms(y=y, hop_length=self.hop_length)[0]
        
        # 3. Zero crossing rate (indicates voice vs. laughter)
        zcr = librosa.feature.zero_crossing_rate(y, hop_length=self.hop_length)[0]
        
        # 4. MFCC features (first 5 coefficients)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=5, hop_length=self.hop_length)
        
        # 5. Chroma features (harmonic content)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=self.hop_length)
        
        # 6. Tempo and rhythm
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=self.hop_length)
        
        # 7. Spectral contrast (distinguishes laughter from speech)
        spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr, hop_length=self.hop_length)
        
        # Time axis for alignment
        times = librosa.frames_to_time(np.arange(len(spectral_centroids)), sr=sr, hop_length=self.hop_length)
        
        return {
            'times': times,
            'spectral_centroids': spectral_centroids,
            'spectral_rolloff': spectral_rolloff,
            'spectral_bandwidth': spectral_bandwidth,
            'rms_energy': rms_energy,
            'zero_crossing_rate': zcr,
            'mfccs': mfccs,
            'chroma': chroma,
            'spectral_contrast': spectral_contrast,
            'tempo': tempo,
            'beats': beats
        }
    
    def _identify_laughter_segments(self, features: Dict, sr: int) -> List[Dict]:
        """Identify time segments that contain laughter"""
        times = features['times']
        laughter_scores = []
        
        # Calculate laughter likelihood for each time frame
        for i in range(len(times)):
            score = self._calculate_laughter_score(features, i)
            laughter_scores.append(score)
        
        laughter_scores = np.array(laughter_scores)
        
        # Smooth the scores to reduce noise
        from scipy.ndimage import gaussian_filter1d
        try:
            laughter_scores_smooth = gaussian_filter1d(laughter_scores, sigma=2)
        except ImportError:
            # Fallback: simple moving average if scipy not available
            window_size = 5
            laughter_scores_smooth = np.convolve(laughter_scores, 
                                               np.ones(window_size)/window_size, 
                                               mode='same')
        
        # Find segments above threshold
        laughter_mask = laughter_scores_smooth > self.laughter_threshold
        
        # Group consecutive laughter frames into segments
        segments = []
        in_laughter = False
        start_time = 0
        
        for i, is_laughter in enumerate(laughter_mask):
            if is_laughter and not in_laughter:
                # Start of laughter segment
                start_time = times[i]
                in_laughter = True
            elif not is_laughter and in_laughter:
                # End of laughter segment
                end_time = times[i-1] if i > 0 else times[i]
                duration = end_time - start_time
                
                # Only include segments longer than minimum duration
                if duration >= self.min_laughter_duration:
                    avg_confidence = np.mean(laughter_scores_smooth[
                        int(start_time * len(times) / times[-1]):
                        int(end_time * len(times) / times[-1])
                    ]) if len(times) > 0 else 0
                    
                    segments.append({
                        'start_time': round(start_time, 2),
                        'end_time': round(end_time, 2),
                        'duration': round(duration, 2),
                        'confidence': round(float(avg_confidence), 3),
                        'peak_confidence': round(float(np.max(laughter_scores_smooth[
                            int(start_time * len(times) / times[-1]):
                            int(end_time * len(times) / times[-1])
                        ])), 3) if len(times) > 0 else 0
                    })
                
                in_laughter = False
        
        # Handle case where laughter continues to end of audio
        if in_laughter and len(times) > 0:
            end_time = times[-1]
            duration = end_time - start_time
            if duration >= self.min_laughter_duration:
                avg_confidence = np.mean(laughter_scores_smooth[
                    int(start_time * len(times) / times[-1]):
                ]) if len(times) > 0 else 0
                
                segments.append({
                    'start_time': round(start_time, 2),
                    'end_time': round(end_time, 2),
                    'duration': round(duration, 2),
                    'confidence': round(float(avg_confidence), 3),
                    'peak_confidence': round(float(np.max(laughter_scores_smooth[
                        int(start_time * len(times) / times[-1]):
                    ])), 3) if len(times) > 0 else 0
                })
        
        return segments
    
    def _generate_timeline_data(self, features: Dict, duration: float) -> Dict:
        """Generate timeline data for laughter visualization"""
        try:
            times = features['times']
            laughter_scores = []
            
            # Calculate laughter scores for each time frame
            for i in range(len(times)):
                score = self._calculate_laughter_score(features, i)
                laughter_scores.append(score)
            
            # Smooth the scores
            try:
                from scipy.ndimage import gaussian_filter1d
                laughter_scores_smooth = gaussian_filter1d(np.array(laughter_scores), sigma=2)
            except ImportError:
                # Fallback: simple moving average
                window_size = 5
                laughter_scores_smooth = np.convolve(laughter_scores, 
                                                   np.ones(window_size)/window_size, 
                                                   mode='same')
            
            # Create timeline data points (sample every 0.1 seconds for smooth graph)
            timeline_points = []
            target_interval = 0.1  # 100ms intervals
            
            for target_time in np.arange(0, duration, target_interval):
                # Find closest time index
                closest_idx = np.argmin(np.abs(times - target_time)) if len(times) > 0 else 0
                
                if closest_idx < len(laughter_scores_smooth):
                    laughter_intensity = float(laughter_scores_smooth[closest_idx])
                else:
                    laughter_intensity = 0.0
                
                timeline_points.append({
                    'time': round(target_time, 2),
                    'laughter_intensity': round(laughter_intensity, 3)
                })
            
            return {
                'points': timeline_points,
                'max_intensity': float(np.max(laughter_scores_smooth)) if len(laughter_scores_smooth) > 0 else 0.0,
                'avg_intensity': float(np.mean(laughter_scores_smooth)) if len(laughter_scores_smooth) > 0 else 0.0,
                'sample_interval': target_interval
            }
            
        except Exception as e:
            print(f"❌ Error generating timeline data: {e}")
            return {
                'points': [],
                'max_intensity': 0.0,
                'avg_intensity': 0.0,
                'sample_interval': 0.1
            }
    
    def _calculate_laughter_score(self, features: Dict, frame_idx: int) -> float:
        """Calculate laughter likelihood score for a specific time frame"""
        try:
            score_components = []
            
            # 1. High energy bursts (laughter is typically energetic)
            rms = features['rms_energy'][frame_idx]
            energy_score = min(rms * 10, 1.0)  # Normalize to 0-1
            score_components.append(energy_score * 0.25)
            
            # 2. Spectral characteristics
            centroid = features['spectral_centroids'][frame_idx]
            bandwidth = features['spectral_bandwidth'][frame_idx]
            
            # Laughter typically has higher spectral centroid and bandwidth
            centroid_score = min(centroid / 3000, 1.0)  # Normalize
            bandwidth_score = min(bandwidth / 2000, 1.0)  # Normalize
            score_components.append(centroid_score * 0.2)
            score_components.append(bandwidth_score * 0.15)
            
            # 3. Zero crossing rate (laughter has different patterns than speech)
            zcr = features['zero_crossing_rate'][frame_idx]
            zcr_score = min(zcr * 50, 1.0)  # Normalize
            score_components.append(zcr_score * 0.15)
            
            # 4. MFCC patterns (laughter has distinctive cepstral characteristics)
            if frame_idx < features['mfccs'].shape[1]:
                mfcc_variance = np.var(features['mfccs'][:, frame_idx])
                mfcc_score = min(mfcc_variance / 100, 1.0)  # Normalize
                score_components.append(mfcc_score * 0.15)
            
            # 5. Spectral contrast (laughter vs speech distinction)
            if frame_idx < features['spectral_contrast'].shape[1]:
                contrast_mean = np.mean(features['spectral_contrast'][:, frame_idx])
                contrast_score = min(contrast_mean / 30, 1.0)  # Normalize
                score_components.append(contrast_score * 0.1)
            
            # Combine all components
            final_score = sum(score_components)
            
            return min(max(final_score, 0.0), 1.0)  # Clamp to 0-1 range
            
        except Exception as e:
            print(f"❌ Error calculating laughter score at frame {frame_idx}: {e}")
            return 0.0
    
    def get_laughter_summary(self, laughter_data: Dict) -> str:
        """Generate a human-readable summary of laughter detection"""
        segments = laughter_data.get('laughter_segments', [])
        
        if not segments:
            return "No laughter detected in this audio."
        
        total_time = laughter_data.get('total_laughter_time', 0)
        percentage = laughter_data.get('laughter_percentage', 0)
        
        summary_parts = [
            f"😄 {len(segments)} laughter burst{'s' if len(segments) != 1 else ''} detected",
            f"⏱️ Total laughter: {total_time:.1f}s ({percentage:.1f}% of audio)"
        ]
        
        if segments:
            # Add details about each segment
            for i, segment in enumerate(segments[:3]):  # Show first 3 segments
                summary_parts.append(
                    f"   • Burst {i+1}: {segment['start_time']}s-{segment['end_time']}s "
                    f"({segment['confidence']:.0%} confidence)"
                )
            
            if len(segments) > 3:
                summary_parts.append(f"   • ...and {len(segments) - 3} more")
        
        return "\n".join(summary_parts)


# Global laughter detector instance
laughter_detector = LaughterDetector()

def detect_laughter_in_audio(audio_file_path: str) -> Dict:
    """Detect laughter in an audio file"""
    return laughter_detector.detect_laughter(audio_file_path)

def get_laughter_summary(laughter_data: Dict) -> str:
    """Get human-readable laughter summary"""
    return laughter_detector.get_laughter_summary(laughter_data)


if __name__ == "__main__":
    # Test the laughter detector
    import sys
    
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        print(f"🎵 Testing laughter detection on: {audio_file}")
        
        result = detect_laughter_in_audio(audio_file)
        print(f"📊 Results: {json.dumps(result, indent=2)}")
        print(f"📝 Summary: {get_laughter_summary(result)}")
    else:
        print("Usage: python3 laughter_detector.py <audio_file>")
