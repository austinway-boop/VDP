// API Token Authentication Middleware
// Provides secure API access control using hashed tokens

const crypto = require('crypto');

class ApiAuthenticator {
    constructor() {
        // Load authorized tokens from environment variables
        this.authorizedTokens = this.loadAuthorizedTokens();
        this.rateLimits = new Map(); // Simple rate limiting
        console.log(`🔐 API Authentication initialized with ${this.authorizedTokens.size} authorized tokens`);
    }
    
    loadAuthorizedTokens() {
        const tokens = new Set();
        
        // Load tokens from environment variables
        // Format: API_TOKEN_1, API_TOKEN_2, etc.
        for (let i = 1; i <= 50; i++) {
            const tokenVar = `API_TOKEN_${i}`;
            const token = process.env[tokenVar];
            if (token) {
                // Store the hash of the token for security
                const hashedToken = this.hashToken(token);
                tokens.add(hashedToken);
                console.log(`✅ Loaded API token ${i}: ${hashedToken.substring(0, 8)}...`);
            }
        }
        
        // If no tokens are configured, create a default one for development
        if (tokens.size === 0) {
            console.log('⚠️  No API tokens configured in environment variables');
            console.log('⚠️  Using default development token: "dev-token-123"');
            console.log('⚠️  Set API_TOKEN_1, API_TOKEN_2, etc. in production');
            
            const defaultToken = this.hashToken('dev-token-123');
            tokens.add(defaultToken);
        }
        
        return tokens;
    }
    
    hashToken(token) {
        // Use SHA-256 to hash tokens for secure storage
        return crypto.createHash('sha256').update(token).digest('hex');
    }
    
    authenticate(req, res, next) {
        // Extract token from Authorization header or query parameter
        let token = null;
        
        // Check Authorization header (Bearer token)
        const authHeader = req.headers.authorization;
        if (authHeader && authHeader.startsWith('Bearer ')) {
            token = authHeader.substring(7);
        }
        
        // Check query parameter as fallback
        if (!token && req.query.api_token) {
            token = req.query.api_token;
        }
        
        // Check if token is provided
        if (!token) {
            return res.status(401).json({
                success: false,
                error: 'Authentication required',
                message: 'Please provide an API token in the Authorization header (Bearer token) or as api_token query parameter',
                example: {
                    header: 'Authorization: Bearer your-api-token-here',
                    query: '?api_token=your-api-token-here'
                }
            });
        }
        
        // Hash the provided token and check if it's authorized
        const hashedToken = this.hashToken(token);
        
        if (!this.authorizedTokens.has(hashedToken)) {
            console.log(`❌ Unauthorized API access attempt with token: ${hashedToken.substring(0, 8)}...`);
            return res.status(401).json({
                success: false,
                error: 'Invalid API token',
                message: 'The provided API token is not authorized to access this API'
            });
        }
        
        // Check rate limiting (simple implementation)
        const clientId = hashedToken.substring(0, 8);
        const now = Date.now();
        const windowMs = 60 * 1000; // 1 minute window
        const maxRequests = 100; // Max 100 requests per minute per token
        
        if (!this.rateLimits.has(clientId)) {
            this.rateLimits.set(clientId, []);
        }
        
        const requests = this.rateLimits.get(clientId);
        const recentRequests = requests.filter(time => now - time < windowMs);
        
        if (recentRequests.length >= maxRequests) {
            return res.status(429).json({
                success: false,
                error: 'Rate limit exceeded',
                message: `Maximum ${maxRequests} requests per minute exceeded`,
                retry_after: Math.ceil((recentRequests[0] + windowMs - now) / 1000)
            });
        }
        
        // Update rate limiting
        recentRequests.push(now);
        this.rateLimits.set(clientId, recentRequests);
        
        // Log successful authentication
        console.log(`✅ Authenticated API request from token: ${clientId}...`);
        
        // Add client info to request for logging
        req.apiClient = {
            tokenHash: hashedToken.substring(0, 8),
            authenticated: true
        };
        
        // Continue to the actual endpoint
        next();
    }
    
    // Utility method to generate new tokens
    generateToken() {
        return crypto.randomBytes(32).toString('hex');
    }
    
    // Get authentication statistics
    getAuthStats() {
        return {
            authorized_tokens: this.authorizedTokens.size,
            active_rate_limits: this.rateLimits.size,
            rate_limit_window: '60 seconds',
            max_requests_per_window: 100
        };
    }
}

// Global authenticator instance
const apiAuth = new ApiAuthenticator();

// Export both the middleware function and the authenticator instance
module.exports = {
    authenticate: (req, res, next) => apiAuth.authenticate(req, res, next),
    apiAuth,
    generateToken: () => apiAuth.generateToken()
};
