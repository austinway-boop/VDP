#!/usr/bin/env python3
"""
Admin Panel Server for Speech Recognition Training
Web interface for reviewing and correcting uncertain transcriptions
"""

from flask import Flask, render_template, request, jsonify, send_file, abort
from flask_cors import CORS
import json
import os
import time
from pathlib import Path
from enhanced_speech_analyzer import EnhancedSpeechAnalyzer
import mimetypes

app = Flask(__name__)
CORS(app)

# Initialize the analyzer
analyzer = EnhancedSpeechAnalyzer()

@app.route('/')
def admin_dashboard():
    """Main admin dashboard"""
    return render_template('admin_dashboard.html')

@app.route('/api/stats')
def get_stats():
    """Get training statistics"""
    try:
        stats = analyzer.get_training_stats()
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/pending-reviews')
def get_pending_reviews():
    """Get all clips pending review"""
    try:
        pending_clips = analyzer.get_pending_reviews()
        return jsonify({
            "success": True,
            "clips": pending_clips
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/audio/<clip_id>')
def get_audio(clip_id):
    """Serve audio file for a specific clip"""
    try:
        # Find the audio file for this clip
        for ext in ['.wav', '.flac', '.aiff', '.mp3']:
            audio_file = analyzer.uncertain_dir / f"{clip_id}{ext}"
            if audio_file.exists():
                # Determine MIME type
                mime_type, _ = mimetypes.guess_type(str(audio_file))
                if mime_type is None:
                    mime_type = 'audio/wav'  # Default
                
                return send_file(
                    str(audio_file),
                    mimetype=mime_type,
                    as_attachment=False
                )
        
        # If no audio file found, return 404
        abort(404)
        
    except Exception as e:
        print(f"Error serving audio for clip {clip_id}: {e}")
        abort(500)

@app.route('/api/submit-correction', methods=['POST'])
def submit_correction():
    """Submit a correction for a clip"""
    try:
        data = request.json
        clip_id = data.get('clip_id')
        corrected_text = data.get('corrected_text', '').strip()
        user_id = data.get('user_id', 'admin')
        
        if not clip_id or not corrected_text:
            return jsonify({
                "success": False,
                "error": "Missing clip_id or corrected_text"
            }), 400
        
        # Submit the correction
        success = analyzer.submit_correction(clip_id, corrected_text, user_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Correction submitted successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to submit correction"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/skip-clip', methods=['POST'])
def skip_clip():
    """Skip a clip (mark as reviewed without correction)"""
    try:
        data = request.json
        clip_id = data.get('clip_id')
        
        if not clip_id:
            return jsonify({
                "success": False,
                "error": "Missing clip_id"
            }), 400
        
        # Mark as skipped (move to reviewed without correction)
        metadata_file = analyzer.uncertain_dir / f"{clip_id}_metadata.json"
        
        if not metadata_file.exists():
            return jsonify({
                "success": False,
                "error": "Clip not found"
            }), 404
        
        # Load and update metadata
        with open(metadata_file, 'r', encoding='utf-8') as f:
            clip_data = json.load(f)
        
        clip_data['status'] = 'skipped'
        clip_data['skipped_by'] = 'admin'
        clip_data['skip_timestamp'] = int(time.time())
        
        # Save updated metadata
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(clip_data, f, indent=2, ensure_ascii=False)
        
        # Move to reviewed directory
        analyzer.move_to_reviewed(clip_id)
        
        return jsonify({
            "success": True,
            "message": "Clip skipped successfully"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/corrections-history')
def get_corrections_history():
    """Get history of corrections"""
    try:
        corrections = analyzer.corrections.get('corrections', [])
        # Sort by timestamp (newest first)
        corrections.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        return jsonify({
            "success": True,
            "corrections": corrections
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/vocabulary-improvements')
def get_vocabulary_improvements():
    """Get vocabulary improvements statistics"""
    try:
        improvements = analyzer.corrections.get('vocabulary_improvements', {})
        
        # Convert to list of tuples and sort by frequency
        improvements_list = [
            {"word": word, "frequency": freq}
            for word, freq in improvements.items()
        ]
        improvements_list.sort(key=lambda x: x['frequency'], reverse=True)
        
        return jsonify({
            "success": True,
            "improvements": improvements_list
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/update-confidence-threshold', methods=['POST'])
def update_confidence_threshold():
    """Update the confidence threshold"""
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

@app.route('/api/pending-word-reviews')
def get_pending_word_reviews():
    """Get all word snippets pending review"""
    try:
        pending_words = analyzer.get_pending_word_reviews()
        return jsonify({
            "success": True,
            "words": pending_words
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/word-audio/<word_id>')
def get_word_audio(word_id):
    """Serve audio file for a specific word"""
    try:
        # Find the audio file for this word
        for ext in ['.wav', '.flac', '.aiff', '.mp3', '.webm']:
            audio_file = analyzer.uncertain_words_dir / f"{word_id}{ext}"
            if audio_file.exists():
                # Determine MIME type
                mime_type, _ = mimetypes.guess_type(str(audio_file))
                if mime_type is None:
                    mime_type = 'audio/wav'  # Default
                
                return send_file(
                    str(audio_file),
                    mimetype=mime_type,
                    as_attachment=False
                )
        
        # If no audio file found, return 404
        abort(404)
        
    except Exception as e:
        print(f"Error serving word audio for {word_id}: {e}")
        abort(500)

@app.route('/api/submit-word-correction', methods=['POST'])
def submit_word_correction():
    """Submit a correction for a word"""
    try:
        data = request.json
        word_id = data.get('word_id')
        corrected_word = data.get('corrected_word', '').strip()
        user_id = data.get('user_id', 'admin')
        
        if not word_id or not corrected_word:
            return jsonify({
                "success": False,
                "error": "Missing word_id or corrected_word"
            }), 400
        
        # Submit the word correction
        success = analyzer.submit_word_correction(word_id, corrected_word, None, user_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Word correction submitted successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to submit word correction"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/skip-word', methods=['POST'])
def skip_word():
    """Skip a word (mark as reviewed without correction)"""
    try:
        data = request.json
        word_id = data.get('word_id')
        
        if not word_id:
            return jsonify({
                "success": False,
                "error": "Missing word_id"
            }), 400
        
        # Mark as skipped (move to reviewed without correction)
        metadata_file = analyzer.uncertain_words_dir / f"{word_id}_metadata.json"
        
        if not metadata_file.exists():
            return jsonify({
                "success": False,
                "error": "Word not found"
            }), 404
        
        # Load and update metadata
        with open(metadata_file, 'r', encoding='utf-8') as f:
            word_data = json.load(f)
        
        word_data['status'] = 'word_skipped'
        word_data['skipped_by'] = 'admin'
        word_data['skip_timestamp'] = int(time.time())
        
        # Save updated metadata
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(word_data, f, indent=2, ensure_ascii=False)
        
        # Move to reviewed directory
        analyzer.move_word_to_reviewed(word_id)
        
        return jsonify({
            "success": True,
            "message": "Word skipped successfully"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/word-corrections-history')
def get_word_corrections_history():
    """Get history of word corrections"""
    try:
        word_corrections = analyzer.corrections.get('word_corrections', [])
        # Sort by timestamp (newest first)
        word_corrections.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        return jsonify({
            "success": True,
            "word_corrections": word_corrections
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/local-model-info')
def get_local_model_info():
    """Get information about the local speech recognition model"""
    try:
        model_info = analyzer.get_local_model_info()
        return jsonify({
            "success": True,
            "model_info": model_info
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/train-local-model', methods=['POST'])
def train_local_model():
    """Train the local speech recognition model"""
    try:
        success = analyzer.train_local_model()
        
        if success:
            return jsonify({
                "success": True,
                "message": "Local model training completed successfully!"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Local model training failed"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Admin Panel Server...")
    print("🌐 Admin panel will be available at: http://localhost:5002")
    print("🔧 Features:")
    print("   • Review uncertain transcriptions")
    print("   • Submit corrections")
    print("   • View training statistics")
    print("   • Monitor vocabulary improvements")
    print("   • Adjust confidence threshold")
    
    app.run(host='0.0.0.0', port=5002, debug=True)
