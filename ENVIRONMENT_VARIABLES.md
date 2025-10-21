# Environment Variables for Vercel Deployment

This document explains all the environment variables needed for the Speech Emotion Analysis API deployment on Vercel.

## Required Variables

### DEEPSEEK_API_KEY (Required)

**Purpose**: Powers the emotion analysis system by processing text through DeepSeek's AI model.

**How to get it**:
1. Visit [DeepSeek API](https://platform.deepseek.com/)
2. Create an account and verify your email
3. Navigate to API Keys section
4. Generate a new API key
5. Copy the key (starts with `sk-...`)

**Usage**: The system uses DeepSeek to analyze emotional content of words and phrases, providing detailed emotion probabilities across 8 categories.

**Set in Vercel**:
```bash
vercel env add DEEPSEEK_API_KEY
# Paste your key when prompted
```

**Format**: `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## Optional Variables (Enhance Performance)

### OPENAI_API_KEY (Optional)

**Purpose**: Enables Whisper API for high-quality speech transcription.

**How to get it**:
1. Visit [OpenAI API](https://platform.openai.com/api-keys)
2. Create an account and add billing information
3. Generate a new API key
4. Copy the key (starts with `sk-...`)

**Benefits**: 
- More accurate transcription than free alternatives
- Better handling of accents and background noise
- Faster processing for audio analysis

**Set in Vercel**:
```bash
vercel env add OPENAI_API_KEY
```

**Format**: `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### BING_KEY (Optional)

**Purpose**: Microsoft Bing Speech Recognition as a fallback transcription engine.

**How to get it**:
1. Visit [Azure Cognitive Services](https://azure.microsoft.com/en-us/services/cognitive-services/speech-services/)
2. Create an Azure account
3. Create a Speech resource
4. Copy the API key from the resource page

**Benefits**:
- Additional transcription engine for better accuracy
- Good for enterprise environments
- Handles multiple languages well

**Set in Vercel**:
```bash
vercel env add BING_KEY
```

**Format**: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### IBM_USERNAME & IBM_PASSWORD (Optional)

**Purpose**: IBM Watson Speech to Text service as another fallback option.

**How to get them**:
1. Visit [IBM Watson Speech to Text](https://www.ibm.com/cloud/watson-speech-to-text)
2. Create an IBM Cloud account
3. Create a Speech to Text service instance
4. Get the username and password from service credentials

**Benefits**:
- Professional-grade speech recognition
- Good accuracy for business applications
- Multiple language support

**Set in Vercel**:
```bash
vercel env add IBM_USERNAME
vercel env add IBM_PASSWORD
```

**Format**: 
- Username: Usually `apikey`
- Password: Long alphanumeric string

## Setting Environment Variables

### Method 1: Vercel CLI (Recommended)

```bash
# Install Vercel CLI if you haven't already
npm i -g vercel

# Login to Vercel
vercel login

# Add each environment variable
vercel env add DEEPSEEK_API_KEY
vercel env add OPENAI_API_KEY
vercel env add BING_KEY
vercel env add IBM_USERNAME
vercel env add IBM_PASSWORD

# Choose "Production" when prompted for each variable
```

### Method 2: Vercel Dashboard

1. Go to your project on [vercel.com](https://vercel.com)
2. Click on "Settings" tab
3. Click on "Environment Variables" in the sidebar
4. Add each variable:
   - Name: `DEEPSEEK_API_KEY`
   - Value: Your API key
   - Environment: Select "Production", "Preview", and "Development"
5. Click "Save"

### Method 3: .env.local (Development Only)

For local testing, create a `.env.local` file:

```bash
# .env.local (DO NOT COMMIT TO GIT)
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
OPENAI_API_KEY=sk-your-openai-key-here
BING_KEY=your-bing-key-here
IBM_USERNAME=apikey
IBM_PASSWORD=your-ibm-password-here
```

**⚠️ Important**: Never commit `.env.local` to git. Add it to your `.gitignore` file.

## Variable Priority and Fallbacks

The system is designed with intelligent fallbacks:

1. **Primary Speech Recognition**: Local Whisper (no API key needed)
2. **Fallback 1**: OpenAI Whisper API (if `OPENAI_API_KEY` provided)
3. **Fallback 2**: Bing Speech (if `BING_KEY` provided)
4. **Fallback 3**: IBM Watson (if `IBM_USERNAME` and `IBM_PASSWORD` provided)
5. **Final Fallback**: Google Speech (free, built-in)

**Emotion Analysis**: Only requires `DEEPSEEK_API_KEY` - no fallbacks needed.

## Security Best Practices

### 1. API Key Rotation

Regularly rotate your API keys:
- DeepSeek: Every 90 days
- OpenAI: Every 90 days  
- Azure/Bing: Every 180 days
- IBM Watson: Every 180 days

### 2. Usage Monitoring

Monitor your API usage to detect anomalies:
- Check your provider dashboards regularly
- Set up billing alerts
- Monitor for unusual usage patterns

### 3. Access Control

- Only share API keys with authorized team members
- Use separate keys for development and production
- Revoke keys immediately if compromised

### 4. Environment Separation

Use different API keys for different environments:
- Development: Lower-tier keys with usage limits
- Staging: Mid-tier keys for testing
- Production: Full-featured keys with monitoring

## Cost Optimization

### DeepSeek API Costs

- **Model**: deepseek-chat
- **Typical cost**: ~$0.0014 per 1K tokens
- **Estimated usage**: 50-200 tokens per text analysis
- **Monthly estimate**: $5-20 for moderate usage (1000 requests)

### OpenAI Whisper API Costs

- **Model**: whisper-1
- **Cost**: $0.006 per minute of audio
- **Typical usage**: 30-second clips = ~$0.003 per analysis
- **Monthly estimate**: $10-30 for moderate usage (1000 audio files)

### Cost-Saving Tips

1. **Use local Whisper first**: It's free and quite accurate
2. **Optimize audio length**: Trim silence to reduce costs
3. **Cache results**: Store results to avoid re-processing
4. **Use text analysis**: Much cheaper than audio analysis
5. **Set usage limits**: Configure billing alerts

## Testing Your Setup

### 1. Test Environment Variables

```bash
# Test if variables are set correctly
vercel env ls
```

### 2. Test API Endpoints

```bash
# Test stats endpoint (doesn't require API keys)
curl https://your-project.vercel.app/api/stats

# Test text analysis (requires DEEPSEEK_API_KEY)
curl -X POST https://your-project.vercel.app/api/analyze-text \
  -H "Content-Type: application/json" \
  -d '{"text": "I am happy"}'

# Test audio analysis (requires audio file)
curl -X POST https://your-project.vercel.app/api/analyze-audio \
  -F "audio=@test.wav"
```

### 3. Check Logs

```bash
# View function logs
vercel logs
```

## Troubleshooting

### Common Issues

**1. "DeepSeek API key not found"**
```
Error: Failed to process text: API key not found
```
**Solution**: Ensure `DEEPSEEK_API_KEY` is set correctly in Vercel dashboard.

**2. "OpenAI API quota exceeded"**
```
Error: OpenAI API quota exceeded
```
**Solution**: Check your OpenAI billing and increase limits, or rely on fallback engines.

**3. "All speech recognition engines failed"**
```
Error: All recognition services failed
```
**Solution**: At least one speech engine should work (Google is always available). Check if audio file is valid.

**4. Environment variables not loading**
```
Error: Cannot read environment variable
```
**Solution**: Redeploy after setting environment variables:
```bash
vercel --prod
```

### Debugging Steps

1. **Check variable names**: Ensure exact spelling
2. **Check variable values**: No extra spaces or characters
3. **Redeploy**: Environment changes require redeployment
4. **Check logs**: Use `vercel logs` to see detailed errors
5. **Test locally**: Use `vercel dev` with `.env.local`

## Migration from Local Setup

If you're migrating from a local Flask setup:

1. **Export current settings**: Check your current `.env` file
2. **Map variables**: Most variables have the same names
3. **Test gradually**: Add one API key at a time and test
4. **Monitor performance**: Compare accuracy with your local setup

## Support

For environment variable issues:

1. **Check Vercel docs**: [Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)
2. **API provider docs**: Check your specific API provider's documentation
3. **Test endpoints**: Use the testing commands above
4. **Check logs**: Always check Vercel function logs for detailed errors

---

*Last updated: January 2024*
