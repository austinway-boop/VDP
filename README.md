# Speech Emotion Analysis API

> Advanced AI-powered speech recognition and emotion analysis system deployable on Vercel

## 🚀 Quick Start

Deploy this API to Vercel in minutes:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/your-username/speech-emotion-api)

## 🎯 What This API Does

Transform speech and text into detailed emotional insights:

- **🎤 Speech Recognition**: Convert audio files to text with high accuracy
- **🎭 Emotion Analysis**: Detect 8 emotion categories with confidence scores
- **😄 Laughter Detection**: Automatically detect and analyze laughter
- **🎵 Music Detection**: Identify background music and filter its influence
- **📊 Detailed Analytics**: Word-level analysis, sentiment, and psychological dimensions
- **⚡ Real-time Processing**: Optimized for fast API responses

## 📋 Table of Contents

- [Features](#features)
- [API Endpoints](#api-endpoints)
- [Quick Deploy](#quick-deploy)
- [Local Development](#local-development)
- [Environment Variables](#environment-variables)
- [Testing](#testing)
- [Documentation](#documentation)
- [Examples](#examples)
- [Support](#support)

## ✨ Features

### Core Capabilities
- **Multi-engine Speech Recognition**: Whisper, Google Speech, Bing, IBM Watson
- **8-Category Emotion Detection**: Joy, Trust, Anticipation, Surprise, Anger, Fear, Sadness, Disgust
- **Advanced Confidence Scoring**: Reliability metrics for all analyses
- **Laughter & Music Detection**: Context-aware emotion adjustment
- **Word-level Analysis**: Individual word emotion breakdown
- **VAD Scoring**: Valence, Arousal, Dominance psychological dimensions

### Technical Features
- **Serverless Architecture**: Scales automatically on Vercel
- **Multiple Audio Formats**: WAV, MP3, FLAC, WebM, AIFF support
- **Intelligent Fallbacks**: Multiple recognition engines for reliability
- **Error Handling**: Comprehensive error responses and recovery
- **CORS Support**: Ready for web applications
- **Rate Limiting**: Built-in protection and optimization

## 🔗 API Endpoints

### POST `/api/analyze-audio`
Upload audio files for speech recognition and emotion analysis.

**Input**: Audio file (multipart/form-data)
**Output**: Transcription + emotion analysis + laughter/music detection

### POST `/api/analyze-text`
Analyze text directly for emotion detection and sentiment.

**Input**: Text string (JSON)
**Output**: Detailed emotion analysis with word-level breakdown

### GET `/api/stats`
Get system statistics and capabilities.

**Output**: Database size, features, performance metrics

## 🚀 Quick Deploy

### 1. Fork & Deploy

1. Fork this repository
2. Connect to Vercel: [vercel.com/new](https://vercel.com/new)
3. Import your fork
4. Add environment variables (see below)
5. Deploy!

### 2. Environment Variables

**Required**:
```bash
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
```

**Optional** (for enhanced accuracy):
```bash
OPENAI_API_KEY=sk-your-openai-key-here
BING_KEY=your-bing-speech-key
IBM_USERNAME=apikey
IBM_PASSWORD=your-ibm-watson-password
```

### 3. Test Your Deployment

```bash
# Test the API
curl https://your-project.vercel.app/api/stats

# Analyze text
curl -X POST https://your-project.vercel.app/api/analyze-text \
  -H "Content-Type: application/json" \
  -d '{"text": "I am so excited about this!"}'
```

## 💻 Local Development

### Prerequisites

- Node.js 18+
- Python 3.9+
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/your-username/speech-emotion-api.git
cd speech-emotion-api

# Install Node.js dependencies
npm install

# Install Python dependencies
pip install -r python/requirements.txt

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your API keys

# Start development server
npm run dev
```

### Development Commands

```bash
npm run dev          # Start development server
npm test            # Run test suite
npm run build       # Build for production (not needed for Vercel)
npm run deploy      # Deploy to Vercel
```

## 🔧 Environment Variables

### Required Variables

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `DEEPSEEK_API_KEY` | Powers emotion analysis | [DeepSeek API](https://platform.deepseek.com/) |

### Optional Variables

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `OPENAI_API_KEY` | Enhanced speech recognition | [OpenAI API](https://platform.openai.com/api-keys) |
| `BING_KEY` | Microsoft speech recognition | [Azure Cognitive Services](https://azure.microsoft.com/services/cognitive-services/speech-services/) |
| `IBM_USERNAME` | IBM Watson speech recognition | [IBM Watson](https://www.ibm.com/cloud/watson-speech-to-text) |
| `IBM_PASSWORD` | IBM Watson speech recognition | [IBM Watson](https://www.ibm.com/cloud/watson-speech-to-text) |

**📖 Detailed setup guide**: [ENVIRONMENT_VARIABLES.md](./ENVIRONMENT_VARIABLES.md)

## 🧪 Testing

### Automated Tests

```bash
# Node.js test suite
npm test

# Python test suite
python test/test-audio.py

# Test against deployed API
TEST_BASE_URL=https://your-project.vercel.app npm test
```

### Manual Testing

```bash
# Test stats endpoint
curl https://your-project.vercel.app/api/stats

# Test text analysis
curl -X POST https://your-project.vercel.app/api/analyze-text \
  -H "Content-Type: application/json" \
  -d '{"text": "I love this amazing product!"}'

# Test audio analysis
curl -X POST https://your-project.vercel.app/api/analyze-audio \
  -F "audio=@recording.wav"
```

## 📚 Documentation

- **[API Documentation](./API_DOCUMENTATION.md)**: Complete API reference with examples
- **[Environment Variables](./ENVIRONMENT_VARIABLES.md)**: Detailed setup guide
- **[Test Suite Documentation](./test/)**: Testing tools and examples

## 💡 Examples

### JavaScript/Node.js

```javascript
// Text analysis
const response = await fetch('https://your-project.vercel.app/api/analyze-text', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text: 'I am extremely happy today!' })
});

const result = await response.json();
console.log('Primary emotion:', result.result.emotion_analysis.overall_emotion);
console.log('Confidence:', result.result.emotion_analysis.confidence);

// Audio analysis
const formData = new FormData();
formData.append('audio', audioFile);

const audioResponse = await fetch('https://your-project.vercel.app/api/analyze-audio', {
  method: 'POST',
  body: formData
});

const audioResult = await audioResponse.json();
console.log('Transcription:', audioResult.result.transcription);
console.log('Emotion:', audioResult.result.emotion_analysis.overall_emotion);
```

### Python

```python
import requests

# Text analysis
response = requests.post(
    'https://your-project.vercel.app/api/analyze-text',
    json={'text': 'I feel amazing about this project!'}
)

result = response.json()
print(f"Emotion: {result['result']['emotion_analysis']['overall_emotion']}")
print(f"Confidence: {result['result']['emotion_analysis']['confidence']:.2%}")

# Audio analysis
with open('recording.wav', 'rb') as audio_file:
    files = {'audio': audio_file}
    response = requests.post(
        'https://your-project.vercel.app/api/analyze-audio',
        files=files
    )

result = response.json()
print(f"Transcription: {result['result']['transcription']}")
```

### cURL

```bash
# Analyze text
curl -X POST https://your-project.vercel.app/api/analyze-text \
  -H "Content-Type: application/json" \
  -d '{"text": "This is absolutely wonderful news!"}'

# Analyze audio
curl -X POST https://your-project.vercel.app/api/analyze-audio \
  -F "audio=@recording.wav" \
  -F "retry_mode=normal"
```

## 🎮 Use Cases

### Content Analysis
- **Social Media Monitoring**: Analyze user sentiment in posts and comments
- **Customer Feedback**: Process support tickets and reviews for emotion insights
- **Market Research**: Understand emotional responses to products and campaigns

### Voice Applications
- **Call Center Analytics**: Monitor customer satisfaction in real-time
- **Voice Assistants**: Adapt responses based on user emotional state
- **Mental Health Apps**: Track emotional patterns in speech

### Gaming & Entertainment
- **Player Emotion Tracking**: Adapt game difficulty based on emotional state
- **Content Recommendation**: Suggest content based on current mood
- **Interactive Experiences**: Create emotion-responsive applications

## 🔒 Privacy & Security

- **No Data Storage**: Audio and text are processed in real-time and not stored
- **Secure Processing**: All analysis happens in isolated serverless functions
- **API Key Protection**: Environment variables keep your keys secure
- **CORS Support**: Configurable for your specific domains

## 📈 Performance & Limits

### Vercel Limits
- **Function Timeout**: 5 minutes (300 seconds)
- **File Size**: 50MB maximum
- **Memory**: 1008MB available
- **Concurrent Executions**: Based on your plan

### Typical Performance
- **Text Analysis**: 0.5-2 seconds
- **Audio Analysis**: 2-10 seconds (depends on length)
- **Stats Endpoint**: <0.5 seconds

## 🆘 Support

### Getting Help

1. **Check the documentation**: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
2. **Review error messages**: API provides detailed error information
3. **Test with examples**: Use the provided test scripts
4. **Check environment variables**: Ensure all keys are set correctly

### Common Issues

**"DeepSeek API key not found"**
- Set `DEEPSEEK_API_KEY` in Vercel environment variables
- Redeploy after adding environment variables

**"Speech recognition failed"**
- Try different audio formats (WAV recommended)
- Ensure audio has clear speech
- Use "aggressive" retry mode for difficult audio

**"Function timeout"**
- Reduce audio file size
- Try shorter audio clips
- Check if all API services are responding

### Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **DeepSeek AI**: Advanced language model for emotion analysis
- **OpenAI Whisper**: State-of-the-art speech recognition
- **Vercel**: Serverless deployment platform
- **CircuitAlg Team**: Original speech analysis system

---

**Ready to deploy?** Click the button below to get started:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/your-username/speech-emotion-api)

*Last updated: January 2024*