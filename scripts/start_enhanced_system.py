#!/usr/bin/env python3
"""
Start the Enhanced Speech Emotion Analysis System
Launches both the main server and admin panel
"""

import subprocess
import time
import sys
import os
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    try:
        import speech_recognition
        import flask
        import flask_cors
        import requests
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please install requirements with: pip install -r requirements.txt")
        return False

def start_servers():
    """Start both servers"""
    enhanced_dir = Path(__file__).parent / "enhanced_system"
    
    if not enhanced_dir.exists():
        print("❌ Enhanced system directory not found")
        return False
    
    print("🚀 Starting Enhanced Speech Emotion Analysis System...")
    
    # Start the main speech server (port 5003)
    print("📡 Starting main speech server on port 5003...")
    speech_server = subprocess.Popen([
        sys.executable, "enhanced_speech_server.py"
    ], cwd=str(enhanced_dir))
    
    # Give it a moment to start
    time.sleep(2)
    
    # Start the admin panel (port 5002)
    print("🔧 Starting admin panel on port 5002...")
    admin_server = subprocess.Popen([
        sys.executable, "admin_panel.py"
    ], cwd=str(enhanced_dir))
    
    # Give it a moment to start
    time.sleep(2)
    
    print("\n" + "="*60)
    print("🎉 ENHANCED SPEECH EMOTION ANALYSIS SYSTEM STARTED!")
    print("="*60)
    print(f"🌐 Main Interface: http://localhost:5003")
    print(f"🔧 Admin Panel: http://localhost:5002")
    print("\n🎤 Features Available:")
    print("   • Record audio directly in browser")
    print("   • Upload audio files for analysis")
    print("   • Real-time emotion detection")
    print("   • Confidence-based training system")
    print("   • Admin panel for reviewing uncertain clips")
    print("   • Advanced vocabulary learning")
    print("\n⚠️  To stop the system, press Ctrl+C")
    print("="*60)
    
    try:
        # Wait for user interrupt
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down servers...")
        speech_server.terminate()
        admin_server.terminate()
        
        # Wait for clean shutdown
        speech_server.wait()
        admin_server.wait()
        
        print("✅ System stopped successfully")

def main():
    """Main function"""
    print("🔍 Enhanced Speech Emotion Analysis System")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check if we're in the right directory
    if not Path("enhanced_system").exists():
        print("❌ Please run this script from the CircuitAlg root directory")
        sys.exit(1)
    
    # Start the system
    start_servers()

if __name__ == "__main__":
    main()
