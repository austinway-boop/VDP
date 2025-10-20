# 🎵 Background Music Detection & Song Identification

## Overview

The Enhanced Speech Analysis System now includes **automatic background music detection** that identifies music segments in audio clips and can identify specific songs using Chromaprint fingerprinting and AcoustID database lookup.

## 🎯 Features

### **Real-Time Music Detection**
- **Automatic Analysis**: Every audio clip is analyzed for background music
- **Precise Timing**: Shows exact start/end times of music segments
- **Confidence Scoring**: Each music segment has a confidence percentage
- **Visual Timeline Graph**: Interactive line graph showing music intensity over time

### **Song Identification**
- **Chromaprint Fingerprinting**: Generates audio fingerprints for music segments
- **AcoustID Integration**: Queries online database for song identification
- **Music Isolation**: Separates music from speech for better identification
- **Multiple Song Support**: Can identify multiple songs in one audio clip

## 🔧 Setup Instructions

### **1. Install Dependencies**
```bash
# Install Python packages
pip install pyacoustid chromaprint-python mutagen

# Install Chromaprint system library
# macOS:
brew install chromaprint

# Ubuntu/Debian:
sudo apt-get install libchromaprint-dev

# Windows:
# Download from: https://acoustid.org/chromaprint
```

### **2. Get AcoustID API Key**
1. **Register**: Go to https://acoustid.org/new-application
2. **Create Application**: Get your free API key
3. **Configure**: Set environment variable:
```bash
export ACOUSTID_API_KEY="your-acoustid-api-key-here"
```

### **3. Test Installation**
```bash
cd enhanced_system
python3 music_detector.py path/to/audio/with/music.wav
```

## 🎵 How It Works

### **Music Detection Algorithm**
1. **Harmonic-Percussive Separation**: Isolates musical content from speech
2. **Spectral Analysis**: Analyzes frequency characteristics
3. **Chroma Features**: Detects harmonic structure typical of music
4. **Temporal Analysis**: Identifies rhythmic patterns
5. **Confidence Scoring**: Combines multiple features for music likelihood

### **Song Identification Process**
1. **Music Isolation**: Enhances harmonic content, reduces speech frequencies
2. **Fingerprint Generation**: Creates Chromaprint audio fingerprint
3. **Database Query**: Searches AcoustID for matching songs
4. **Result Filtering**: Returns high-confidence matches (>80%)

### **Audio Processing Pipeline**
```
Audio Input
    ↓
Speech Recognition → Emotion Analysis → Laughter Detection
    ↓
Music Detection ← NEW!
    ↓
Song Identification (if music found)
    ↓
Combined Results with Timeline Graphs
```

## 📊 Detection Features

### **Music vs Speech Distinction**
- **Harmonic Content**: Music has more harmonic structure
- **Frequency Distribution**: Music covers broader frequency range
- **Spectral Contrast**: Music has more distinct frequency bands
- **Temporal Patterns**: Music has consistent rhythmic elements

### **Advanced Audio Analysis**
- **MFCC Features**: 13 coefficients for audio characterization
- **Chroma Variance**: Harmonic structure analysis
- **Spectral Bandwidth**: Frequency spread analysis
- **Tempo Detection**: Beat tracking for rhythmic content

## 🎨 Visual Interface

### **Music Timeline Graph** (Blue Theme)
- **Interactive line graph**: Shows music intensity over time
- **Blue color scheme**: Distinguishes from yellow laughter graph
- **Segment highlights**: Visual rectangles for detected music
- **Hover tooltips**: Precise timing and intensity information

### **Song Identification Display**
- **Green theme**: Identified songs in success-style cards
- **Song details**: Title, artist, confidence percentage
- **Timing info**: When in the audio each song appears
- **Match confidence**: AcoustID confidence scores

### **Consistent Styling**
- **Matches laughter design**: Same layout and interaction patterns
- **Word-analysis theme**: Chip-style segment display
- **Professional graphs**: Canvas-based visualization with grid lines

## 📈 Example Output

### **Music Detection Results**
```json
{
  "music_segments": [
    {
      "start_time": 1.5,
      "end_time": 8.2,
      "duration": 6.7,
      "confidence": 0.85
    }
  ],
  "identified_songs": [
    {
      "title": "Shape of You",
      "artist": "Ed Sheeran",
      "match_confidence": 0.92,
      "segment_start": 1.5,
      "segment_end": 8.2
    }
  ],
  "music_percentage": 67.0,
  "timeline_data": {
    "points": [...],
    "max_intensity": 0.89
  }
}
```

### **UI Display**
- **Summary**: "🎵 1 music segment detected (67% of audio)"
- **Timeline Graph**: Blue line showing music intensity peaks
- **Segment Chips**: `🎵 1.5s-8.2s`
- **Song Card**: "🎼 Shape of You by Ed Sheeran (92% confidence)"

## 🔧 Configuration

### **Detection Parameters**
```python
# In music_detector.py
self.music_threshold = 0.6        # Sensitivity (lower = more sensitive)
self.min_music_duration = 2.0     # Minimum segment length
self.harmonic_threshold = 0.7     # Harmonic content threshold
```

### **AcoustID Settings**
```python
# Minimum confidence for song matches
match_threshold = 0.8  # 80% confidence required

# Maximum segments to analyze (to avoid API limits)
max_segments = 3
```

## 🎯 Use Cases

### **Content Analysis**
- **Podcast Production**: Identify background music in recordings
- **Video Editing**: Find copyrighted music automatically
- **Content Moderation**: Detect unauthorized music usage
- **Media Archiving**: Catalog music content in audio files

### **Research Applications**
- **Music Information Retrieval**: Automatic music cataloging
- **Audio Forensics**: Identify music in evidence
- **Social Media**: Detect copyrighted content
- **Broadcasting**: Monitor music usage for licensing

## 🚨 Troubleshooting

### **Common Issues**

**1. "Music detection dependencies not available"**
```bash
pip install pyacoustid chromaprint-python
brew install chromaprint  # macOS
```

**2. "AcoustID API key not configured"**
```bash
export ACOUSTID_API_KEY="your-key-here"
```

**3. "No music detected" (but music is present)**
- Lower music_threshold in music_detector.py
- Check audio quality and volume
- Ensure music is prominent enough vs speech

**4. "Song identification failed"**
- Check internet connection
- Verify AcoustID API key
- Music segment might be too short or unclear

### **Performance Tips**
1. **Clear audio**: Better music isolation and identification
2. **Prominent music**: Background music should be audible
3. **Longer segments**: 5+ second music segments identify better
4. **Popular songs**: Well-known songs have higher match rates

## 📚 API Integration

### **New Result Fields**
- `result.music_analysis` - Complete music detection data
- `result.music_analysis.music_segments` - Detected music segments
- `result.music_analysis.identified_songs` - Song identification results
- `result.music_analysis.timeline_data` - Graph visualization data

### **Environment Variables**
```bash
# Required for song identification
ACOUSTID_API_KEY=your-acoustid-api-key-here

# Optional for enhanced features  
DEEPSEEK_API_KEY=your-deepseek-api-key-here
```

## 🎉 Benefits

### **Automatic Music Cataloging**
- **No manual work**: Automatically detect and identify background music
- **Precise timing**: Know exactly when music plays
- **Professional insights**: Understand audio composition

### **Content Creation**
- **Copyright awareness**: Identify copyrighted music automatically
- **Music discovery**: Find songs you hear but don't know
- **Quality control**: Ensure appropriate music usage

### **Enhanced Analysis**
- **Complete audio understanding**: Speech + Emotions + Laughter + Music
- **Visual timelines**: See the full audio story at a glance
- **Interactive exploration**: Hover and explore any moment in the audio

---

The music detection system completes the comprehensive audio analysis suite, providing insights into every aspect of your audio content! 🎵📊
