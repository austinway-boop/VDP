#!/usr/bin/env python3
"""
Setup script for Speech Emotion Analysis System
Installs dependencies and provides system test
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a shell command with error handling"""
    print(f"\n📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_system_dependencies():
    """Install system-level dependencies for audio processing"""
    print("\n🔧 Installing system dependencies...")
    
    # Check if we're on macOS
    if sys.platform == "darwin":
        print("Detected macOS - checking for Homebrew...")
        try:
            subprocess.run("brew --version", shell=True, check=True, capture_output=True)
            print("✅ Homebrew found")
            
            # Install PortAudio for PyAudio
            if run_command("brew install portaudio", "Installing PortAudio"):
                print("✅ PortAudio installed")
            
        except subprocess.CalledProcessError:
            print("⚠️  Homebrew not found. Please install Homebrew first:")
            print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            return False
    
    elif sys.platform.startswith("linux"):
        print("Detected Linux - installing dependencies...")
        run_command("sudo apt-get update", "Updating package list")
        run_command("sudo apt-get install -y portaudio19-dev python3-pyaudio", "Installing PortAudio")
        run_command("sudo apt-get install -y flac", "Installing FLAC for speech recognition")
    
    return True

def install_python_dependencies():
    """Install Python packages"""
    print("\n📦 Installing Python dependencies...")
    
    # Upgrade pip first
    run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip")
    
    # Install packages one by one for better error handling
    packages = [
        "flask>=2.0.0",
        "flayour-api-key-here>=3.0.0", 
        "SpeechRecognition>=3.10.0",
        "pyaudio>=0.2.11",
        "numpy>=1.20.0",
        "requests>=2.25.0"
    ]
    
    for package in packages:
        if not run_command(f"{sys.executable} -m pip install {package}", f"Installing {package}"):
            print(f"⚠️  Failed to install {package}, but continuing...")
    
    return True

def test_speech_recognition():
    """Test speech recognition functionality"""
    print("\n🎤 Testing speech recognition...")
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        print("✅ Speech recognition module imported successfully")
        
        # Test microphone access
        try:
            with sr.Microphone() as source:
                print("✅ Microphone access successful")
        except Exception as e:
            print(f"⚠️  Microphone access issue: {e}")
            
        return True
    except ImportError as e:
        print(f"❌ Speech recognition import failed: {e}")
        return False

def test_word_database():
    """Test word emotion database"""
    print("\n📚 Testing word emotion database...")
    
    words_dir = Path("words")
    if not words_dir.exists():
        print("❌ Words directory not found")
        return False
    
    json_files = list(words_dir.glob("*.json"))
    if not json_files:
        print("❌ No word emotion files found")
        return False
    
    print(f"✅ Found {len(json_files)} word emotion files")
    
    # Test loading a sample file
    try:
        import json
        with open(json_files[0], 'r') as f:
            data = json.load(f)
            if 'words' in data:
                print(f"✅ Successfully loaded sample word data")
                return True
    except Exception as e:
        print(f"❌ Error loading word data: {e}")
        return False

def create_test_audio():
    """Create a simple test for the system"""
    print("\n🧪 Creating system test...")
    
    test_code = '''
# Test the speech emotion analyzer
from speech_emotion_analyzer import SpeechEmotionAnalyzer

print("Initializing Speech Emotion Analyzer...")
analyzer = SpeechEmotionAnalyzer()
print(f"✅ Loaded {len(analyzer.word_cache)} words")

# Test text analysis
test_text = "I am very happy and excited about this new project"
print(f"\\nTesting with: '{test_text}'")
result = analyzer.analyze_phrase_emotion(test_text)

print(f"Primary emotion: {result['overall_emotion']}")
print(f"Confidence: {result['confidence']:.1%}")
print(f"Sentiment: {result['sentiment']['polarity']}")
print("✅ Text analysis working!")
'''
    
    with open("test_emotion_system.py", "w") as f:
        f.write(test_code)
    
    print("✅ Created test_emotion_system.py")
    return True

def main():
    """Main setup function"""
    print("🚀 Speech Emotion Analysis System Setup")
    print("="*50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install system dependencies
    if not install_system_dependencies():
        print("⚠️  System dependency installation had issues, but continuing...")
    
    # Install Python dependencies
    if not install_python_dependencies():
        print("⚠️  Some Python packages failed to install")
    
    # Test components
    test_speech_recognition()
    test_word_database()
    create_test_audio()
    
    print("\n" + "="*50)
    print("🎉 Setup Complete!")
    print("\n📋 Next Steps:")
    print("1. Start the emotion analysis server:")
    print("   python3 speech_emotion_server.py")
    print("\n2. In another terminal, start the audio recorder server:")
    print("   python3 server.py")
    print("\n3. Open your browser to:")
    print("   http://localhost:8000 (audio recorder)")
    print("   http://localhost:5001 (emotion analysis)")
    print("\n4. Test the system:")
    print("   - Record a 10-second audio clip")
    print("   - Click 'Analyze Emotion' button")
    print("   - View the emotion analysis results")
    print("\n🧪 To test the analyzer directly:")
    print("   python3 test_emotion_system.py")
    
    return True

if __name__ == "__main__":
    main()

