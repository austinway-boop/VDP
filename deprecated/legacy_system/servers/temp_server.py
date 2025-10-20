#!/usr/bin/env python3
"""
Enhanced Web Server for Word Emotion Processor with Real-time Updates
"""

from flask import Flask, request, jsonify, send_from_directory
import subprocess
import sys
import os
import threading
import time
import json

app = Flask(__name__)

# Global state for real-time monitoring
processing_state = {
    'is_processing': False,
    'current_mode': None,
    'start_time': None,
    'last_stats_update': 0,
    'resource_warnings': [],
    'auto_throttling': False
}

# Resource thresholds for auto-regulation
RESOURCE_THRESHOLDS = {
    'cpu_warning': 75,
    'cpu_critical': 90,
    'memory_warning': 80,
    'memory_critical': 95,
    'consecutive_errors_limit': 50
}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/processor')
def processor():
    return send_from_directory('.', 'processor.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

@app.route('/api/stats')
def get_stats():
    """Get enhanced processing statistics with real-time data"""
    try:
        sys.path.append('.')
        from word_processor import WordEmotionProcessor
        
        processor = WordEmotionProcessor()
        stats = processor.get_stats()
        
        # Add enhanced real-time data
        current_time = time.time()
        processing_state['last_stats_update'] = current_time
        
        # Check for resource warnings
        sys_perf = stats.get('system_performance', {})
        warnings = check_resource_warnings(sys_perf)
        
        # Calculate real-time processing rate
        processing_rate = calculate_processing_rate(stats)
        
        enhanced_stats = {
            'totalWords': stats['total_words'],
            'processedWords': stats['processed_words'],
            'remainingWords': stats['remaining_words'],
            'consecutiveErrors': stats['consecutive_errors'],
            'completionPercentage': stats['completion_percentage'],
            'currentWords': stats['current_words'],
            'sessionProcessed': stats['session_processed'],
            'performance': stats['performance'],
            'systemPerformance': sys_perf,
            'sessionData': stats.get('session_data', {}),
            'realTimeData': {
                'lastUpdate': current_time,
                'processingRate': processing_rate,
                'resourceWarnings': warnings,
                'autoThrottling': processing_state.get('auto_throttling', False),
                'isProcessing': processing_state.get('is_processing', False),
                'currentMode': processing_state.get('current_mode', None)
            }
        }
        
        return jsonify(enhanced_stats)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def check_resource_warnings(sys_perf):
    """Check system resources and return warnings"""
    warnings = []
    
    cpu = sys_perf.get('cpu_percent', 0)
    memory = sys_perf.get('memory_percent', 0)
    
    if cpu >= RESOURCE_THRESHOLDS['cpu_critical']:
        warnings.append({'type': 'cpu', 'level': 'critical', 'message': f'CPU usage critical: {cpu:.1f}%'})
    elif cpu >= RESOURCE_THRESHOLDS['cpu_warning']:
        warnings.append({'type': 'cpu', 'level': 'warning', 'message': f'CPU usage high: {cpu:.1f}%'})
    
    if memory >= RESOURCE_THRESHOLDS['memory_critical']:
        warnings.append({'type': 'memory', 'level': 'critical', 'message': f'Memory usage critical: {memory:.1f}%'})
    elif memory >= RESOURCE_THRESHOLDS['memory_warning']:
        warnings.append({'type': 'memory', 'level': 'warning', 'message': f'Memory usage high: {memory:.1f}%'})
    
    return warnings

def calculate_processing_rate(stats):
    """Calculate current processing rate"""
    perf = stats.get('performance', {})
    session_speed = perf.get('session_speed_wph', 0)
    avg_time = perf.get('avg_processing_time', 0)
    
    return {
        'wordsPerHour': session_speed,
        'avgTimePerWord': avg_time,
        'estimatedTimeRemaining': perf.get('estimated_completion_time', 0)
    }

@app.route('/api/deepseek-status')
def deepseek_status():
    """Check DeepSeek API status"""
    try:
        import requests
        headers = {'Authorization': 'Bearer your-api-key-here'}
        response = requests.get('https://api.deepseek.com/v1/models', headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = [model['id'] for model in data.get('data', [])]
            return f"connected - Available models: {', '.join(models)}"
        else:
            return f"error - HTTP {response.status_code}"
    except Exception as e:
        return f"offline - {str(e)}"

@app.route('/run_python', methods=['POST'])
def run_python():
    """Run word processing command with resource regulation"""
    data = request.get_json()
    command = data.get('command', 'stats')
    
    # Handle 2000 concurrent command
    if command == '2000':
        processing_state['is_processing'] = True
        processing_state['current_mode'] = '2000 concurrent'
        processing_state['start_time'] = time.time()
    
    # Update processing state
    if command != 'stats':
        processing_state['is_processing'] = True
        processing_state['current_mode'] = command
        processing_state['start_time'] = time.time()
    
    try:
        # Check system resources before starting intensive operations
        if command == 'all':
            sys.path.append('.')
            from word_processor import WordEmotionProcessor
            processor = WordEmotionProcessor()
            sys_perf = processor.get_system_performance()
            
            # Apply resource regulation
            regulated_command = apply_resource_regulation(command, sys_perf)
            if regulated_command != command:
                processing_state['auto_throttling'] = True
                command = regulated_command
        
        # NO TIMEOUT - let processing take as long as needed
        result = subprocess.run([
            'python3', 'word_processor.py', command
        ], capture_output=True, text=True, timeout=None)
        
        return result.stdout
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if command != 'stats':
            processing_state['is_processing'] = False
            processing_state['current_mode'] = None
            processing_state['auto_throttling'] = False

def apply_resource_regulation(command, sys_perf):
    """Apply intelligent resource regulation"""
    cpu = sys_perf.get('cpu_percent', 0)
    memory = sys_perf.get('memory_percent', 0)
    
    # If system resources are stressed, convert 'all' to 'batch' for better control
    if command == 'all':
        if cpu >= RESOURCE_THRESHOLDS['cpu_critical'] or memory >= RESOURCE_THRESHOLDS['memory_critical']:
            print(f"🛡️ Resource regulation: Converting 'all' to 'batch' due to high resource usage")
            print(f"   CPU: {cpu:.1f}%, Memory: {memory:.1f}%")
            return 'batch'  # More controlled processing
        elif cpu >= RESOURCE_THRESHOLDS['cpu_warning'] or memory >= RESOURCE_THRESHOLDS['memory_warning']:
            print(f"⚠️ Resource warning: High resource usage detected")
            print(f"   CPU: {cpu:.1f}%, Memory: {memory:.1f}%")
    
    return command

@app.route('/api/realtime-status')
def get_realtime_status():
    """Get real-time processing status"""
    return jsonify(processing_state)

if __name__ == '__main__':
    print("🚀 Enhanced Word Emotion Processor Server")
    print("📍 Server running at: http://localhost:5005")
    print("🤖 DeepSeek API processing with parallel execution")
    print("🛡️ Intelligent resource regulation enabled")
    print("⚡ Real-time statistics updates")
    print("🚀 20x faster with parallel processing!")
    print("Press Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=5006, debug=False)
