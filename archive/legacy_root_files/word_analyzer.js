/**
 * Word Emotion Analyzer Web Interface
 * Provides UI controls for processing words through Claude API
 */

class WordAnalyzerInterface {
    constructor() {
        this.isProcessing = false;
        this.processingMode = null;
        this.stats = {
            totalWords: 0,
            processedWords: 0,
            remainingWords: 0,
            consecutiveErrors: 0
        };
        
        this.initializeElements();
        this.attachEventListeners();
        this.loadInitialStats();
        
        // Auto-refresh stats every 30 seconds
        setInterval(() => {
            if (!this.isProcessing) {
                this.loadStats();
            }
        }, 30000);
    }
    
    initializeElements() {
        // Stat elements
        this.totalWordsEl = document.getElementById('totalWords');
        this.processedWordsEl = document.getElementById('processedWords');
        this.remainingWordsEl = document.getElementById('remainingWords');
        this.completionPercentEl = document.getElementById('completionPercent');
        
        // Progress bar
        this.progressFillEl = document.getElementById('progressFill');
        
        // Control buttons
        this.processSingleBtn = document.getElementById('processSingleBtn');
        this.processBatchBtn = document.getElementById('processBatchBtn');
        this.processAllBtn = document.getElementById('processAllBtn');
        this.stopProcessingBtn = document.getElementById('stopProcessingBtn');
        
        // Display elements
        this.currentWordEl = document.getElementById('currentWord');
        this.logContentEl = document.getElementById('logContent');
        this.errorCountEl = document.getElementById('errorCount');
        
        // Pricing elements
        this.totalCostEl = document.getElementById('totalCost');
        this.costPerWordEl = document.getElementById('costPerWord');
        this.estimatedCostEl = document.getElementById('estimatedCost');
    }
    
    attachEventListeners() {
        this.processSingleBtn.addEventListener('click', () => this.processSingle());
        this.processBatchBtn.addEventListener('click', () => this.processBatch());
        this.processAllBtn.addEventListener('click', () => this.processAll());
        this.stopProcessingBtn.addEventListener('click', () => this.stopProcessing());
    }
    
    async loadInitialStats() {
        await this.loadStats();
        this.addLogEntry('System ready. Click a button to start processing words.', 'info');
    }
    
    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            if (response.ok) {
                this.stats = await response.json();
                this.updateStatsDisplay();
            } else {
                // If API not available, try to estimate from Python script
                this.estimateStatsFromPython();
            }
        } catch (error) {
            console.log('Stats API not available, using Python backend');
            this.estimateStatsFromPython();
        }
    }
    
    async estimateStatsFromPython() {
        try {
            const response = await fetch('/run_python_stats');
            if (response.ok) {
                const result = await response.text();
                this.parseStatsFromPythonOutput(result);
            }
        } catch (error) {
            console.log('Python stats not available');
        }
    }
    
    parseStatsFromPythonOutput(output) {
        // Parse Python script output to extract stats
        const lines = output.split('\n');
        for (const line of lines) {
            if (line.includes('Total Words:')) {
                this.stats.totalWords = parseInt(line.match(/\d+/)[0]);
            } else if (line.includes('Processed:')) {
                this.stats.processedWords = parseInt(line.match(/\d+/)[0]);
            } else if (line.includes('Remaining:')) {
                this.stats.remainingWords = parseInt(line.match(/\d+/)[0]);
            } else if (line.includes('Consecutive Errors:')) {
                this.stats.consecutiveErrors = parseInt(line.match(/\d+/)[0]);
            }
        }
        this.updateStatsDisplay();
    }
    
    updateStatsDisplay() {
        this.totalWordsEl.textContent = this.stats.totalWords.toLocaleString();
        this.processedWordsEl.textContent = this.stats.processedWords.toLocaleString();
        this.remainingWordsEl.textContent = this.stats.remainingWords.toLocaleString();
        
        const percentage = this.stats.totalWords > 0 
            ? ((this.stats.processedWords / this.stats.totalWords) * 100).toFixed(1)
            : 0;
        this.completionPercentEl.textContent = `${percentage}%`;
        
        // Update progress bar
        this.progressFillEl.style.width = `${percentage}%`;
        
        // Update error count
        this.errorCountEl.textContent = this.stats.consecutiveErrors;
        
        // Update current words
        if (this.stats.currentWords && this.stats.currentWords.length > 0) {
            this.currentWordEl.textContent = this.stats.currentWords.join(', ');
        } else {
            this.currentWordEl.textContent = '-';
        }
        
        // Update pricing information
        if (this.stats.pricing) {
            const pricing = this.stats.pricing;
            this.totalCostEl.textContent = `$${pricing.total_cost.toFixed(4)}`;
            this.costPerWordEl.textContent = `$${pricing.avg_cost_per_word.toFixed(6)}`;
            this.estimatedCostEl.textContent = `$${pricing.estimated_remaining_cost.toFixed(2)}`;
        }
        
        // Update error status color
        const errorStatusEl = document.getElementById('errorStatus');
        if (this.stats.consecutiveErrors > 50) {
            errorStatusEl.style.background = '#f8d7da';
            errorStatusEl.style.borderColor = '#f5c6cb';
        } else if (this.stats.consecutiveErrors > 20) {
            errorStatusEl.style.background = '#fff3cd';
            errorStatusEl.style.borderColor = '#ffeaa7';
        } else {
            errorStatusEl.style.background = '#d4edda';
            errorStatusEl.style.borderColor = '#c3e6cb';
        }
    }
    
    setProcessingState(isProcessing, mode = null) {
        this.isProcessing = isProcessing;
        this.processingMode = mode;
        
        // Update button states
        this.processSingleBtn.disabled = isProcessing;
        this.processBatchBtn.disabled = isProcessing;
        this.processAllBtn.disabled = isProcessing;
        this.stopProcessingBtn.disabled = !isProcessing;
        
        if (isProcessing) {
            this.addLogEntry(`Started ${mode} processing mode...`, 'info');
        } else {
            this.addLogEntry('Processing stopped.', 'info');
            this.currentWordEl.textContent = '-';
        }
    }
    
    addLogEntry(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = `[${timestamp}] ${message}\n`;
        
        this.logContentEl.textContent += logEntry;
        this.logContentEl.scrollTop = this.logContentEl.scrollHeight;
        
        // Limit log size
        const lines = this.logContentEl.textContent.split('\n');
        if (lines.length > 100) {
            this.logContentEl.textContent = lines.slice(-80).join('\n');
        }
    }
    
    async processSingle() {
        this.setProcessingState(true, 'single word');
        
        try {
            const response = await this.runPythonCommand('single');
            await this.handleProcessingResponse(response);
        } catch (error) {
            this.addLogEntry(`Error in single word processing: ${error.message}`, 'error');
        } finally {
            this.setProcessingState(false);
            await this.loadStats();
        }
    }
    
    async processBatch() {
        this.setProcessingState(true, 'batch');
        
        try {
            // Start batch processing
            this.batchProcessing = true;
            await this.runBatchProcessing();
        } catch (error) {
            this.addLogEntry(`Error in batch processing: ${error.message}`, 'error');
        } finally {
            this.batchProcessing = false;
            this.setProcessingState(false);
            await this.loadStats();
        }
    }
    
    async processAll() {
        this.setProcessingState(true, 'all words');
        
        try {
            const response = await this.runPythonCommand('all');
            await this.handleProcessingResponse(response);
        } catch (error) {
            this.addLogEntry(`Error in all words processing: ${error.message}`, 'error');
        } finally {
            this.setProcessingState(false);
            await this.loadStats();
        }
    }
    
    stopProcessing() {
        this.batchProcessing = false;
        this.setProcessingState(false);
        this.addLogEntry('Stop requested by user.', 'warning');
    }
    
    async runBatchProcessing() {
        while (this.batchProcessing && this.stats.remainingWords > 0) {
            try {
                const response = await this.runPythonCommand('single');
                await this.handleProcessingResponse(response);
                await this.loadStats();
                
                // Brief pause between words
                await this.sleep(2000);
                
                if (this.stats.consecutiveErrors >= 100) {
                    this.addLogEntry('Stopping due to too many consecutive errors.', 'error');
                    break;
                }
                
            } catch (error) {
                this.addLogEntry(`Batch processing error: ${error.message}`, 'error');
                await this.sleep(5000); // Wait longer on error
            }
        }
    }
    
    async runPythonCommand(command) {
        const response = await fetch('/run_python', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ command })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.text();
    }
    
    async handleProcessingResponse(response) {
        const lines = response.split('\n');
        let currentWord = null;
        
        for (const line of lines) {
            if (line.includes('Processing word:')) {
                const match = line.match(/Processing word: '([^']+)'/);
                if (match) {
                    currentWord = match[1];
                    // Don't update current word here - let the stats API handle it
                    this.addLogEntry(`Processing: ${currentWord}`, 'info');
                }
            } else if (line.includes('Saved')) {
                this.addLogEntry(line, 'success');
            } else if (line.includes('Failed')) {
                this.addLogEntry(line, 'error');
            } else if (line.includes('Error') || line.includes('error')) {
                this.addLogEntry(line, 'error');
            } else if (line.includes('No more words')) {
                this.addLogEntry('All words completed! 🎉', 'success');
            }
        }
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialize the interface when the page loads
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if we're on a page with the word analyzer elements
    if (document.getElementById('wordAnalysisApp')) {
        window.wordAnalyzer = new WordAnalyzerInterface();
    }
});
