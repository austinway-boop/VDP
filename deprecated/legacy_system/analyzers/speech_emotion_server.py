#!/usr/bin/env python3
"""
Speech Emotion Analysis Web Server
Provides REST API for speech-to-emotion analysis
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
import tempfile
import base64
from pathlib import Path
from speech_emotion_analyzer import SpeechEmotionAnalyzer
from batch_word_processor import batch_processor

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the speech emotion analyzer
analyzer = SpeechEmotionAnalyzer()

@app.route('/')
def index():
    """Serve the main interface"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Speech Emotion Analyzer</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }
        
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5em;
            font-weight: 300;
        }
        
        .controls {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        
        button {
            padding: 12px 24px;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        
        .record-btn {
            background: linear-gradient(45deg, #ff6b6b, #ee5a52);
            color: white;
        }
        
        .record-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 107, 107, 0.3);
        }
        
        .record-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .upload-btn {
            background: linear-gradient(45deg, #4ecdc4, #44a08d);
            color: white;
        }
        
        .upload-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(78, 205, 196, 0.3);
        }
        
        .analyze-btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
        }
        
        .analyze-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
        }
        
        .analyze-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .status {
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            border-radius: 10px;
            font-weight: 500;
        }
        
        .status.recording {
            background: rgba(255, 107, 107, 0.1);
            color: #d63031;
            border: 2px solid rgba(255, 107, 107, 0.3);
        }
        
        .status.analyzing {
            background: rgba(102, 126, 234, 0.1);
            color: #667eea;
            border: 2px solid rgba(102, 126, 234, 0.3);
        }
        
        .status.success {
            background: rgba(78, 205, 196, 0.1);
            color: #00b894;
            border: 2px solid rgba(78, 205, 196, 0.3);
        }
        
        .status.error {
            background: rgba(255, 107, 107, 0.1);
            color: #d63031;
            border: 2px solid rgba(255, 107, 107, 0.3);
        }
        
        .results {
            margin-top: 30px;
        }
        
        .transcription {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }
        
        .emotion-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
            border: 1px solid #e9ecef;
        }
        
        .emotion-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .emotion-icon {
            font-size: 2em;
            margin-right: 15px;
        }
        
        .emotion-title {
            font-size: 1.5em;
            font-weight: 600;
            color: #333;
        }
        
        .emotion-confidence {
            margin-left: auto;
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .metric {
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        
        .metric-label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }
        
        .metric-value {
            font-size: 1.5em;
            font-weight: 600;
            color: #333;
        }
        
        .emotion-bars {
            margin-top: 20px;
        }
        
        .emotion-bar {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .emotion-label {
            width: 100px;
            font-size: 0.9em;
            color: #666;
            text-transform: capitalize;
        }
        
        .emotion-bar-bg {
            flex: 1;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            margin: 0 10px;
            overflow: hidden;
        }
        
        .emotion-bar-fill {
            height: 100%;
            border-radius: 10px;
            transition: width 0.5s ease;
        }
        
        .emotion-percentage {
            width: 50px;
            text-align: right;
            font-size: 0.9em;
            color: #666;
        }
        
        input[type="file"] {
            display: none;
        }
        
        .hidden {
            display: none;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .recording .record-btn {
            animation: pulse 1s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎤 Speech Emotion Analyzer</h1>
        
        <div class="controls">
            <button id="recordBtn" class="record-btn">🎙️ Record 10s</button>
            <button id="uploadBtn" class="upload-btn">📁 Upload Audio</button>
            <button id="analyzeBtn" class="analyze-btn hidden" disabled>🔍 Analyze Emotion</button>
            <input type="file" id="fileInput" accept="audio/*">
        </div>
        
        <div id="status" class="status hidden"></div>
        <div id="countdown" class="status hidden"></div>
        
        <div id="results" class="results hidden">
            <div class="transcription">
                <h3>📝 Transcription</h3>
                <p id="transcriptionText"></p>
            </div>
            
            <div class="emotion-card">
                <div class="emotion-header">
                    <span id="emotionIcon" class="emotion-icon">😊</span>
                    <span id="emotionTitle" class="emotion-title">Joy</span>
                    <span id="emotionConfidence" class="emotion-confidence">85%</span>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric">
                        <div class="metric-label">Valence</div>
                        <div id="valenceValue" class="metric-value">0.75</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Arousal</div>
                        <div id="arousalValue" class="metric-value">0.65</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Dominance</div>
                        <div id="dominanceValue" class="metric-value">0.80</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Sentiment</div>
                        <div id="sentimentValue" class="metric-value">Positive</div>
                    </div>
                </div>
                
                <div class="emotion-bars" id="emotionBars">
                    <!-- Emotion bars will be populated by JavaScript -->
                </div>
            </div>
        </div>
    </div>
    
    <script>
        class SpeechEmotionApp {
            constructor() {
                this.mediaRecorder = null;
                this.audioChunks = [];
                this.currentAudio = null;
                this.isRecording = false;
                
                this.initializeElements();
                this.attachEventListeners();
                
                this.emotionIcons = {
                    'joy': '😊',
                    'trust': '🤝',
                    'anticipation': '🤔',
                    'surprise': '😮',
                    'anger': '😠',
                    'fear': '😰',
                    'sadness': '😢',
                    'disgust': '🤢',
                    'neutral': '😐'
                };
                
                this.emotionColors = {
                    'joy': '#f1c40f',
                    'trust': '#3498db',
                    'anticipation': '#e67e22',
                    'surprise': '#9b59b6',
                    'anger': '#e74c3c',
                    'fear': '#34495e',
                    'sadness': '#2c3e50',
                    'disgust': '#27ae60'
                };
            }
            
            initializeElements() {
                this.elements = {
                    recordBtn: document.getElementById('recordBtn'),
                    uploadBtn: document.getElementById('uploadBtn'),
                    analyzeBtn: document.getElementById('analyzeBtn'),
                    fileInput: document.getElementById('fileInput'),
                    status: document.getElementById('status'),
                    countdown: document.getElementById('countdown'),
                    results: document.getElementById('results'),
                    transcriptionText: document.getElementById('transcriptionText'),
                    emotionIcon: document.getElementById('emotionIcon'),
                    emotionTitle: document.getElementById('emotionTitle'),
                    emotionConfidence: document.getElementById('emotionConfidence'),
                    valenceValue: document.getElementById('valenceValue'),
                    arousalValue: document.getElementById('arousalValue'),
                    dominanceValue: document.getElementById('dominanceValue'),
                    sentimentValue: document.getElementById('sentimentValue'),
                    emotionBars: document.getElementById('emotionBars')
                };
            }
            
            attachEventListeners() {
                this.elements.recordBtn.addEventListener('click', () => this.toggleRecording());
                this.elements.uploadBtn.addEventListener('click', () => this.elements.fileInput.click());
                this.elements.analyzeBtn.addEventListener('click', () => this.analyzeAudio());
                this.elements.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
            }
            
            async toggleRecording() {
                if (this.isRecording) {
                    this.stopRecording();
                } else {
                    await this.startRecording();
                }
            }
            
            async startRecording() {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    this.mediaRecorder = new MediaRecorder(stream);
                    this.audioChunks = [];
                    
                    this.mediaRecorder.ondataavailable = (event) => {
                        this.audioChunks.push(event.data);
                    };
                    
                    this.mediaRecorder.onstop = () => {
                        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                        this.currentAudio = audioBlob;
                        this.showAnalyzeButton();
                        this.hideStatus();
                    };
                    
                    this.mediaRecorder.start();
                    this.isRecording = true;
                    
                    this.elements.recordBtn.textContent = '⏹️ Stop Recording';
                    this.elements.recordBtn.classList.add('recording');
                    this.showStatus('🎙️ Recording... Speak now!', 'recording');
                    
                    // 10-second countdown
                    let timeLeft = 10;
                    this.elements.countdown.textContent = `⏱️ ${timeLeft}s remaining`;
                    this.elements.countdown.classList.remove('hidden');
                    
                    const countdownInterval = setInterval(() => {
                        timeLeft--;
                        this.elements.countdown.textContent = `⏱️ ${timeLeft}s remaining`;
                        
                        if (timeLeft <= 0) {
                            clearInterval(countdownInterval);
                            if (this.isRecording) {
                                this.stopRecording();
                            }
                        }
                    }, 1000);
                    
                    // Auto-stop after 10 seconds
                    setTimeout(() => {
                        if (this.isRecording) {
                            this.stopRecording();
                        }
                    }, 10000);
                    
                } catch (error) {
                    this.showStatus('❌ Error accessing microphone: ' + error.message, 'error');
                }
            }
            
            stopRecording() {
                if (this.mediaRecorder && this.isRecording) {
                    this.mediaRecorder.stop();
                    this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
                    this.isRecording = false;
                    
                    this.elements.recordBtn.textContent = '🎙️ Record 10s';
                    this.elements.recordBtn.classList.remove('recording');
                    this.elements.countdown.classList.add('hidden');
                    
                    this.showStatus('✅ Recording complete! Click "Analyze Emotion" to process.', 'success');
                }
            }
            
            handleFileUpload(event) {
                const file = event.target.files[0];
                if (file) {
                    this.currentAudio = file;
                    this.showAnalyzeButton();
                    this.showStatus(`📁 File uploaded: ${file.name}`, 'success');
                }
            }
            
            showAnalyzeButton() {
                this.elements.analyzeBtn.classList.remove('hidden');
                this.elements.analyzeBtn.disabled = false;
            }
            
            async analyzeAudio() {
                if (!this.currentAudio) {
                    this.showStatus('❌ No audio to analyze', 'error');
                    return;
                }
                
                this.showStatus('🔍 Analyzing speech and emotions...', 'analyzing');
                this.elements.analyzeBtn.disabled = true;
                this.hideResults();
                
                try {
                    const formData = new FormData();
                    formData.append('audio', this.currentAudio);
                    
                    const response = await fetch('/api/analyze', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        this.displayResults(result);
                        this.showStatus('✅ Analysis complete!', 'success');
                    } else {
                        this.showStatus(`❌ Analysis failed: ${result.error}`, 'error');
                    }
                    
                } catch (error) {
                    this.showStatus(`❌ Error during analysis: ${error.message}`, 'error');
                }
                
                this.elements.analyzeBtn.disabled = false;
            }
            
            displayResults(result) {
                const analysis = result.emotion_analysis;
                
                // Transcription
                this.elements.transcriptionText.textContent = result.transcription || 'No speech detected';
                
                // Main emotion
                const mainEmotion = analysis.overall_emotion;
                this.elements.emotionIcon.textContent = this.emotionIcons[mainEmotion] || '😐';
                this.elements.emotionTitle.textContent = mainEmotion.charAt(0).toUpperCase() + mainEmotion.slice(1);
                this.elements.emotionConfidence.textContent = Math.round(analysis.confidence * 100) + '%';
                
                // VAD values
                this.elements.valenceValue.textContent = analysis.vad.valence.toFixed(2);
                this.elements.arousalValue.textContent = analysis.vad.arousal.toFixed(2);
                this.elements.dominanceValue.textContent = analysis.vad.dominance.toFixed(2);
                
                // Sentiment
                this.elements.sentimentValue.textContent = analysis.sentiment.polarity.charAt(0).toUpperCase() + 
                    analysis.sentiment.polarity.slice(1);
                
                // Emotion bars
                this.createEmotionBars(analysis.emotions);
                
                this.showResults();
            }
            
            createEmotionBars(emotions) {
                this.elements.emotionBars.innerHTML = '';
                
                // Sort emotions by probability
                const sortedEmotions = Object.entries(emotions).sort((a, b) => b[1] - a[1]);
                
                sortedEmotions.forEach(([emotion, probability]) => {
                    const barContainer = document.createElement('div');
                    barContainer.className = 'emotion-bar';
                    
                    const label = document.createElement('div');
                    label.className = 'emotion-label';
                    label.textContent = emotion;
                    
                    const barBg = document.createElement('div');
                    barBg.className = 'emotion-bar-bg';
                    
                    const barFill = document.createElement('div');
                    barFill.className = 'emotion-bar-fill';
                    barFill.style.width = (probability * 100) + '%';
                    barFill.style.backgroundColor = this.emotionColors[emotion] || '#ccc';
                    
                    const percentage = document.createElement('div');
                    percentage.className = 'emotion-percentage';
                    percentage.textContent = Math.round(probability * 100) + '%';
                    
                    barBg.appendChild(barFill);
                    barContainer.appendChild(label);
                    barContainer.appendChild(barBg);
                    barContainer.appendChild(percentage);
                    
                    this.elements.emotionBars.appendChild(barContainer);
                });
            }
            
            showStatus(message, type) {
                this.elements.status.textContent = message;
                this.elements.status.className = `status ${type}`;
                this.elements.status.classList.remove('hidden');
            }
            
            hideStatus() {
                this.elements.status.classList.add('hidden');
            }
            
            showResults() {
                this.elements.results.classList.remove('hidden');
            }
            
            hideResults() {
                this.elements.results.classList.add('hidden');
            }
        }
        
        // Initialize the app when the page loads
        document.addEventListener('DOMContentLoaded', () => {
            new SpeechEmotionApp();
        });
    </script>
</body>
</html>
    ''')

@app.route('/api/analyze', methods=['POST'])
def analyze_speech():
    """Analyze uploaded audio for speech emotion"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            # Analyze the audio
            result = analyzer.analyze_audio_file(temp_path)
            return jsonify(result)
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze_text', methods=['POST'])
def analyze_text():
    """Analyze text directly for emotion (for testing)"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Analyze the text
        emotion_analysis = analyzer.analyze_phrase_emotion(text)
        
        result = {
            "transcription": text,
            "emotion_analysis": emotion_analysis,
            "processing_time": 0,
            "success": True,
            "error": None
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get system statistics"""
    cache_stats = batch_processor.get_cache_stats()
    return jsonify({
        'word_database_size': cache_stats['cached_words'],
        'processing_queue_size': cache_stats.get('processing_queue', 0),
        'supported_emotions': analyzer.emotions,
        'system_ready': True,
        'mode': 'batch_processing'
    })

if __name__ == '__main__':
    print("🚀 Starting Speech Emotion Analysis Server...")
    print(f"📊 Loaded emotion data for {len(analyzer.word_cache)} words")
    print("🌐 Server will be available at: http://localhost:5001")
    print("🎤 Features:")
    print("   • Record 10-second audio clips")
    print("   • Upload audio files") 
    print("   • Speech-to-text transcription")
    print("   • Word-level emotion analysis")
    print("   • Phrase-level emotion aggregation")
    print("   • VAD (Valence-Arousal-Dominance) scoring")
    print("   • Sentiment analysis")
    
    app.run(host='0.0.0.0', port=5001, debug=True)

