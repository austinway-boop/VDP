# Speech Emotion Analysis API Documentation

## Overview

The Speech Emotion Analysis API provides advanced AI-powered speech recognition and emotion analysis capabilities. It can process both audio files and text input to detect emotions, sentiment, and psychological patterns with high accuracy.

### Key Features

- **🎤 Advanced Speech Recognition**: Multi-engine transcription with Whisper, Google Speech, and fallback engines
- **🎭 Emotion Analysis**: 8-category emotion detection (joy, trust, anticipation, surprise, anger, fear, sadness, disgust)
- **😄 Laughter Detection**: Automatic detection and influence on emotion scores
- **🎵 Music Detection**: Background music identification and filtering
- **🧠 Confidence Scoring**: Advanced confidence estimation for transcription quality
- **📊 Detailed Analytics**: Word-level analysis, sentiment scoring, and psychological dimensions
- **🔄 Retry Mechanisms**: Aggressive retry modes for difficult audio
- **⚡ Fast Processing**: Optimized for real-time applications

## Base URL

**🌐 Live API**: [https://vdp-peach.vercel.app](https://vdp-peach.vercel.app)

```
https://vdp-peach.vercel.app
```

**Test it now**: `curl https://vdp-peach.vercel.app/api/stats`

## Authentication

Currently, the API is open and does not require authentication. Rate limiting may apply based on your Vercel plan.

## Endpoints

### 1. Audio Analysis

**Endpoint:** `POST /api/analyze-audio`

Analyzes uploaded audio files for speech recognition and emotion detection.

#### Request Format

**Content-Type:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `audio` | File | Yes | Audio file (WAV, MP3, FLAC, WebM, AIFF) |
| `retry_mode` | String | No | `"normal"` or `"aggressive"` (default: "normal") |

#### Supported Audio Formats

- **WAV** (recommended for best quality)
- **MP3** (widely supported)
- **FLAC** (lossless compression)
- **WebM** (browser recordings)
- **AIFF** (Apple format)

#### File Limits

- **Maximum file size:** 50MB
- **Minimum file size:** 50 bytes
- **Maximum duration:** ~5 minutes (depends on quality)

#### Example Request

```bash
curl -X POST https://vdp-peach.vercel.app/api/analyze-audio \
  -F "audio=@recording.wav" \
  -F "retry_mode=normal"
```

#### Response Format

```json
{
  "success": true,
  "result": {
    "transcription": "I am feeling really happy today",
    "confidence": 0.95,
    "emotion_analysis": {
      "overall_emotion": "joy",
      "confidence": 0.78,
      "emotions": {
        "joy": 0.65,
        "trust": 0.15,
        "anticipation": 0.10,
        "surprise": 0.05,
        "anger": 0.01,
        "fear": 0.01,
        "sadness": 0.02,
        "disgust": 0.01
      },
      "word_analysis": [
        {
          "word": "I",
          "clean_word": "i",
          "emotion": "neutral",
          "confidence": 0.125,
          "valence": 0.5,
          "arousal": 0.5,
          "sentiment": "neutral",
          "found": true
        },
        {
          "word": "feeling",
          "clean_word": "feeling",
          "emotion": "anticipation",
          "confidence": 0.35,
          "valence": 0.6,
          "arousal": 0.4,
          "sentiment": "neutral",
          "found": true
        },
        {
          "word": "happy",
          "clean_word": "happy",
          "emotion": "joy",
          "confidence": 0.85,
          "valence": 0.9,
          "arousal": 0.7,
          "sentiment": "positive",
          "found": true
        }
      ],
      "vad": {
        "valence": 0.75,
        "arousal": 0.65,
        "dominance": 0.6
      },
      "sentiment": {
        "polarity": "positive",
        "strength": 0.8
      },
      "word_count": 6,
      "analyzed_words": 5,
      "coverage": 0.83
    },
    "laughter_analysis": {
      "laughter_segments": [],
      "laughter_percentage": 0.0,
      "total_laughter_duration": 0.0
    },
    "music_analysis": {
      "music_segments": [],
      "music_percentage": 0.0
    },
    "processing_time": 2.34,
    "api_processing_time": 2.87,
    "success": true,
    "error": null,
    "needs_review": false,
    "file_info": {
      "size": 156789,
      "name": "recording.wav",
      "type": "audio/wav"
    }
  }
}
```

#### Error Response

```json
{
  "success": false,
  "error": "Speech recognition failed. Please try speaking louder or in a quieter environment.",
  "details": {
    "confidence": 0.12,
    "processing_time": 1.23,
    "file_info": {
      "size": 1234,
      "name": "quiet_recording.wav"
    }
  }
}
```

### 2. Text Analysis

**Endpoint:** `POST /api/analyze-text`

Analyzes text directly for emotion detection and sentiment analysis.

#### Request Format

**Content-Type:** `application/json`

```json
{
  "text": "I am feeling really excited about this new project!"
}
```

#### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | String | Yes | Text to analyze (max 10,000 characters) |

#### Example Request

```bash
curl -X POST https://vdp-peach.vercel.app/api/analyze-text \
  -H "Content-Type: application/json" \
  -d '{"text": "I am feeling really excited about this new project!"}'
```

#### Response Format

```json
{
  "success": true,
  "result": {
    "transcription": "I am feeling really excited about this new project!",
    "confidence": 1.0,
    "emotion_analysis": {
      "overall_emotion": "anticipation",
      "confidence": 0.72,
      "emotions": {
        "anticipation": 0.45,
        "joy": 0.35,
        "trust": 0.10,
        "surprise": 0.05,
        "anger": 0.01,
        "fear": 0.01,
        "sadness": 0.01,
        "disgust": 0.02
      },
      "word_analysis": [
        {
          "word": "excited",
          "emotion": "anticipation",
          "confidence": 0.78,
          "valence": 0.85,
          "arousal": 0.9,
          "sentiment": "positive"
        }
      ],
      "vad": {
        "valence": 0.8,
        "arousal": 0.75,
        "dominance": 0.7
      },
      "sentiment": {
        "polarity": "positive", 
        "strength": 0.85
      },
      "word_count": 9,
      "analyzed_words": 7,
      "coverage": 0.78
    },
    "processing_time": 0.45,
    "api_processing_time": 0.52,
    "needs_review": false,
    "success": true,
    "error": null,
    "input_stats": {
      "character_count": 49,
      "word_count": 9,
      "sentence_count": 1
    }
  }
}
```

### 3. System Statistics

**Endpoint:** `GET /api/stats`

Retrieves system statistics and capabilities information.

#### Example Request

```bash
curl https://vdp-peach.vercel.app/api/stats
```

#### Response Format

```json
{
  "success": true,
  "stats": {
    "word_database_size": 25847,
    "system_status": "operational",
    "training_stats": {
      "pending_reviews": 3,
      "completed_corrections": 127,
      "total_corrections": 130,
      "confidence_threshold": 0.7,
      "calibration_accuracy": 0.89
    },
    "batch_processor": {
      "cached_words": 25847,
      "processing_queue": 0
    },
    "features": {
      "speech_recognition": true,
      "emotion_analysis": true,
      "laughter_detection": true,
      "music_detection": true,
      "confidence_scoring": true,
      "training_data_collection": true,
      "local_speech_model": true
    },
    "capabilities": {
      "supported_audio_formats": ["WAV", "FLAC", "AIFF", "MP3", "WebM"],
      "supported_languages": ["en-US", "en-GB", "en"],
      "max_audio_size_mb": 50,
      "max_text_length": 10000,
      "confidence_threshold": 0.7
    },
    "api_info": {
      "query_time": 0.12,
      "timestamp": "2024-01-15T10:30:45.123Z",
      "version": "2.0.0"
    }
  }
}
```

## Response Data Structures

### Emotion Analysis Object

```json
{
  "overall_emotion": "joy",
  "confidence": 0.78,
  "emotions": {
    "joy": 0.65,
    "trust": 0.15,
    "anticipation": 0.10,
    "surprise": 0.05,
    "anger": 0.01,
    "fear": 0.01,
    "sadness": 0.02,
    "disgust": 0.01
  },
  "word_analysis": [...],
  "vad": {
    "valence": 0.75,
    "arousal": 0.65,
    "dominance": 0.6
  },
  "sentiment": {
    "polarity": "positive",
    "strength": 0.8
  },
  "word_count": 6,
  "analyzed_words": 5,
  "coverage": 0.83
}
```

### Word Analysis Object

```json
{
  "word": "happy",
  "clean_word": "happy",
  "emotion": "joy",
  "confidence": 0.85,
  "valence": 0.9,
  "arousal": 0.7,
  "sentiment": "positive",
  "found": true
}
```

### VAD Dimensions

- **Valence**: Emotional positivity (0.0 = very negative, 1.0 = very positive)
- **Arousal**: Emotional intensity (0.0 = very calm, 1.0 = very intense)
- **Dominance**: Emotional control (0.0 = submissive, 1.0 = dominant)

### Emotion Categories

1. **Joy**: Happiness, pleasure, contentment
2. **Trust**: Confidence, faith, reliability
3. **Anticipation**: Expectation, hope, excitement
4. **Surprise**: Amazement, astonishment, wonder
5. **Anger**: Rage, fury, irritation
6. **Fear**: Anxiety, worry, terror
7. **Sadness**: Grief, sorrow, melancholy
8. **Disgust**: Revulsion, distaste, aversion

## Error Handling

### HTTP Status Codes

- **200 OK**: Request successful
- **400 Bad Request**: Invalid input or failed analysis
- **405 Method Not Allowed**: Wrong HTTP method
- **413 Payload Too Large**: File too large
- **500 Internal Server Error**: Server error

### Common Error Messages

```json
{
  "success": false,
  "error": "No audio file provided. Please include an audio file in the 'audio' field."
}
```

```json
{
  "success": false,
  "error": "Audio file too large. Maximum size is 50MB."
}
```

```json
{
  "success": false,
  "error": "Speech recognition failed. Please try speaking louder or in a quieter environment."
}
```

## Usage Examples

### JavaScript/Node.js

```javascript
// Audio Analysis
const formData = new FormData();
formData.append('audio', audioFile);
formData.append('retry_mode', 'normal');

const response = await fetch('https://your-project.vercel.app/api/analyze-audio', {
  method: 'POST',
  body: formData
});

const result = await response.json();
if (result.success) {
  console.log('Emotion:', result.result.emotion_analysis.overall_emotion);
  console.log('Confidence:', result.result.emotion_analysis.confidence);
}

// Text Analysis
const textResponse = await fetch('https://your-project.vercel.app/api/analyze-text', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text: 'I love this amazing product!' })
});

const textResult = await textResponse.json();
```

### Python

```python
import requests

# Audio Analysis
with open('recording.wav', 'rb') as audio_file:
    files = {'audio': audio_file}
    data = {'retry_mode': 'normal'}
    
    response = requests.post(
        'https://your-project.vercel.app/api/analyze-audio',
        files=files,
        data=data
    )
    
    result = response.json()
    if result['success']:
        print(f"Emotion: {result['result']['emotion_analysis']['overall_emotion']}")

# Text Analysis
text_response = requests.post(
    'https://your-project.vercel.app/api/analyze-text',
    json={'text': 'I am so excited about this!'}
)

text_result = text_response.json()
```

### cURL

```bash
# Audio Analysis
curl -X POST https://your-project.vercel.app/api/analyze-audio \
  -F "audio=@recording.wav" \
  -F "retry_mode=aggressive"

# Text Analysis
curl -X POST https://your-project.vercel.app/api/analyze-text \
  -H "Content-Type: application/json" \
  -d '{"text": "This is absolutely fantastic!"}'

# Get Stats
curl https://your-project.vercel.app/api/stats
```

## Rate Limits & Performance

### Vercel Limits

- **Function Timeout**: 5 minutes (300 seconds)
- **Payload Size**: 50MB maximum
- **Concurrent Executions**: Based on your Vercel plan
- **Memory**: 1008MB available

### Performance Tips

1. **Audio Quality**: Use WAV or FLAC for best transcription accuracy
2. **File Size**: Smaller files process faster; compress if possible
3. **Retry Mode**: Use "aggressive" only for difficult audio
4. **Caching**: Results are not cached; consider client-side caching
5. **Batch Processing**: For multiple texts, send separate requests

## Advanced Features

### Confidence Scoring

The API provides detailed confidence scoring:
- **Transcription Confidence**: How certain the speech recognition is
- **Emotion Confidence**: How certain the emotion detection is
- **Word-level Confidence**: Individual word recognition certainty

### Laughter Detection

Automatically detects laughter in audio and influences emotion scores:
- Boosts joy and positive emotions
- Reduces negative emotions when laughter is present
- Provides laughter percentage and duration

### Music Detection

Identifies background music and filters its influence on emotion analysis:
- Detects music segments
- Can identify specific songs (when available)
- Prevents music from skewing emotion results

### Training Data Collection

The system automatically collects uncertain transcriptions for improvement:
- Low-confidence transcriptions are flagged for review
- Contributes to system accuracy over time
- No personal data is stored without consent

## Deployment Guide

### Environment Variables

Set these in your Vercel project settings:

| Variable | Required | Description |
|----------|----------|-------------|
| `DEEPSEEK_API_KEY` | Yes | DeepSeek API key for emotion analysis |
| `OPENAI_API_KEY` | No | OpenAI API key for Whisper transcription |
| `BING_KEY` | No | Microsoft Bing Speech API key |
| `IBM_USERNAME` | No | IBM Watson Speech username |
| `IBM_PASSWORD` | No | IBM Watson Speech password |

### Deployment Steps

1. **Clone Repository**
   ```bash
   git clone https://github.com/your-username/speech-emotion-api.git
   cd speech-emotion-api
   ```

2. **Install Dependencies**
   ```bash
   npm install
   ```

3. **Set Environment Variables**
   ```bash
   vercel env add DEEPSEEK_API_KEY
   # Add your DeepSeek API key when prompted
   ```

4. **Deploy to Vercel**
   ```bash
   vercel --prod
   ```

5. **Test Deployment**
   ```bash
   curl https://your-project.vercel.app/api/stats
   ```

## Troubleshooting

### Common Issues

**1. "Python script failed" errors**
- Ensure all required Python packages are installed
- Check that Python 3.9+ is available
- Verify environment variables are set correctly

**2. Audio transcription fails**
- Try using WAV format instead of MP3/WebM
- Ensure audio has clear speech (not too quiet/noisy)
- Use "aggressive" retry mode for difficult audio
- Check file size is within limits

**3. Timeout errors**
- Large audio files may timeout; compress or trim them
- Complex emotion analysis can take time; be patient
- Consider splitting long audio into smaller chunks

**4. Memory errors**
- Very large audio files may exceed memory limits
- Try reducing file size or audio quality
- Use compressed formats like MP3

### Support

For issues and questions:
1. Check the error message details in the API response
2. Review the troubleshooting section above
3. Test with different audio formats/sizes
4. Check Vercel function logs for detailed error information

## Changelog

### Version 2.0.0
- Complete rewrite for Vercel serverless deployment
- Added comprehensive emotion analysis with 8 categories
- Implemented multi-engine speech recognition
- Added laughter and music detection
- Enhanced confidence scoring system
- Improved error handling and response formats

### Version 1.x
- Legacy Flask-based system
- Basic emotion analysis
- Local deployment only

---

*Last updated: January 2024*
