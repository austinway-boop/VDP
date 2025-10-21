#!/usr/bin/env python3
"""
Enhanced Speech Emotion Server with Confidence-Based Training
Flask server that provides speech-to-text with confidence scoring and training data collection
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import tempfile
import time
from pathlib import Path
from enhanced_speech_analyzer import EnhancedSpeechAnalyzer

# Add ffmpeg to PATH for Whisper
current_dir = Path(__file__).parent.parent
ffmpeg_path = current_dir / "ffmpeg"
if ffmpeg_path.exists():
    os.environ['PATH'] = str(ffmpeg_path.parent) + os.pathsep + os.environ.get('PATH', '')
    print(f"🔧 Added ffmpeg to PATH for Whisper: {ffmpeg_path.parent}")

app = Flask(__name__)
CORS(app)

# Initialize the enhanced analyzer
analyzer = EnhancedSpeechAnalyzer()

@app.route('/')
def index():
    """Original interface that users prefer"""
    return send_from_directory('../deprecated', 'index.html')

@app.route('/script.js')
def serve_script():
    """Serve the deprecated script.js for backward compatibility"""
    return send_from_directory('../deprecated', 'script.js')

@app.route('/styles.css')
def serve_styles():
    """Serve the deprecated styles.css for backward compatibility"""
    return send_from_directory('../deprecated', 'styles.css')

@app.route('/api/analyze-audio', methods=['POST'])
def analyze_audio():
    """Analyze uploaded audio with confidence scoring"""
    try:
        if 'audio' not in request.files:
            return jsonify({
                "success": False,
                "error": "No audio file provided"
            }), 400

        audio_file = request.files['audio']
        retry_mode = request.form.get('retry_mode', 'normal')  # Check for retry flag
        
        if audio_file.filename == '':
            return jsonify({
                "success": False,
                "error": "No audio file selected"
            }), 400

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name

        try:
            # If this is a retry request, try aggressive transcription first
            if retry_mode == 'aggressive':
                print(f"🔄 RETRY MODE: Attempting aggressive transcription first")
                retry_text, retry_confidence, retry_metadata = analyzer.aggressive_retry_transcription(temp_path)
                if retry_text and retry_text.strip():
                    print(f"✅ AGGRESSIVE RETRY SUCCESS: '{retry_text}'")
                    # Create a successful result with the retry transcription
                    result = {
                        "transcription": retry_text,
                        "confidence": retry_confidence,
                        "metadata": retry_metadata,
                        "emotion_analysis": analyzer.analyze_phrase_emotion(retry_text),
                        "laughter_analysis": {"error": "Not analyzed in retry mode"},
                        "music_analysis": {"error": "Not analyzed in retry mode"},
                        "processing_time": 0,
                        "success": True,
                        "error": None,
                        "needs_review": retry_confidence < 0.7,
                        "unknown_words": 0,
                        "unknown_word_ids": []
                    }
                else:
                    # Aggressive retry failed, fall back to normal analysis
                    print(f"❌ AGGRESSIVE RETRY FAILED: Falling back to normal analysis")
                    result = analyzer.analyze_audio_file_with_training(temp_path)
            else:
                # Normal analysis
                result = analyzer.analyze_audio_file_with_training(temp_path)
            
            # Clean up temp file
            os.unlink(temp_path)
            
            # Check if analysis actually succeeded
            analysis_success = result.get("success", False)
            has_transcription = bool(result.get("transcription", "").strip())
            has_error = bool(result.get("error"))
            
            if not analysis_success or has_error or not has_transcription:
                # Analysis failed - return proper error response
                error_msg = result.get("error", "Speech recognition failed")
                return jsonify({
                    "success": False,
                    "error": error_msg,
                    "details": result
                }), 400
            
            return jsonify({
                "success": True,
                "result": result
            })
            
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/analyze-text', methods=['POST'])
def analyze_text():
    """Analyze text directly for emotion (for testing)"""
    try:
        data = request.json
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({
                "success": False,
                "error": "No text provided"
            }), 400
        
        # Analyze emotion only (no laughter data for text input)
        emotion_analysis = analyzer.analyze_phrase_emotion(text, None)
        
        return jsonify({
            "success": True,
            "result": {
                "transcription": text,
                "confidence": 1.0,  # Perfect confidence for direct text input
                "emotion_analysis": emotion_analysis,
                "needs_review": False,
                "success": True
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/stats')
def get_stats():
    """Get system statistics"""
    try:
        training_stats = analyzer.get_training_stats()
        word_count = len(analyzer.word_cache)
        
        stats = {
            "word_database_size": word_count,
            "training_stats": training_stats,
            "system_status": "operational"
        }
        
        return jsonify({
            "success": True,
            "stats": stats
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/pending-reviews-summary')
def get_pending_reviews_summary():
    """Get summary of pending reviews for main interface"""
    try:
        pending_clips = analyzer.get_pending_reviews()
        
        return jsonify({
            "success": True,
            "summary": {
                "count": len(pending_clips),
                "recent_clips": pending_clips[:3]  # Show 3 most recent
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/confidence-threshold')
def get_confidence_threshold():
    """Get current confidence threshold"""
    return jsonify({
        "success": True,
        "threshold": analyzer.confidence_threshold
    })

@app.route('/api/confidence-threshold', methods=['POST'])
def update_confidence_threshold():
    """Update confidence threshold"""
    try:
        data = request.json
        new_threshold = data.get('threshold')
        
        if new_threshold is None or not (0.0 <= new_threshold <= 1.0):
            return jsonify({
                "success": False,
                "error": "Threshold must be between 0.0 and 1.0"
            }), 400
        
        analyzer.confidence_threshold = new_threshold
        
        return jsonify({
            "success": True,
            "message": f"Confidence threshold updated to {new_threshold}"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Serve static files
@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from deprecated directory (original UI files)"""
    return send_from_directory('../deprecated', filename)

if __name__ == '__main__':
    print("🚀 Starting Enhanced Speech Emotion Analysis Server...")
    print(f"📊 Loaded emotion data for {len(analyzer.word_cache)} words")
    print(f"🎯 Current confidence threshold: {analyzer.confidence_threshold}")
    print("🌐 Server will be available at: http://localhost:5003")
    print("🎤 Enhanced Features:")
    print("   • Confidence-based transcription scoring")
    print("   • Automatic uncertain clip detection")
    print("   • Training data collection")
    print("   • Custom vocabulary learning")
    print("   • Speech-to-text with fallback recognition")
    print("   • Word-level emotion analysis")
    print("   • Real-time training statistics")
    print("\n🔧 Admin Panel: http://localhost:5002")
    print("   • Review uncertain transcriptions")
    print("   • Submit corrections for training")
    print("   • Monitor system performance")
    
    app.run(host='0.0.0.0', port=5003, debug=True)
