#!/usr/bin/env node

// API Token Management Utility
// Generate, validate, and manage API tokens for the CircuitAlg API

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

class TokenManager {
    constructor() {
        this.tokensFile = path.join(__dirname, '..', 'api-tokens.json');
    }
    
    // Generate a new secure API token
    generateToken(description = 'API Token') {
        const token = crypto.randomBytes(32).toString('hex');
        const hash = this.hashToken(token);
        
        return {
            token: token,
            hash: hash,
            description: description,
            created: new Date().toISOString(),
            active: true
        };
    }
    
    // Hash a token using SHA-256
    hashToken(token) {
        return crypto.createHash('sha256').update(token).digest('hex');
    }
    
    // Load existing tokens from file
    loadTokens() {
        try {
            if (fs.existsSync(this.tokensFile)) {
                const data = fs.readFileSync(this.tokensFile, 'utf8');
                return JSON.parse(data);
            }
        } catch (error) {
            console.error('Error loading tokens file:', error.message);
        }
        return { tokens: [], created: new Date().toISOString() };
    }
    
    // Save tokens to file
    saveTokens(tokenData) {
        try {
            fs.writeFileSync(this.tokensFile, JSON.stringify(tokenData, null, 2));
            return true;
        } catch (error) {
            console.error('Error saving tokens file:', error.message);
            return false;
        }
    }
    
    // Add a new token
    addToken(description = 'API Token') {
        const tokenData = this.loadTokens();
        const newToken = this.generateToken(description);
        
        tokenData.tokens.push({
            id: tokenData.tokens.length + 1,
            hash: newToken.hash,
            description: description,
            created: newToken.created,
            active: true,
            last_used: null
        });
        
        if (this.saveTokens(tokenData)) {
            return {
                success: true,
                token: newToken.token,
                id: tokenData.tokens.length,
                message: 'Token created successfully'
            };
        }
        
        return { success: false, message: 'Failed to save token' };
    }
    
    // List all tokens (without revealing the actual tokens)
    listTokens() {
        const tokenData = this.loadTokens();
        return tokenData.tokens.map(token => ({
            id: token.id,
            description: token.description,
            created: token.created,
            active: token.active,
            last_used: token.last_used,
            hash_preview: token.hash.substring(0, 8) + '...'
        }));
    }
    
    // Deactivate a token
    deactivateToken(tokenId) {
        const tokenData = this.loadTokens();
        const token = tokenData.tokens.find(t => t.id === tokenId);
        
        if (!token) {
            return { success: false, message: 'Token not found' };
        }
        
        token.active = false;
        
        if (this.saveTokens(tokenData)) {
            return { success: true, message: 'Token deactivated successfully' };
        }
        
        return { success: false, message: 'Failed to save changes' };
    }
    
    // Generate environment variables for Vercel
    generateEnvVars() {
        const tokenData = this.loadTokens();
        const activeTokens = tokenData.tokens.filter(t => t.active);
        
        let envVars = '';
        activeTokens.forEach((token, index) => {
            // We need to reverse-engineer the original token from the hash
            // This is not possible, so we'll generate new tokens for env vars
            console.log(`⚠️  Cannot generate env vars from hashed tokens.`);
            console.log(`⚠️  Use the original tokens you received when creating them.`);
        });
        
        return {
            success: false,
            message: 'Cannot generate env vars from hashed tokens. Use original tokens.',
            example: `API_TOKEN_1=your-token-here\nAPI_TOKEN_2=your-other-token-here`
        };
    }
    
    // Validate a token
    validateToken(token) {
        const hash = this.hashToken(token);
        const tokenData = this.loadTokens();
        const foundToken = tokenData.tokens.find(t => t.hash === hash && t.active);
        
        return {
            valid: !!foundToken,
            token_info: foundToken ? {
                id: foundToken.id,
                description: foundToken.description,
                created: foundToken.created
            } : null
        };
    }
}

// Command line interface
function main() {
    const tokenManager = new TokenManager();
    const args = process.argv.slice(2);
    const command = args[0];
    
    switch (command) {
        case 'generate':
        case 'create':
            const description = args[1] || 'API Token';
            const result = tokenManager.addToken(description);
            if (result.success) {
                console.log('✅ New API token created successfully!');
                console.log('📋 Token ID:', result.id);
                console.log('🔑 Token:', result.token);
                console.log('📝 Description:', description);
                console.log('');
                console.log('⚠️  IMPORTANT: Save this token securely! It cannot be retrieved again.');
                console.log('💡 Set this as an environment variable: API_TOKEN_' + result.id + '=' + result.token);
            } else {
                console.error('❌ Failed to create token:', result.message);
            }
            break;
            
        case 'list':
            const tokens = tokenManager.listTokens();
            if (tokens.length === 0) {
                console.log('📭 No tokens found.');
            } else {
                console.log('📋 API Tokens:');
                console.log('');
                tokens.forEach(token => {
                    console.log(`ID: ${token.id}`);
                    console.log(`Description: ${token.description}`);
                    console.log(`Status: ${token.active ? '✅ Active' : '❌ Inactive'}`);
                    console.log(`Created: ${token.created}`);
                    console.log(`Hash Preview: ${token.hash_preview}`);
                    console.log('---');
                });
            }
            break;
            
        case 'deactivate':
        case 'disable':
            const tokenId = parseInt(args[1]);
            if (!tokenId) {
                console.error('❌ Please provide a token ID to deactivate');
                console.log('💡 Usage: node manage-api-tokens.js deactivate <token_id>');
                break;
            }
            
            const deactivateResult = tokenManager.deactivateToken(tokenId);
            if (deactivateResult.success) {
                console.log('✅ Token deactivated successfully');
            } else {
                console.error('❌ Failed to deactivate token:', deactivateResult.message);
            }
            break;
            
        case 'validate':
            const tokenToValidate = args[1];
            if (!tokenToValidate) {
                console.error('❌ Please provide a token to validate');
                console.log('💡 Usage: node manage-api-tokens.js validate <token>');
                break;
            }
            
            const validation = tokenManager.validateToken(tokenToValidate);
            if (validation.valid) {
                console.log('✅ Token is valid');
                console.log('📋 Token Info:', validation.token_info);
            } else {
                console.log('❌ Token is invalid or inactive');
            }
            break;
            
        case 'env':
            const envResult = tokenManager.generateEnvVars();
            console.log('📋 Environment Variables Setup:');
            console.log('');
            console.log('For Vercel deployment, set these environment variables:');
            console.log('');
            console.log('Example:');
            console.log('API_TOKEN_1=your-first-token-here');
            console.log('API_TOKEN_2=your-second-token-here');
            console.log('');
            console.log('💡 Use the original tokens you received when creating them.');
            break;
            
        default:
            console.log('🔧 CircuitAlg API Token Manager');
            console.log('');
            console.log('Usage:');
            console.log('  node manage-api-tokens.js generate [description]  - Create a new API token');
            console.log('  node manage-api-tokens.js list                   - List all tokens');
            console.log('  node manage-api-tokens.js deactivate <id>        - Deactivate a token');
            console.log('  node manage-api-tokens.js validate <token>       - Validate a token');
            console.log('  node manage-api-tokens.js env                    - Show environment setup');
            console.log('');
            console.log('Examples:');
            console.log('  node manage-api-tokens.js generate "Production API Key"');
            console.log('  node manage-api-tokens.js generate "Development Testing"');
            console.log('  node manage-api-tokens.js list');
            console.log('  node manage-api-tokens.js deactivate 1');
    }
}

if (require.main === module) {
    main();
}

module.exports = TokenManager;
