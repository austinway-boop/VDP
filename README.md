# 🎤 Enhanced Speech Emotion Analysis System

A comprehensive speech-to-text and emotion analysis system with confidence-based training and word-level uncertainty detection.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Required packages: `pip install -r requirements.txt`

### Running the System

1. **Start the Enhanced System**:
   ```bash
   cd enhanced_system
   python3 enhanced_speech_server.py
   ```
   Access at: `http://localhost:5003`

2. **Start the Admin Training Panel**:
   ```bash
   cd enhanced_system  
   python3 admin_panel.py
   ```
   Access at: `http://localhost:5002`

## 📁 Project Structure

```
CircuitAlg/
├── enhanced_system/           # 🎯 Main application
│   ├── enhanced_speech_analyzer.py    # Core analysis engine
│   ├── enhanced_speech_server.py      # Main web server
│   ├── admin_panel.py                 # Training admin panel
│   ├── enhanced_interface.html        # Main UI
│   ├── batch_word_processor.py        # Word processing
│   ├── templates/                     # HTML templates
│   ├── training_data/                 # Training data storage
│   └── emotion_analysis_results/      # Analysis outputs
├── words/                     # 📚 Emotion word database
├── docs/                      # 📖 Documentation
│   ├── archive/              # Historical documentation
│   └── guides/               # User guides
├── scripts/                   # 🔧 Utility scripts
├── tests/                     # 🧪 Test files
├── deprecated/                # 📦 Legacy code
├── archive/                   # 🗄️ Archive storage
└── requirements.txt           # 📋 Dependencies
```

## ✨ Features

### 🎵 Speech Analysis
- **Real-time speech-to-text** with confidence scoring
- **Multi-service recognition** (Google Speech, Sphinx)
- **Confidence-based training** data collection
- **Audio format support** (WAV, FLAC, WebM, MP3)

### 🎭 Emotion Analysis
- **8-emotion classification** (joy, trust, anticipation, surprise, anger, fear, sadness, disgust)
- **VAD scoring** (Valence, Arousal, Dominance)
- **Word-by-word analysis** with color coding
- **Batch text processing** capability

### 🔍 Training System
- **Uncertain clip detection** and review
- **Word-level uncertainty** detection and correction
- **Admin panel** for manual corrections
- **Vocabulary learning** from corrections
- **Confidence calibration** improvement

### 🤖 Local Speech Model
- **Three-tier recognition**: Google/Sphinx → Local Model → Final Fallback
- **Trains on your corrections** for personalized accuracy
- **Audio hash matching** for 100% accuracy on corrected files
- **Feature-based recognition** using machine learning
- **Optional Vosk integration** for offline recognition
- **One-click training** from admin panel

### 📊 Advanced Features
- **Tab-based interface** for clips and words
- **Real-time statistics** and progress tracking
- **Audio playback** for review items
- **Export capabilities** for analysis results

## 🎨 User Interface

### Main Interface
- Modern blue/teal gradient design
- Upload or record audio directly
- Real-time analysis results
- Word-by-word emotion visualization
- Confidence indicators

### Admin Training Panel
- Dual-tab interface (Audio Clips / Word Reviews)
- Statistics dashboard with progress tracking
- Audio playback for uncertain items
- Correction forms with skip options
- Settings panel for confidence threshold
- **Local model training interface** with one-click training
- Real-time training statistics and recommendations

## 🔧 Configuration

### Confidence Threshold
Adjust the confidence threshold in the admin panel to control when audio gets flagged for review:
- **Lower values** (0.3-0.5): More items flagged for training
- **Higher values** (0.7-0.9): Only very uncertain items flagged

### Word Database
The system uses JSON files in the `words/` directory for emotion classification:
- Organized alphabetically (a.json, b.json, etc.)
- Each word has emotion probabilities and VAD scores
- Easily extensible with new words

## 📚 Documentation

- **System Architecture**: `docs/ENHANCED_SYSTEM_SUMMARY.md`
- **Training System**: `docs/WORD_LEVEL_TRAINING_SYSTEM.md`
- **API Documentation**: `docs/archive/`
- **Change History**: `docs/FINAL_SOLUTION.md`

## 🧪 Testing

Run tests from the `tests/` directory:
```bash
cd tests
python3 test_speech_recognition.py
python3 test_word_loading.py
```

## 🔧 Utilities

Scripts in the `scripts/` directory:
- `start_enhanced_system.py` - System startup
- `create_basic_words.py` - Word database creation
- `fix_neutral_words.py` - Database maintenance

## 🗂️ Data Storage

### Training Data
- `uncertain_clips/` - Low confidence audio clips
- `uncertain_words/` - Individual uncertain words
- `reviewed_clips/` - Manually reviewed clips
- `reviewed_words/` - Manually reviewed words
- `corrections.json` - Training corrections database

### Analysis Results
- Real-time emotion analysis outputs
- Session data and statistics
- Confidence calibration data

## 🚀 Deployment

The system is designed for local deployment with:
- **Port 5003**: Main speech analysis interface
- **Port 5002**: Admin training panel
- **File-based storage**: No external database required
- **Modular design**: Easy to extend and customize

## 🤝 Contributing

1. Make changes in the `enhanced_system/` directory
2. Test with the provided test files
3. Update documentation in `docs/`
4. Follow the existing code style and structure

## 📄 License

This project is part of a speech emotion analysis research system.

---

**Last Updated**: October 2024  
**Version**: Enhanced System v2.0
