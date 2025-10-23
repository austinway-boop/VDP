# CircuitAlg Speech Emotion API - Authentication Guide

## 🔐 API Authentication Overview

The CircuitAlg Speech Emotion API now requires authentication using secure API tokens to control access and ensure proper usage. All API endpoints require a valid API token to be provided with each request.

## 🛡️ Security Features

- **Hashed Token Storage**: API tokens are stored as SHA-256 hashes for security
- **Rate Limiting**: 100 requests per minute per token
- **Token Management**: Create, list, and deactivate tokens as needed
- **Environment Variable Support**: Secure token storage via environment variables

## 📚 API Endpoints

All endpoints now require authentication:

- `POST /api/analyze-text` - Text emotion analysis
- `POST /api/analyze-audio` - Audio analysis (redirects to text analysis)
- `POST /api/analyze-audio-browser` - Browser-based audio analysis
- `GET /api/stats` - System statistics and health

## 🔑 Getting API Tokens

### Method 1: Using the Token Manager Script

Generate new API tokens using the provided management script:

```bash
# Generate a new token
node scripts/manage-api-tokens.js generate "My Application"

# List all tokens
node scripts/manage-api-tokens.js list

# Deactivate a token
node scripts/manage-api-tokens.js deactivate 1

# Validate a token
node scripts/manage-api-tokens.js validate your-token-here
```

### Method 2: Environment Variables (Production)

For production deployments, set API tokens as environment variables:

```bash
API_TOKEN_1=your-first-token-here
API_TOKEN_2=your-second-token-here
API_TOKEN_3=your-third-token-here
# ... up to API_TOKEN_50
```

### Method 3: Development Default

For development, a default token is available:
- **Token**: `dev-token-123`
- **Note**: Only use this for development/testing

## 🌐 Using the API

### Authentication Methods

#### Method 1: Authorization Header (Recommended)

```bash
curl -X POST https://your-api-domain.com/api/analyze-text \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-token-here" \
  -d '{"text": "I am feeling great today!"}'
```

#### Method 2: Query Parameter

```bash
curl -X POST "https://your-api-domain.com/api/analyze-text?api_token=your-api-token-here" \
  -H "Content-Type: application/json" \
  -d '{"text": "I am feeling great today!"}'
```

### JavaScript Example

```javascript
const apiToken = 'your-api-token-here';
const apiUrl = 'https://your-api-domain.com/api/analyze-text';

const response = await fetch(apiUrl, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiToken}`
    },
    body: JSON.stringify({
        text: 'I am feeling excited about this project!'
    })
});

const result = await response.json();
console.log(result);
```

### Python Example

```python
import requests

api_token = 'your-api-token-here'
api_url = 'https://your-api-domain.com/api/analyze-text'

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {api_token}'
}

data = {
    'text': 'I am feeling excited about this project!'
}

response = requests.post(api_url, json=data, headers=headers)
result = response.json()
print(result)
```

## 🚀 Deployment Setup

### Vercel Deployment

1. **Set Environment Variables in Vercel Dashboard**:
   - Go to your Vercel project settings
   - Add environment variables:
     ```
     API_TOKEN_1 = your-first-production-token
     API_TOKEN_2 = your-second-production-token
     ```

2. **Or use Vercel CLI**:
   ```bash
   vercel env add API_TOKEN_1
   # Enter your token when prompted
   
   vercel env add API_TOKEN_2
   # Enter your second token when prompted
   ```

### Local Development

1. **Create `.env` file**:
   ```bash
   API_TOKEN_1=dev-token-123
   API_TOKEN_2=your-dev-token-here
   DEEPSEEK_API_KEY=your-deepseek-key-here
   ```

2. **Start the development server**:
   ```bash
   npm run dev
   # or
   vercel dev
   ```

## 🔒 Security Best Practices

### Token Management

1. **Generate Strong Tokens**: Use the token manager script for cryptographically secure tokens
2. **Rotate Tokens Regularly**: Deactivate old tokens and generate new ones periodically
3. **Use Different Tokens**: Create separate tokens for different applications/environments
4. **Monitor Usage**: Check API logs for unusual activity

### Environment Security

1. **Never Commit Tokens**: Add `.env` files to `.gitignore`
2. **Use Environment Variables**: Store tokens as environment variables in production
3. **Limit Token Scope**: Create tokens for specific use cases
4. **Revoke Unused Tokens**: Deactivate tokens that are no longer needed

## 📊 Rate Limiting

Each API token has the following limits:

- **Rate Limit**: 100 requests per minute
- **Window**: 60 seconds
- **Behavior**: Returns 429 status code when exceeded
- **Reset**: Automatic after the rate limit window expires

### Rate Limit Response

```json
{
  "success": false,
  "error": "Rate limit exceeded",
  "message": "Maximum 100 requests per minute exceeded",
  "retry_after": 30
}
```

## ❌ Error Responses

### Authentication Required (401)

```json
{
  "success": false,
  "error": "Authentication required",
  "message": "Please provide an API token in the Authorization header (Bearer token) or as api_token query parameter",
  "example": {
    "header": "Authorization: Bearer your-api-token-here",
    "query": "?api_token=your-api-token-here"
  }
}
```

### Invalid Token (401)

```json
{
  "success": false,
  "error": "Invalid API token",
  "message": "The provided API token is not authorized to access this API"
}
```

### Rate Limit Exceeded (429)

```json
{
  "success": false,
  "error": "Rate limit exceeded",
  "message": "Maximum 100 requests per minute exceeded",
  "retry_after": 45
}
```

## 🛠️ Token Management Commands

### Generate New Token

```bash
node scripts/manage-api-tokens.js generate "Production API"
```

**Output:**
```
✅ New API token created successfully!
📋 Token ID: 1
🔑 Token: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
📝 Description: Production API

⚠️  IMPORTANT: Save this token securely! It cannot be retrieved again.
💡 Set this as an environment variable: API_TOKEN_1=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

### List All Tokens

```bash
node scripts/manage-api-tokens.js list
```

**Output:**
```
📋 API Tokens:

ID: 1
Description: Production API
Status: ✅ Active
Created: 2024-10-23T10:30:00.000Z
Hash Preview: a1b2c3d4...
---
ID: 2
Description: Development Testing
Status: ❌ Inactive
Created: 2024-10-23T11:45:00.000Z
Hash Preview: e5f6g7h8...
---
```

### Deactivate Token

```bash
node scripts/manage-api-tokens.js deactivate 2
```

**Output:**
```
✅ Token deactivated successfully
```

### Validate Token

```bash
node scripts/manage-api-tokens.js validate your-token-here
```

**Output:**
```
✅ Token is valid
📋 Token Info: {
  "id": 1,
  "description": "Production API",
  "created": "2024-10-23T10:30:00.000Z"
}
```

## 🔧 Integration Examples

### React/Next.js Integration

```javascript
// hooks/useEmotionAPI.js
import { useState } from 'react';

export function useEmotionAPI() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyzeText = async (text) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/analyze-text', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${process.env.NEXT_PUBLIC_API_TOKEN}`
        },
        body: JSON.stringify({ text })
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { analyzeText, loading, error };
}
```

### Node.js Backend Integration

```javascript
// services/emotionService.js
const axios = require('axios');

class EmotionService {
  constructor(apiToken, baseUrl) {
    this.apiToken = apiToken;
    this.baseUrl = baseUrl;
    this.client = axios.create({
      baseURL: baseUrl,
      headers: {
        'Authorization': `Bearer ${apiToken}`,
        'Content-Type': 'application/json'
      }
    });
  }

  async analyzeText(text) {
    try {
      const response = await this.client.post('/api/analyze-text', { text });
      return response.data;
    } catch (error) {
      if (error.response?.status === 401) {
        throw new Error('Invalid API token');
      } else if (error.response?.status === 429) {
        throw new Error('Rate limit exceeded');
      }
      throw error;
    }
  }

  async getStats() {
    const response = await this.client.get('/api/stats');
    return response.data;
  }
}

module.exports = EmotionService;
```

## 🆘 Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check if token is provided in request
   - Verify token is correct and active
   - Ensure proper header format: `Authorization: Bearer token`

2. **429 Rate Limited**
   - Wait for rate limit window to reset
   - Implement exponential backoff in your client
   - Consider using multiple tokens for higher throughput

3. **Token Not Working**
   - Verify token hasn't been deactivated
   - Check environment variable names (API_TOKEN_1, API_TOKEN_2, etc.)
   - Ensure no extra spaces or characters in token

### Support

For additional support:
1. Check the API logs for detailed error messages
2. Use the token validation command to verify your token
3. Review the rate limiting section for usage guidelines

## 📝 Changelog

### v2.1.0 - Authentication Added
- ✅ Added secure API token authentication
- ✅ Implemented rate limiting (100 req/min per token)
- ✅ Created token management utilities
- ✅ Added comprehensive error handling
- ✅ Updated all endpoints to require authentication

---

**Happy Coding! 🚀**

For more information about the emotion analysis capabilities, see the main [README.md](./README.md) file.
