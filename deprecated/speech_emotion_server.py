#!/usr/bin/env python3
"""
Main Speech Emotion Server with Training Capabilities
Uses the enhanced backend but serves the original UI that users prefer
"""

from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import sys
import os
from pathlib import Path

# Add enhanced_system to path for imports
sys.path.insert(0, str(Path(__file__).parent / "enhanced_system"))

from enhanced_speech_analyzer import EnhancedSpeechAnalyzer
import tempfile

app = Flask(__name__)
CORS(app)

# Initialize the enhanced analyzer with training capabilities
analyzer = EnhancedSpeechAnalyzer()

@app.route('/')
def index():
    """Serve the original interface that users prefer"""
    return send_from_directory('.', 'index.html')

@app.route('/api/analyze-audio', methods=['POST'])
def analyze_audio():
    """Analyze uploaded audio with confidence scoring and training data collection"""
    try:
        if 'audio' not in request.files:
            return jsonify({
                "success": False,
                "error": "No audio file provided"
            }), 400

        audio_file = request.files['audio']
        
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
            # Analyze with enhanced system (includes confidence scoring and training data collection)
            result = analyzer.analyze_audio_file_with_training(temp_path)
            
            # Clean up temp file
            os.unlink(temp_path)
            
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

@app.route('/api/stats')
def get_stats():
    """Get system statistics including training data"""
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

# Serve static files (CSS, JS, etc.)
@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('.', filename)

if __name__ == '__main__':
    print("🚀 Starting Speech Emotion Analysis Server with Training...")
    print(f"📊 Loaded emotion data for {len(analyzer.word_cache)} words")
    print(f"🎯 Current confidence threshold: {analyzer.confidence_threshold}")
    print("🌐 Server will be available at: http://localhost:5003")
    print("\n🎤 Features:")
    print("   • Original UI interface (as preferred)")
    print("   • Advanced confidence-based transcription scoring")
    print("   • Automatic uncertain clip detection and saving")
    print("   • Training data collection for model improvement")
    print("   • Custom vocabulary learning from corrections")
    print("   • Speech-to-text with fallback recognition")
    print("   • Word-level emotion analysis")
    print("\n🔧 Admin Panel: http://localhost:5002")
    print("   • Review uncertain transcriptions")
    print("   • Submit corrections for training")
    print("   • Monitor system performance")
    print("   • Adjust confidence threshold")
    
    app.run(host='0.0.0.0', port=5003, debug=True)