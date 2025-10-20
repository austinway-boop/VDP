#!/usr/bin/env python3
"""
Web server for Word Emotion Analyzer
Provides API endpoints to run the Python word processing script
"""

from flask import Flask, request, jsonify, send_from_directory
import subprocess
import json
import os
import threading
import time

app = Flask(__name__)

# Store the current processing state
processing_state = {
    'is_processing': False,
    'current_word': None,
    'mode': None
}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/word_analyzer')
def word_analyzer():
    return send_from_directory('.', 'word_analyzer.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/api/stats')
def get_stats():
    """Get processing statistics"""
    try:
        # Import and use the analyzer directly
        import sys
        sys.path.append('.')
        from word_emotion_analyzer import WordEmotionAnalyzer
        
        API_KEY = "your-anthropic-api-key-here"
        analyzer = WordEmotionAnalyzer(API_KEY)
        stats = analyzer.get_stats()
        
        return jsonify({
            'totalWords': stats['total_words'],
            'processedWords': stats['processed_words'],
            'remainingWords': stats['remaining_words'],
            'consecutiveErrors': stats['consecutive_errors'],
            'completionPercentage': stats['completion_percentage'],
            'currentWords': stats['current_words'],
            'pricing': stats['pricing']
        })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/run_python', methods=['POST'])
def run_python():
    """Run Python word processing command"""
    global processing_state
    
    data = request.get_json()
    command = data.get('command', 'stats')
    
    if processing_state['is_processing'] and command != 'stats':
        return jsonify({'error': 'Already processing'}), 400
    
    try:
        if command != 'stats':
            processing_state['is_processing'] = True
            processing_state['mode'] = command
        
        # Run the Python script
        result = subprocess.run([
            'python3', 'word_emotion_analyzer.py', command
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        if command != 'stats':
            processing_state['is_processing'] = False
            processing_state['current_word'] = None
        
        return result.stdout
        
    except subprocess.TimeoutExpired:
        processing_state['is_processing'] = False
        return jsonify({'error': 'Command timed out'}), 500
        
    except Exception as e:
        processing_state['is_processing'] = False
        return jsonify({'error': str(e)}), 500

@app.route('/run_python_stats')
def run_python_stats():
    """Get stats via simple endpoint"""
    try:
        result = subprocess.run([
            'python3', 'word_emotion_analyzer.py', 'stats'
        ], capture_output=True, text=True, timeout=30)
        
        return result.stdout
        
    except Exception as e:
        return f"Error: {str(e)}", 500

def parse_stats_output(output):
    """Parse statistics from Python script output"""
    stats = {
        'totalWords': 147323,  # Fixed total
        'processedWords': 0,
        'remainingWords': 147323,
        'consecutiveErrors': 0,
        'completionPercentage': 0
    }
    
    lines = output.split('\n')
    for line in lines:
        if 'Total Words:' in line:
            try:
                stats['totalWords'] = int(line.split(':')[1].strip().replace(',', ''))
            except:
                pass
        elif 'Processed:' in line:
            try:
                stats['processedWords'] = int(line.split(':')[1].strip().replace(',', ''))
            except:
                pass
        elif 'Remaining:' in line:
            try:
                stats['remainingWords'] = int(line.split(':')[1].strip().replace(',', ''))
            except:
                pass
        elif 'Consecutive Errors:' in line:
            try:
                stats['consecutiveErrors'] = int(line.split(':')[1].strip())
            except:
                pass
        elif 'Completion:' in line:
            try:
                percentage_str = line.split(':')[1].strip().replace('%', '')
                stats['completionPercentage'] = float(percentage_str)
            except:
                pass
    
    # Calculate completion percentage if not found
    if stats['totalWords'] > 0:
        stats['completionPercentage'] = (stats['processedWords'] / stats['totalWords']) * 100
    
    return stats

if __name__ == '__main__':
    print("🚀 Word Emotion Analyzer Web Server")
    print("📍 Server running at: http://localhost:5000")
    print("🧠 Ready to process words with Claude AI")
    print("⚡ Press Ctrl+C to stop the server\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
