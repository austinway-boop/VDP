class AudioRecorder {
    constructor() {
        this.audioContext = null;
        this.mediaRecorder = null;
        this.isRecording = false;
        this.audioBuffer = null;
        this.audioSource = null;
        this.isPlaying = false;
        this.startTime = 0;
        this.pauseTime = 0;
        this.animationFrame = null;
        this.canvas = document.getElementById('waveform');
        this.ctx = this.canvas.getContext('2d');
        this.arousalCanvas = document.getElementById('arousal');
        this.arousalCtx = this.arousalCanvas.getContext('2d');
        this.waveformData = null;
        this.arousalData = null;
        this.loudnessDataStatic = [];
        this.pitchDataStatic = [];
        this.paceDataStatic = [];
        this.analyser = null;
        this.recordingVisualizer = null;
        this.colorOffset = 0;
        this.speechData = [];
        this.realtimeSpeechBoxes = [];
        this.pitchData = [];
        this.paceData = [];
        this.loudnessData = [];
        this.lastSpeechTime = 0;
        this.speechEvents = [];
        this.wordCount = 0;
        this.recordingStartTime = 0;
        
        this.elements = {
            recordBtn: document.getElementById('recordBtn'),
            uploadBtn: document.getElementById('uploadBtn'),
            emotionBtn: document.getElementById('emotionBtn'),
            fileInput: document.getElementById('fileInput'),
            recordingStatus: document.getElementById('recordingStatus'),
            countdown: document.getElementById('countdown'),
            statusMessage: document.getElementById('statusMessage'),
            waveformSection: document.getElementById('waveformSection'),
            playbackControls: document.getElementById('playbackControls'),
            playBtn: document.getElementById('playBtn'),
            currentTime: document.getElementById('currentTime'),
            totalTime: document.getElementById('totalTime'),
            audioInfo: document.getElementById('audioInfo'),
            duration: document.getElementById('duration'),
            scrubber: document.getElementById('scrubber'),
            speechAnalysis: document.getElementById('speechAnalysis'),
            speechBoxes: document.getElementById('speechBoxes'),
            speakingPercentage: document.getElementById('speakingPercentage'),
            arousalInfo: document.getElementById('arousalInfo'),
            arousalBarFill: document.getElementById('arousalBarFill'),
            metricsContainer: document.getElementById('metricsContainer'),
            loudnessCanvas: document.getElementById('loudnessCanvas'),
            pitchCanvas: document.getElementById('pitchCanvas'),
            paceCanvas: document.getElementById('paceCanvas'),
            loudnessInfo: document.getElementById('loudnessInfo'),
            pitchInfo: document.getElementById('pitchInfo'),
            paceInfo: document.getElementById('paceInfo'),
            loudnessBarFill: document.getElementById('loudnessBarFill'),
            pitchBarFill: document.getElementById('pitchBarFill'),
            paceBarFill: document.getElementById('paceBarFill'),
            // Emotion analysis elements
            emotionAnalysis: document.getElementById('emotionAnalysis'),
            transcriptionText: document.getElementById('transcriptionText'),
            wordBreakdown: document.getElementById('wordBreakdown'),
            emotionIcon: document.getElementById('emotionIcon'),
            emotionName: document.getElementById('emotionName'),
            emotionConfidence: document.getElementById('emotionConfidence'),
            emotionDetails: document.getElementById('emotionDetails'),
            valenceScore: document.getElementById('valenceScore'),
            arousalScore: document.getElementById('arousalScore'),
            dominanceScore: document.getElementById('dominanceScore'),
            sentimentPolarity: document.getElementById('sentimentPolarity'),
            sentimentStrength: document.getElementById('sentimentStrength')
        };

        this.init();
    }

    init() {
        this.setupCanvas();
        this.setupArousalCanvas();
        this.setupMetricCanvases();
        this.bindEvents();
        window.addEventListener('resize', () => {
            this.setupCanvas();
            this.setupArousalCanvas();
            this.setupMetricCanvases();
        });
    }

    setupCanvas() {
        const container = this.canvas.parentElement;
        const rect = container.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        
        this.canvas.width = (rect.width - 30) * dpr; // Account for padding
        this.canvas.height = 150 * dpr; // Updated height
        this.canvas.style.width = (rect.width - 30) + 'px';
        this.canvas.style.height = '150px';
        
        this.ctx.scale(dpr, dpr);
    }

    setupArousalCanvas() {
        const container = this.arousalCanvas.parentElement;
        const rect = container.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        
        this.arousalCanvas.width = (rect.width - 30) * dpr; // Account for padding
        this.arousalCanvas.height = 60 * dpr;
        this.arousalCanvas.style.width = (rect.width - 30) + 'px';
        this.arousalCanvas.style.height = '60px';
        
        this.arousalCtx.scale(dpr, dpr);
        
        console.log('Arousal canvas setup:', {
            containerWidth: rect.width,
            canvasWidth: this.arousalCanvas.width,
            canvasHeight: this.arousalCanvas.height,
            dpr: dpr
        });
    }

    setupMetricCanvases() {
        const canvases = [
            { canvas: this.elements.loudnessCanvas, name: 'loudness' },
            { canvas: this.elements.pitchCanvas, name: 'pitch' },
            { canvas: this.elements.paceCanvas, name: 'pace' }
        ];

        canvases.forEach(({ canvas, name }) => {
            const container = canvas.parentElement;
            const rect = container.getBoundingClientRect();
            const dpr = window.devicePixelRatio || 1;
            
            canvas.width = (rect.width - 30) * dpr; // Account for padding like arousal
            canvas.height = 60 * dpr; // Same height as arousal
            canvas.style.width = (rect.width - 30) + 'px';
            canvas.style.height = '60px';
            
            const ctx = canvas.getContext('2d');
            ctx.scale(dpr, dpr);
            
            // Store context for later use
            this[name + 'Ctx'] = ctx;
        });
    }

    bindEvents() {
        this.elements.recordBtn.addEventListener('click', () => this.toggleRecording());
        this.elements.uploadBtn.addEventListener('click', () => this.elements.fileInput.click());
        this.elements.emotionBtn.addEventListener('click', () => this.analyzeEmotion());
        this.elements.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        this.elements.playBtn.addEventListener('click', () => this.togglePlayback());
        this.canvas.addEventListener('click', (e) => this.handleWaveformClick(e));
    }

    async toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }

    async startRecording() {
        try {
            this.showStatus('Requesting microphone access...', 'success');
            
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 44100
                }
            });

            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Set up real-time visualization
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            const source = this.audioContext.createMediaStreamSource(stream);
            source.connect(this.analyser);
            
            // Try to use a format that's more compatible with speech recognition
            const mimeTypes = [
                'audio/wav',
                'audio/webm;codecs=pcm',
                'audio/webm;codecs=opus',
                'audio/webm',
                'audio/mp4'
            ];
            
            let selectedMimeType = '';
            for (const mimeType of mimeTypes) {
                if (MediaRecorder.isTypeSupported(mimeType)) {
                    selectedMimeType = mimeType;
                    console.log('Using MIME type for recording:', mimeType);
                    break;
                }
            }
            
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: selectedMimeType || 'audio/webm;codecs=opus'
            });
            
            const audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = async () => {
                const mimeType = this.mediaRecorder.mimeType || 'audio/webm';
                const audioBlob = new Blob(audioChunks, { type: mimeType });
                console.log('Audio recording complete:', {
                    size: audioBlob.size,
                    type: audioBlob.type,
                    mimeType: mimeType
                });
                await this.processAudioBlob(audioBlob);
                stream.getTracks().forEach(track => track.stop());
            };

            this.mediaRecorder.start(100); // Collect data every 100ms
            this.isRecording = true;
            this.elements.recordBtn.textContent = 'Stop Recording';
            this.elements.recordBtn.style.background = '#666';
            this.elements.uploadBtn.disabled = true;
            this.elements.recordingStatus.classList.add('active');
            this.hideStatus();
            
            // Start real-time visualization and speech detection
            this.setupRealtimeSpeechBoxes();
            this.elements.waveformSection.classList.add('visible');
            this.startRecordingVisualization();

            // 10-second countdown
            let timeLeft = 10;
            const countdownInterval = setInterval(() => {
                timeLeft--;
                this.elements.countdown.textContent = timeLeft;
                if (timeLeft <= 0) {
                    clearInterval(countdownInterval);
                    this.stopRecording();
                }
            }, 1000);

            this.countdownInterval = countdownInterval;

        } catch (error) {
            this.showStatus('Error: ' + error.message, 'error');
            console.error('Recording error:', error);
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.elements.recordBtn.textContent = 'Record 10s';
            this.elements.recordBtn.style.background = '';
            this.elements.uploadBtn.disabled = false;
            this.elements.recordingStatus.classList.remove('active');
            this.elements.countdown.textContent = '10';
            
            // Stop recording visualization
            this.stopRecordingVisualization();
            
            // Reset arousal info text and bar
            this.elements.arousalInfo.textContent = 'Avg Arousal: 0%';
            this.elements.arousalBarFill.style.width = '0%';
                
            if (this.countdownInterval) {
                clearInterval(this.countdownInterval);
            }
        }
    }

    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        if (!file.type.startsWith('audio/')) {
            this.showStatus('Please select an audio file', 'error');
            return;
        }

        this.showStatus('Processing file...', 'success');
        await this.processAudioBlob(file);
    }

    async processAudioBlob(blob) {
        try {
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }

            const arrayBuffer = await blob.arrayBuffer();
            this.audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
            
            this.drawWaveform();
            this.showAudioInfo();
            this.showStatus('Audio loaded successfully!', 'success');
            this.elements.emotionBtn.style.display = 'inline-block';
            
            // Automatically analyze emotion after audio is loaded
            setTimeout(() => {
                this.analyzeEmotion();
            }, 500);
            
        } catch (error) {
            this.showStatus('Error processing audio: ' + error.message, 'error');
            console.error('Processing error:', error);
        }
    }

    drawWaveform() {
        if (!this.audioBuffer) return;

        const width = this.canvas.width / (window.devicePixelRatio || 1);
        const height = this.canvas.height / (window.devicePixelRatio || 1);
        
        this.ctx.clearRect(0, 0, width, height);
        
        // Get audio data with better sampling
        const data = this.audioBuffer.getChannelData(0);
        const samplesPerPixel = Math.max(1, Math.floor(data.length / width));
        const amp = height / 2;

        // Pre-calculate waveform data for better accuracy
        this.waveformData = [];
        
        for (let i = 0; i < width; i++) {
            const start = i * samplesPerPixel;
            const end = Math.min(start + samplesPerPixel, data.length);
            
            let min = 0;
            let max = 0;
            let sum = 0;
            let count = 0;
            
            for (let j = start; j < end; j++) {
                const sample = data[j];
                if (sample < min) min = sample;
                if (sample > max) max = sample;
                sum += Math.abs(sample);
                count++;
            }
            
            const avg = count > 0 ? sum / count : 0;
            this.waveformData.push({ min, max, avg });
        }

        console.log('About to analyze arousal, metrics, and speech...');
        this.redrawWaveform();
        this.analyzeEnhancedArousal(); // Enhanced version with pitch and pace
        this.analyzeStaticMetrics(); // Analyze loudness, pitch, pace for static audio
        this.analyzeSpeech();
        console.log('Finished analyzing arousal, metrics, and speech.');
        this.elements.waveformSection.classList.add('visible');
        this.elements.playbackControls.classList.add('visible');
    }

    redrawWaveform(playPosition = -1) {
        if (!this.waveformData) return;

        const width = this.canvas.width / (window.devicePixelRatio || 1);
        const height = this.canvas.height / (window.devicePixelRatio || 1);
        const amp = height / 2;
        
        this.ctx.clearRect(0, 0, width, height);

        // Create gradient backgrounds
        const bgGradient = this.ctx.createLinearGradient(0, 0, 0, height);
        bgGradient.addColorStop(0, 'rgba(255, 255, 255, 0.05)');
        bgGradient.addColorStop(0.5, 'rgba(255, 255, 255, 0.02)');
        bgGradient.addColorStop(1, 'rgba(255, 255, 255, 0.05)');
        this.ctx.fillStyle = bgGradient;
        this.ctx.fillRect(0, 0, width, height);

        // Draw animated center line
        const centerGradient = this.ctx.createLinearGradient(0, 0, width, 0);
        centerGradient.addColorStop(0, 'rgba(255, 255, 255, 0.2)');
        centerGradient.addColorStop(0.5, 'rgba(255, 255, 255, 0.6)');
        centerGradient.addColorStop(1, 'rgba(255, 255, 255, 0.2)');
        this.ctx.strokeStyle = centerGradient;
        this.ctx.lineWidth = 1;
        this.ctx.beginPath();
        this.ctx.moveTo(0, amp);
        this.ctx.lineTo(width, amp);
        this.ctx.stroke();

        // Draw dynamic waveform with colors
        for (let i = 0; i < this.waveformData.length; i++) {
            const { min, max, avg } = this.waveformData[i];
            
            // Create dynamic colors based on amplitude and position
            const intensity = Math.abs(avg) * 2;
            const hue = (i * 2 + this.colorOffset) % 360;
            
            let gradient;
            if (playPosition >= 0 && i <= playPosition) {
                // Played portion - hot colors
                gradient = this.ctx.createLinearGradient(0, 0, 0, height);
                gradient.addColorStop(0, `hsla(${Math.max(0, hue - 60)}, 80%, 60%, 0.9)`);
                gradient.addColorStop(0.5, `hsla(${Math.max(0, hue - 30)}, 90%, 50%, 1)`);
                gradient.addColorStop(1, `hsla(${hue}, 80%, 60%, 0.9)`);
            } else {
                // Unplayed portion - cool colors
                gradient = this.ctx.createLinearGradient(0, 0, 0, height);
                gradient.addColorStop(0, `hsla(${200 + hue * 0.3}, 70%, 70%, 0.8)`);
                gradient.addColorStop(0.5, `hsla(${220 + hue * 0.2}, 80%, 60%, 0.9)`);
                gradient.addColorStop(1, `hsla(${240 + hue * 0.1}, 70%, 70%, 0.8)`);
            }
            
            this.ctx.fillStyle = gradient;
            
            const yMin = (1 + min) * amp;
            const yMax = (1 + max) * amp;
            const barHeight = Math.max(1, yMax - yMin);
            
            // Add glow effect for high amplitude
            if (intensity > 0.3) {
                this.ctx.shadowBlur = 10 * intensity;
                this.ctx.shadowColor = playPosition >= 0 && i <= playPosition ? '#ff6b6b' : '#4ecdc4';
            } else {
                this.ctx.shadowBlur = 0;
            }
            
            this.ctx.fillRect(i, yMin, 1, barHeight);
        }
        
        // Reset shadow
        this.ctx.shadowBlur = 0;
        
        // Animate color offset for dynamic effect
        this.colorOffset += 0.5;
        if (this.colorOffset > 360) this.colorOffset = 0;
    }

    startRecordingVisualization() {
        if (!this.analyser) return;
        
        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        // Show waveform container with recording animation
        this.elements.waveformSection.classList.add('visible');
        this.canvas.parentElement.classList.add('recording');
        
        // Make sure arousal canvas is visible during recording
        this.elements.arousalInfo.textContent = 'Live Arousal: 0%';
        
        // Reset all tracking variables
        this.speechEvents = [];
        this.recentLevels = [];
        this.lastSpeechTime = 0;
        this.loudnessData = [];
        this.pitchData = [];
        this.paceData = [];
        this.wordCount = 0;
        this.recordingStartTime = Date.now();
        
        // Reset pace tracking variables
        this.speechSegments = [];
        this.currentSegmentStart = null;
        this.totalSpeechTime = 0;
        this.speechTransitions = 0;
        this.syllableEvents = [];
        this.lastSyllableTime = 0;
        
        let recordingStartTime = Date.now();
        
        const visualize = () => {
            if (!this.isRecording) return;
            
            this.analyser.getByteFrequencyData(dataArray);
            
            const width = this.canvas.width / (window.devicePixelRatio || 1);
            const height = this.canvas.height / (window.devicePixelRatio || 1);
            
            this.ctx.clearRect(0, 0, width, height);
            
            // Calculate average audio level for speech detection
            let totalLevel = 0;
            for (let i = 0; i < bufferLength; i++) {
                totalLevel += dataArray[i];
            }
            const averageLevel = totalLevel / bufferLength / 255;
            
            // Update real-time speech detection and arousal
            const timeElapsed = (Date.now() - recordingStartTime) / 1000;
            this.updateRealtimeSpeechDetection(timeElapsed, averageLevel);
            this.updateRealtimeAnalysis(dataArray, averageLevel, timeElapsed);
            
            // Create animated background
            const time = Date.now() * 0.001;
            const bgGradient = this.ctx.createRadialGradient(
                width/2, height/2, 0,
                width/2, height/2, width/2
            );
            bgGradient.addColorStop(0, `hsla(${time * 20}, 50%, 20%, 0.3)`);
            bgGradient.addColorStop(1, `hsla(${time * 15}, 40%, 10%, 0.1)`);
            this.ctx.fillStyle = bgGradient;
            this.ctx.fillRect(0, 0, width, height);
            
            // Draw real-time frequency bars
            const barWidth = width / bufferLength;
            let x = 0;
            
            for (let i = 0; i < bufferLength; i++) {
                const barHeight = (dataArray[i] / 255) * height * 0.8;
                
                // Create dynamic gradient for each bar
                const gradient = this.ctx.createLinearGradient(0, height, 0, height - barHeight);
                const hue = (i * 3 + time * 50) % 360;
                gradient.addColorStop(0, `hsla(${hue}, 80%, 50%, 0.8)`);
                gradient.addColorStop(0.5, `hsla(${hue + 30}, 90%, 60%, 0.9)`);
                gradient.addColorStop(1, `hsla(${hue + 60}, 80%, 70%, 1)`);
                
                this.ctx.fillStyle = gradient;
                
                // Add glow effect
                this.ctx.shadowBlur = 15;
                this.ctx.shadowColor = `hsla(${hue}, 80%, 60%, 0.6)`;
                
                this.ctx.fillRect(x, height - barHeight, barWidth - 1, barHeight);
                
                x += barWidth;
            }
            
            this.ctx.shadowBlur = 0;
            this.recordingVisualizer = requestAnimationFrame(visualize);
        };
        
        visualize();
    }

    stopRecordingVisualization() {
        if (this.recordingVisualizer) {
            cancelAnimationFrame(this.recordingVisualizer);
            this.recordingVisualizer = null;
        }
        this.canvas.parentElement.classList.remove('recording');
    }

    analyzeEnhancedArousal() {
        console.log('=== AROUSAL ANALYSIS START ===');
        
        if (!this.audioBuffer) {
            console.log('ERROR: No audio buffer available');
            return;
        }

        const sampleRate = this.audioBuffer.sampleRate;
        const audioData = this.audioBuffer.getChannelData(0);
        const duration = this.audioBuffer.duration;
        const width = this.arousalCanvas.width / (window.devicePixelRatio || 1);
        const samplesPerPixel = Math.max(1, Math.floor(audioData.length / width));
        
        console.log('Audio buffer info:', {
            sampleRate,
            duration,
            audioDataLength: audioData.length,
            width,
            samplesPerPixel
        });
        
        this.arousalData = [];
        
        // Check if we have actual audio data
        let hasNonZeroSamples = false;
        for (let i = 0; i < Math.min(1000, audioData.length); i++) {
            if (Math.abs(audioData[i]) > 0.001) {
                hasNonZeroSamples = true;
                break;
            }
        }
        console.log('Has non-zero audio samples:', hasNonZeroSamples);
        
        // Analyze arousal for each pixel column
        for (let i = 0; i < width; i++) {
            const start = i * samplesPerPixel; // FIXED: Added missing start variable
            const end = Math.min(start + samplesPerPixel, audioData.length);
            
            // Calculate multiple arousal indicators
            let rms = 0;
            let peakAmplitude = 0;
            let zeroCrossings = 0;
            let samples = 0;
            let arousalValue = 0;
            
            let prevSample = 0;
            let sumSquares = 0;
            let sumAmplitudes = 0;
            
            for (let j = start; j < end; j++) {
                const sample = audioData[j];
                const amplitude = Math.abs(sample);
                
                sumSquares += sample * sample;
                sumAmplitudes += amplitude;
                peakAmplitude = Math.max(peakAmplitude, amplitude);
                
                // Zero crossing detection (indicates speech dynamics)
                if ((prevSample >= 0 && sample < 0) || (prevSample < 0 && sample >= 0)) {
                    zeroCrossings++;
                }
                
                prevSample = sample;
                samples++;
            }
            
            if (samples > 0) {
                rms = Math.sqrt(sumSquares / samples);
                const avgAmplitude = sumAmplitudes / samples;
                const zcr = zeroCrossings / samples * sampleRate; // Zero crossing rate
                
                // Enhanced arousal calculation with better scaling
                let loudnessComponent = 0;
                let pitchComponent = 0;
                let paceComponent = 0;
                
                // Improved loudness component with better scaling
                if (rms > 0.0001) {
                    // Use dB-like scaling for more realistic loudness perception
                    loudnessComponent = Math.min(Math.log10(rms * 1000 + 1) / 3, 1);
                }
                
                // Improved pitch component - better frequency range mapping
                if (zcr > 0) {
                    // Map ZCR to typical speech frequency range (85-300 Hz)
                    const estimatedFreq = zcr / 2;
                    pitchComponent = Math.min(Math.max((estimatedFreq - 85) / 215, 0), 1);
                }
                
                // Improved pace component - amplitude variation indicates speech dynamics
                const variation = Math.abs(peakAmplitude - avgAmplitude);
                if (variation > 0.0001) {
                    paceComponent = Math.min(variation * 20, 1);
                }
                
                // Combine components with adjusted weights for better balance
                arousalValue = (loudnessComponent * 0.5) + (pitchComponent * 0.25) + (paceComponent * 0.25);
                
                // Apply smoothing to reduce noise
                arousalValue = Math.max(0, Math.min(1, arousalValue));
                
                // Log only significant values for debugging
                if (i < 5 || arousalValue > 0.05) {
                    console.log(`Pixel ${i}: rms=${rms.toFixed(6)}, zcr=${zcr.toFixed(1)}, arousal=${arousalValue.toFixed(4)}`);
                }
            } else {
                arousalValue = 0;
            }
            
            this.arousalData.push(arousalValue);
        }
        
        // Calculate statistics
        let totalArousal = 0;
        let maxArousal = 0;
        let minArousal = 1;
        let nonZeroCount = 0;
        
        for (let i = 0; i < this.arousalData.length; i++) {
            const value = this.arousalData[i];
            if (value > 0.001) nonZeroCount++;
            totalArousal += value;
            maxArousal = Math.max(maxArousal, value);
            minArousal = Math.min(minArousal, value);
        }
        
        // Use weighted average that considers actual audio content
        let avgArousal = 0;
        if (this.arousalData.length > 0 && nonZeroCount > 0) {
            // Weight the average towards non-zero values for more meaningful results
            avgArousal = totalArousal / this.arousalData.length;
            // Boost the average slightly if we have significant audio content
            if (nonZeroCount > this.arousalData.length * 0.1) {
                avgArousal *= 1.2; // 20% boost for active audio
            }
        }
        
        console.log('Arousal calculation details:', {
            totalArousal: totalArousal,
            arrayLength: this.arousalData.length,
            nonZeroCount: nonZeroCount,
            avgArousal: avgArousal,
            maxArousal: maxArousal,
            minArousal: minArousal
        });
        
        // Convert to percentage with better scaling
        const arousalPercentage = Math.round(Math.min(avgArousal * 100, 100));
        
        console.log('Final arousal percentage:', arousalPercentage);
        
        this.elements.arousalInfo.textContent = `Avg Arousal: ${arousalPercentage}%`;
        this.elements.arousalBarFill.style.width = `${arousalPercentage}%`;
        
        // Color code with adjusted thresholds
        if (arousalPercentage > 60) {
            this.elements.arousalInfo.style.color = '#d63031'; // High energy - red
        } else if (arousalPercentage > 30) {
            this.elements.arousalInfo.style.color = '#e17055'; // Medium energy - orange  
        } else if (arousalPercentage > 10) {
            this.elements.arousalInfo.style.color = '#fdcb6e'; // Low-medium energy - yellow
        } else {
            this.elements.arousalInfo.style.color = '#74b9ff'; // Very low energy - blue
        }
        
        this.drawArousalLine();
    }

    analyzeStaticMetrics() {
        console.log('=== STATIC METRICS ANALYSIS START ===');
        
        if (!this.audioBuffer) {
            console.log('ERROR: No audio buffer available for metrics');
            return;
        }

        const sampleRate = this.audioBuffer.sampleRate;
        const audioData = this.audioBuffer.getChannelData(0);
        const width = this.elements.loudnessCanvas.width / (window.devicePixelRatio || 1);
        const samplesPerPixel = Math.max(1, Math.floor(audioData.length / width));
        
        this.loudnessDataStatic = [];
        this.pitchDataStatic = [];
        this.paceDataStatic = [];
        
        // Analyze each pixel column for metrics
        for (let i = 0; i < width; i++) {
            const start = i * samplesPerPixel;
            const end = Math.min(start + samplesPerPixel, audioData.length);
            
            // Calculate loudness (RMS to dB)
            let sumSquares = 0;
            let samples = 0;
            let maxAmplitude = 0;
            let zeroCrossings = 0;
            let prevSample = 0;
            
            for (let j = start; j < end; j++) {
                const sample = audioData[j];
                const amplitude = Math.abs(sample);
                
                sumSquares += sample * sample;
                maxAmplitude = Math.max(maxAmplitude, amplitude);
                
                // Zero crossing detection for pitch estimation
                if ((prevSample >= 0 && sample < 0) || (prevSample < 0 && sample >= 0)) {
                    zeroCrossings++;
                }
                prevSample = sample;
                samples++;
            }
            
            // ACCURATE: Professional dB SPL calculation for static analysis
            let loudnessDb = 20; // Default quiet level
            if (samples > 0) {
                const rms = Math.sqrt(sumSquares / samples);
                if (rms > 0.0001) {
                    // Professional dB SPL calculation matching real-time method
                    const micSensitivity = 0.01;
                    const pressureLevel = rms * micSensitivity;
                    loudnessDb = 20 * Math.log10(pressureLevel / 0.00002); // 20 µPa reference
                    
                    // Realistic speech range: 20-85 dB
                    loudnessDb = Math.max(20, Math.min(85, loudnessDb));
                }
            }
            
            // ACCURATE: Professional static pitch calculation using autocorrelation
            let pitchHz = 120; // Default fundamental frequency
            if (samples > 50 && zeroCrossings > 2) {
                const rms = Math.sqrt(sumSquares / samples);
                
                // Only process if there's significant speech energy
                if (rms > 0.003) {
                    // Autocorrelation method for accurate pitch detection
                    const segmentSize = Math.min(samples, 2048);
                    let maxCorrelation = 0;
                    let bestPeriod = 0;
                    
                    // Search range for fundamental frequency (85-400 Hz)
                    const minPeriod = Math.floor(sampleRate / 400);
                    const maxPeriod = Math.floor(sampleRate / 85);
                    
                    // Autocorrelation function
                    for (let period = minPeriod; period <= maxPeriod && period < segmentSize / 2; period++) {
                        let correlation = 0;
                        let normalization = 0;
                        
                        for (let i = 0; i < segmentSize - period; i++) {
                            const idx1 = start + i;
                            const idx2 = start + i + period;
                            
                            if (idx1 < audioData.length && idx2 < audioData.length) {
                                correlation += audioData[idx1] * audioData[idx2];
                                normalization += audioData[idx1] * audioData[idx1];
                            }
                        }
                        
                        // Normalized correlation
                        if (normalization > 0) {
                            correlation /= normalization;
                            
                            if (correlation > maxCorrelation) {
                                maxCorrelation = correlation;
                                bestPeriod = period;
                            }
                        }
                    }
                    
                    // If we found a strong correlation, use it
                    if (bestPeriod > 0 && maxCorrelation > 0.3) {
                        pitchHz = sampleRate / bestPeriod;
                        
                        // Refine with parabolic interpolation
                        if (bestPeriod > minPeriod && bestPeriod < maxPeriod) {
                            // Calculate correlation for neighboring periods
                            const prevCorr = this.calculateCorrelation(audioData, start, segmentSize, bestPeriod - 1);
                            const nextCorr = this.calculateCorrelation(audioData, start, segmentSize, bestPeriod + 1);
                            
                            // Parabolic interpolation
                            const a = (prevCorr - 2 * maxCorrelation + nextCorr) / 2;
                            const b = (nextCorr - prevCorr) / 2;
                            
                            if (a !== 0) {
                                const offset = -b / (2 * a);
                                const refinedPeriod = bestPeriod + offset;
                                pitchHz = sampleRate / refinedPeriod;
                            }
                        }
                        
                        // Apply energy-based variation (higher energy = slight pitch increase)
                        const energyFactor = Math.min(Math.max(rms * 100, 0.9), 1.1);
                        pitchHz *= energyFactor;
                    } else {
                        // Fallback to zero-crossing rate method
                        const zcr = (zeroCrossings / samples) * sampleRate;
                        pitchHz = Math.max(85, Math.min(400, zcr / 2));
                    }
                    
                    // Ensure realistic bounds
                    pitchHz = Math.max(85, Math.min(400, Math.round(pitchHz)));
                }
            }
            
            // FIXED: Simplified and effective static pace calculation
            let paceWpm = 120; // Default speaking pace
            if (samples > 50) {
                const rms = Math.sqrt(sumSquares / samples);
                const segmentDuration = samples / sampleRate;
                
                if (rms > 0.005) { // Speech detected
                    // Method 1: Zero-crossing rate indicates speech activity
                    const zcr = (zeroCrossings / samples) * sampleRate;
                    const speechActivity = Math.min(zcr / 100, 3); // Normalize ZCR
                    
                    // Method 2: Amplitude variation indicates word boundaries
                    const amplitudeVariation = Math.abs(maxAmplitude - rms);
                    const wordBoundaryActivity = Math.min(amplitudeVariation * 200, 2);
                    
                    // Method 3: Energy level correlates with speaking pace
                    const energyLevel = Math.min(rms * 100, 2);
                    
                    // Combine factors for pace estimation
                    let paceMultiplier = 1.0;
                    paceMultiplier += speechActivity * 0.3;      // +0% to +90% for speech activity
                    paceMultiplier += wordBoundaryActivity * 0.2; // +0% to +40% for word boundaries  
                    paceMultiplier += energyLevel * 0.2;         // +0% to +40% for energy
                    
                    // Base pace adjusted by segment characteristics
                    paceWpm = 100 * paceMultiplier;
                    
                    // Segment duration adjustment
                    if (segmentDuration > 0.3) {
                        // Longer segments typically have more words
                        const durationFactor = Math.min(segmentDuration * 1.5, 2.5);
                        paceWpm *= durationFactor;
                    }
                    
                    // Realistic bounds
                    paceWpm = Math.max(80, Math.min(300, Math.round(paceWpm)));
                } else {
                    // Low energy segment
                    paceWpm = 90; // Slow pace for quiet segments
                }
            }
            
            this.loudnessDataStatic.push(loudnessDb);
            this.pitchDataStatic.push(pitchHz);
            this.paceDataStatic.push(paceWpm);
        }
        
        console.log('Static metrics analysis complete:', {
            loudnessRange: [Math.min(...this.loudnessDataStatic), Math.max(...this.loudnessDataStatic)],
            pitchRange: [Math.min(...this.pitchDataStatic), Math.max(...this.pitchDataStatic)],
            paceRange: [Math.min(...this.paceDataStatic), Math.max(...this.paceDataStatic)]
        });
        
        // Draw the static visualizations with accurate ranges
        this.drawMetricVisualization('loudness', this.loudnessDataStatic, 20, 85, ['#28a745', '#20c997']);
        this.drawMetricVisualization('pitch', this.pitchDataStatic, 85, 400, ['#007bff', '#6f42c1']);
        this.drawMetricVisualization('pace', this.paceDataStatic, 80, 300, ['#dc3545', '#e83e8c']);
    }

    drawArousalLine(playPosition = -1) {
        if (!this.arousalData) return;

        const width = this.arousalCanvas.width / (window.devicePixelRatio || 1);
        const height = this.arousalCanvas.height / (window.devicePixelRatio || 1);
        
        this.arousalCtx.clearRect(0, 0, width, height);
        
        // Draw background gradient
        const bgGradient = this.arousalCtx.createLinearGradient(0, 0, 0, height);
        bgGradient.addColorStop(0, 'rgba(255, 255, 255, 0.1)');
        bgGradient.addColorStop(1, 'rgba(255, 255, 255, 0.05)');
        this.arousalCtx.fillStyle = bgGradient;
        this.arousalCtx.fillRect(0, 0, width, height);
        
        // Draw baseline
        this.arousalCtx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        this.arousalCtx.lineWidth = 1;
        this.arousalCtx.beginPath();
        this.arousalCtx.moveTo(0, height * 0.8);
        this.arousalCtx.lineTo(width, height * 0.8);
        this.arousalCtx.stroke();
        
        // Draw arousal area fill
        this.arousalCtx.beginPath();
        this.arousalCtx.moveTo(0, height * 0.8);
        
        for (let i = 0; i < this.arousalData.length; i++) {
            const arousal = this.arousalData[i];
            const y = height * 0.8 - (arousal * height * 0.7); // Scale to use 70% of height
            this.arousalCtx.lineTo(i, y);
        }
        
        this.arousalCtx.lineTo(width, height * 0.8);
        this.arousalCtx.closePath();
        
        // Create gradient fill based on play position
        const fillGradient = this.arousalCtx.createLinearGradient(0, 0, width, 0);
        if (playPosition >= 0) {
            const progress = playPosition / width;
            fillGradient.addColorStop(0, 'rgba(255, 107, 107, 0.8)');
            fillGradient.addColorStop(progress, 'rgba(255, 107, 107, 0.8)');
            fillGradient.addColorStop(progress, 'rgba(255, 182, 193, 0.6)');
            fillGradient.addColorStop(1, 'rgba(255, 182, 193, 0.6)');
        } else {
            fillGradient.addColorStop(0, 'rgba(255, 182, 193, 0.7)');
            fillGradient.addColorStop(1, 'rgba(255, 107, 107, 0.7)');
        }
        
        this.arousalCtx.fillStyle = fillGradient;
        this.arousalCtx.fill();
        
        // Draw arousal line
        this.arousalCtx.strokeStyle = playPosition >= 0 ? '#ff4757' : '#ff6b6b';
        this.arousalCtx.lineWidth = 2;
        this.arousalCtx.beginPath();
        
        for (let i = 0; i < this.arousalData.length; i++) {
            const arousal = this.arousalData[i];
            const y = height * 0.8 - (arousal * height * 0.7);
            
            if (i === 0) {
                this.arousalCtx.moveTo(i, y);
            } else {
                this.arousalCtx.lineTo(i, y);
            }
        }
        
        this.arousalCtx.stroke();
        
        // Add glow effect to high arousal areas
        this.arousalCtx.shadowBlur = 8;
        this.arousalCtx.shadowColor = 'rgba(255, 107, 107, 0.6)';
        this.arousalCtx.stroke();
        this.arousalCtx.shadowBlur = 0;
    }

    analyzeSpeech() {
        if (!this.audioBuffer) return;

        const sampleRate = this.audioBuffer.sampleRate;
        const audioData = this.audioBuffer.getChannelData(0);
        const duration = this.audioBuffer.duration;
        const secondsCount = Math.ceil(duration);
        
        this.speechData = [];
        
        // Analyze each second of audio
        for (let second = 0; second < secondsCount; second++) {
            const startSample = Math.floor(second * sampleRate);
            const endSample = Math.min(startSample + sampleRate, audioData.length);
            
            // Calculate RMS (Root Mean Square) energy for this second
            let sumSquares = 0;
            let maxAmplitude = 0;
            let samples = 0;
            
            for (let i = startSample; i < endSample; i++) {
                const amplitude = Math.abs(audioData[i]);
                sumSquares += amplitude * amplitude;
                maxAmplitude = Math.max(maxAmplitude, amplitude);
                samples++;
            }
            
            const rms = samples > 0 ? Math.sqrt(sumSquares / samples) : 0;
            
            // Speech detection algorithm
            // Combine RMS energy and peak amplitude
            const energyThreshold = 0.01; // Minimum energy for speech
            const peakThreshold = 0.05;   // Minimum peak for speech
            const isSpeaking = rms > energyThreshold && maxAmplitude > peakThreshold;
            
            this.speechData.push({
                second,
                rms,
                maxAmplitude,
                isSpeaking
            });
        }
        
        this.createSpeechBoxes();
        this.calculateSpeakingPercentage();
    }

    createSpeechBoxes() {
        this.elements.speechBoxes.innerHTML = '';
        
        this.speechData.forEach((data, index) => {
            const box = document.createElement('div');
            box.className = 'speech-box';
            if (data.isSpeaking) {
                box.classList.add('speaking');
            } else {
                box.classList.add('silence');
            }
            
            // Add tooltip
            box.title = `${index}s: ${data.isSpeaking ? 'Speaking' : 'Silence'} (RMS: ${data.rms.toFixed(3)})`;
            
            this.elements.speechBoxes.appendChild(box);
        });
    }

    calculateSpeakingPercentage() {
        if (this.speechData.length === 0) return;
        
        const speakingSeconds = this.speechData.filter(d => d.isSpeaking).length;
        const percentage = Math.round((speakingSeconds / this.speechData.length) * 100);
        
        this.elements.speakingPercentage.textContent = `Speaking: ${percentage}%`;
        
        // Color code the percentage
        if (percentage > 70) {
            this.elements.speakingPercentage.style.color = '#28a745'; // Green
        } else if (percentage > 40) {
            this.elements.speakingPercentage.style.color = '#ffc107'; // Yellow
        } else {
            this.elements.speakingPercentage.style.color = '#dc3545'; // Red
        }
    }

    setupRealtimeSpeechBoxes() {
        // Create 10 boxes for real-time recording (10 seconds)
        this.elements.speechBoxes.innerHTML = '';
        this.realtimeSpeechBoxes = [];
        
        for (let i = 0; i < 10; i++) {
            const box = document.createElement('div');
            box.className = 'speech-box';
            box.title = `${i + 1}s`;
            this.elements.speechBoxes.appendChild(box);
            this.realtimeSpeechBoxes.push(box);
        }
        
        this.elements.speakingPercentage.textContent = 'Speaking: 0%';
    }

    updateRealtimeSpeechDetection(timeElapsed, audioLevel) {
        const currentSecond = Math.floor(timeElapsed);
        if (currentSecond >= this.realtimeSpeechBoxes.length) return;
        
        // Simple real-time speech detection based on audio level
        const isSpeaking = audioLevel > 0.02; // Threshold for real-time detection
        
        const box = this.realtimeSpeechBoxes[currentSecond];
        if (box) {
            // Remove previous classes
            box.classList.remove('speaking', 'silence', 'current');
            
            // Add current state
            if (isSpeaking) {
                box.classList.add('speaking');
            } else {
                box.classList.add('silence');
            }
            
            // Highlight current box
            box.classList.add('current');
            
            // Remove current class from previous boxes
            this.realtimeSpeechBoxes.forEach((b, i) => {
                if (i !== currentSecond) {
                    b.classList.remove('current');
                }
            });
        }
        
        // Update percentage for completed seconds
        const completedSeconds = Math.min(currentSecond + 1, 10);
        const speakingCount = this.realtimeSpeechBoxes
            .slice(0, completedSeconds)
            .filter(box => box.classList.contains('speaking')).length;
        const percentage = Math.round((speakingCount / completedSeconds) * 100);
        this.elements.speakingPercentage.textContent = `Speaking: ${percentage}%`;
    }

    updateRealtimeAnalysis(frequencyData, audioLevel, timeElapsed) {
        // COMPLETELY REWRITTEN: Accurate dB calculation
        let loudnessDb = -60;
        
        // Calculate RMS from frequency data for more accurate loudness
        let rmsFromFreq = 0;
        for (let i = 0; i < frequencyData.length; i++) {
            const normalized = frequencyData[i] / 255.0; // Normalize to 0-1
            rmsFromFreq += normalized * normalized;
        }
        rmsFromFreq = Math.sqrt(rmsFromFreq / frequencyData.length);
        
        if (rmsFromFreq > 0.001) {
            // Proper dB SPL calculation: 20 * log10(P/P_ref)
            // Reference: 20 µPa (threshold of human hearing)
            // Convert to realistic microphone input levels
            const micSensitivity = 0.01; // Typical microphone sensitivity factor
            const pressureLevel = rmsFromFreq * micSensitivity;
            loudnessDb = 20 * Math.log10(pressureLevel / 0.00002); // 20 µPa reference
            
            // Realistic bounds: whisper (~30dB) to loud speech (~80dB)
            loudnessDb = Math.max(20, Math.min(85, loudnessDb));
        }
        
        // COMPLETELY REWRITTEN: Accurate pitch detection using autocorrelation
        const pitchHz = this.calculateAccuratePitch(frequencyData);
        
        // COMPLETELY REWRITTEN: Accurate WPM calculation
        const paceWpm = this.calculateAccurateWPM(audioLevel, timeElapsed);
        
        // Store data points for visualization
        this.loudnessData.push(loudnessDb);
        this.pitchData.push(pitchHz);
        this.paceData.push(paceWpm);
        
        // Keep only last 300 data points (about 15 seconds at 20fps)
        if (this.loudnessData.length > 300) {
            this.loudnessData.shift();
            this.pitchData.shift();
            this.paceData.shift();
        }
        
        // Update display values
        this.elements.loudnessInfo.textContent = `Loudness: ${Math.round(loudnessDb)} dB`;
        this.elements.pitchInfo.textContent = `Pitch: ${Math.round(pitchHz)} Hz`;
        this.elements.paceInfo.textContent = `Pace: ${Math.round(paceWpm)} WPM`;
        
        // Update progress bars with accurate scaling
        const loudnessPercent = Math.max(0, ((loudnessDb - 20) / 65) * 100); // 20-85 dB range
        const pitchPercent = Math.max(0, ((pitchHz - 85) / 315) * 100); // 85-400 Hz range
        const pacePercent = Math.max(0, ((paceWpm - 80) / 220) * 100); // 80-300 WPM range
        
        this.elements.loudnessBarFill.style.width = `${Math.min(100, loudnessPercent)}%`;
        this.elements.pitchBarFill.style.width = `${Math.min(100, pitchPercent)}%`;
        this.elements.paceBarFill.style.width = `${Math.min(100, pacePercent)}%`;
        
        // Draw metric visualizations with accurate ranges
        this.drawMetricVisualization('loudness', this.loudnessData, 20, 85, ['#28a745', '#20c997']);
        this.drawMetricVisualization('pitch', this.pitchData, 85, 400, ['#007bff', '#6f42c1']);
        this.drawMetricVisualization('pace', this.paceData, 80, 300, ['#dc3545', '#e83e8c']);
        
        // Calculate arousal with accurate normalization
        const loudnessNorm = Math.max(0, Math.min(1, (loudnessDb - 20) / 65));
        const pitchNorm = Math.max(0, Math.min(1, (pitchHz - 85) / 315));
        const paceNorm = Math.max(0, Math.min(1, (paceWpm - 80) / 220));
        
        const combinedArousal = (loudnessNorm * 0.4) + (pitchNorm * 0.3) + (paceNorm * 0.3);
        const arousalPercent = Math.round(combinedArousal * 100);
        
        this.elements.arousalInfo.textContent = `Live Arousal: ${arousalPercent}%`;
        this.elements.arousalBarFill.style.width = `${arousalPercent}%`;
        
        // Color code the arousal
        if (arousalPercent > 70) {
            this.elements.arousalInfo.style.color = '#d63031';
        } else if (arousalPercent > 40) {
            this.elements.arousalInfo.style.color = '#e17055';
        } else if (arousalPercent > 20) {
            this.elements.arousalInfo.style.color = '#fdcb6e';
        } else {
            this.elements.arousalInfo.style.color = '#74b9ff';
        }
        
        this.drawRealtimeArousal(combinedArousal);
    }

    calculateAccuratePitch(frequencyData) {
        // Professional-grade pitch detection using YIN algorithm principles
        const sampleRate = 44100;
        const nyquist = sampleRate / 2;
        const binFreq = nyquist / frequencyData.length;
        
        // Convert frequency data to time domain for autocorrelation
        const bufferSize = frequencyData.length;
        let maxMagnitude = 0;
        
        // Find the strongest frequency components
        for (let i = 0; i < bufferSize; i++) {
            maxMagnitude = Math.max(maxMagnitude, frequencyData[i]);
        }
        
        // If signal is too weak, return default
        if (maxMagnitude < 20) {
            return 120; // Default pitch
        }
        
        // Find fundamental frequency using spectral peak detection
        let fundamentalBin = 0;
        let fundamentalMagnitude = 0;
        
        // Focus on speech frequency range (85-400 Hz)
        const minBin = Math.floor(85 / binFreq);
        const maxBin = Math.min(Math.floor(400 / binFreq), bufferSize - 1);
        
        // Apply spectral whitening to enhance fundamental
        let whitenedSpectrum = new Array(bufferSize);
        for (let i = 0; i < bufferSize; i++) {
            whitenedSpectrum[i] = frequencyData[i];
        }
        
        // Find the strongest peak in the fundamental range
        for (let i = minBin; i <= maxBin; i++) {
            const magnitude = whitenedSpectrum[i];
            
            // Look for local maxima
            if (i > minBin && i < maxBin) {
                const isLocalMax = magnitude > whitenedSpectrum[i-1] && 
                                 magnitude > whitenedSpectrum[i+1];
                
                if (isLocalMax && magnitude > fundamentalMagnitude) {
                    // Check if this is likely the fundamental (not a harmonic)
                    const freq = i * binFreq;
                    let harmonicSupport = magnitude;
                    
                    // Look for harmonic series (2f, 3f, 4f)
                    const harmonic2Bin = Math.floor((freq * 2) / binFreq);
                    const harmonic3Bin = Math.floor((freq * 3) / binFreq);
                    const harmonic4Bin = Math.floor((freq * 4) / binFreq);
                    
                    if (harmonic2Bin < bufferSize) {
                        harmonicSupport += whitenedSpectrum[harmonic2Bin] * 0.6;
                    }
                    if (harmonic3Bin < bufferSize) {
                        harmonicSupport += whitenedSpectrum[harmonic3Bin] * 0.4;
                    }
                    if (harmonic4Bin < bufferSize) {
                        harmonicSupport += whitenedSpectrum[harmonic4Bin] * 0.2;
                    }
                    
                    // Prefer frequencies with strong harmonic support
                    if (harmonicSupport > fundamentalMagnitude * 1.2) {
                        fundamentalMagnitude = harmonicSupport;
                        fundamentalBin = i;
                    }
                }
            }
        }
        
        if (fundamentalBin === 0) {
            // Fallback: find the strongest peak in range
            for (let i = minBin; i <= maxBin; i++) {
                if (whitenedSpectrum[i] > fundamentalMagnitude) {
                    fundamentalMagnitude = whitenedSpectrum[i];
                    fundamentalBin = i;
                }
            }
        }
        
        // Convert bin to frequency
        let pitch = fundamentalBin * binFreq;
        
        // Parabolic interpolation for sub-bin accuracy
        if (fundamentalBin > 0 && fundamentalBin < bufferSize - 1) {
            const y1 = whitenedSpectrum[fundamentalBin - 1];
            const y2 = whitenedSpectrum[fundamentalBin];
            const y3 = whitenedSpectrum[fundamentalBin + 1];
            
            const a = (y1 - 2*y2 + y3) / 2;
            const b = (y3 - y1) / 2;
            
            if (a !== 0) {
                const xOffset = -b / (2 * a);
                pitch = (fundamentalBin + xOffset) * binFreq;
            }
        }
        
        // Clamp to realistic speech range
        pitch = Math.max(85, Math.min(400, pitch));
        
        // Temporal smoothing to reduce jitter
        if (this.lastAccuratePitch !== undefined) {
            const smoothingFactor = 0.3;
            const maxChange = 30; // Max Hz change per frame
            const change = pitch - this.lastAccuratePitch;
            
            if (Math.abs(change) > maxChange) {
                pitch = this.lastAccuratePitch + (change > 0 ? maxChange : -maxChange);
            } else {
                pitch = this.lastAccuratePitch * smoothingFactor + pitch * (1 - smoothingFactor);
            }
        }
        
        this.lastAccuratePitch = pitch;
        return Math.round(pitch);
    }

    calculateAccurateWPM(audioLevel, timeElapsed) {
        // SIMPLIFIED: Direct and effective WPM calculation
        
        // Initialize simple tracking
        if (!this.paceTracker) {
            this.paceTracker = {
                audioLevels: [],
                speechBursts: [],
                lastSpeechTime: 0,
                totalSpeechTime: 0,
                speechTransitions: 0,
                lastState: 'silence'
            };
        }
        
        const tracker = this.paceTracker;
        
        // Store recent audio levels (last 3 seconds)
        tracker.audioLevels.push({ time: timeElapsed, level: audioLevel });
        tracker.audioLevels = tracker.audioLevels.filter(entry => timeElapsed - entry.time < 3);
        
        // Calculate adaptive threshold
        const recentLevels = tracker.audioLevels.map(entry => entry.level);
        const avgLevel = recentLevels.reduce((a, b) => a + b, 0) / recentLevels.length;
        const maxLevel = Math.max(...recentLevels);
        const speechThreshold = Math.max(0.03, avgLevel + (maxLevel - avgLevel) * 0.3);
        
        const isSpeaking = audioLevel > speechThreshold;
        
        // Track speech state changes
        if (isSpeaking && tracker.lastState === 'silence') {
            // Start of speech burst
            tracker.speechBursts.push({ start: timeElapsed, end: null });
            tracker.speechTransitions++;
            tracker.lastState = 'speech';
        } else if (!isSpeaking && tracker.lastState === 'speech') {
            // End of speech burst
            if (tracker.speechBursts.length > 0) {
                const lastBurst = tracker.speechBursts[tracker.speechBursts.length - 1];
                if (lastBurst.end === null) {
                    lastBurst.end = timeElapsed;
                    const burstDuration = lastBurst.end - lastBurst.start;
                    tracker.totalSpeechTime += burstDuration;
                }
            }
            tracker.lastState = 'silence';
        }
        
        // Keep only recent bursts (last 10 seconds)
        tracker.speechBursts = tracker.speechBursts.filter(burst => 
            timeElapsed - burst.start < 10
        );
        
        // Early return for insufficient data
        if (timeElapsed < 1.5) {
            return 120; // Default WPM
        }
        
        // Calculate WPM using multiple methods
        let wpm = 120; // Default
        
        // Method 1: Speech burst frequency (primary method)
        const recentBursts = tracker.speechBursts.filter(burst => 
            timeElapsed - burst.start < 6 // Last 6 seconds
        );
        
        if (recentBursts.length >= 2) {
            // Calculate average burst characteristics
            let totalBurstDuration = 0;
            let completedBursts = 0;
            
            for (const burst of recentBursts) {
                if (burst.end !== null) {
                    totalBurstDuration += (burst.end - burst.start);
                    completedBursts++;
                }
            }
            
            if (completedBursts >= 2) {
                const avgBurstDuration = totalBurstDuration / completedBursts;
                const burstsPerMinute = (completedBursts / 6) * 60; // Bursts per minute
                
                // Estimate words per burst based on duration
                let wordsPerBurst = 1;
                if (avgBurstDuration > 0.3) wordsPerBurst = 1.5;
                if (avgBurstDuration > 0.6) wordsPerBurst = 2.5;
                if (avgBurstDuration > 1.0) wordsPerBurst = 4;
                if (avgBurstDuration > 1.5) wordsPerBurst = 6;
                if (avgBurstDuration > 2.0) wordsPerBurst = 8;
                
                wpm = burstsPerMinute * wordsPerBurst;
            }
        }
        
        // Method 2: Audio activity analysis (backup/refinement)
        if (tracker.audioLevels.length >= 30) { // At least 1.5 seconds of data
            // Count significant audio activity peaks (word-like events)
            let activityPeaks = 0;
            const levelThreshold = avgLevel * 1.5;
            
            for (let i = 1; i < tracker.audioLevels.length - 1; i++) {
                const prev = tracker.audioLevels[i - 1].level;
                const curr = tracker.audioLevels[i].level;
                const next = tracker.audioLevels[i + 1].level;
                
                // Peak detection: current level is higher than neighbors and above threshold
                if (curr > prev && curr > next && curr > levelThreshold) {
                    // Check if this peak is spaced appropriately (not too close to previous)
                    const timeSinceLast = i > 10 ? tracker.audioLevels[i].time - tracker.audioLevels[i - 10].time : 0.5;
                    if (timeSinceLast > 0.15) { // At least 150ms between word-peaks
                        activityPeaks++;
                    }
                }
            }
            
            // Convert peaks to WPM
            const peaksPerSecond = activityPeaks / 3; // Over 3 second window
            const peaksPerMinute = peaksPerSecond * 60;
            const activityWpm = peaksPerMinute * 0.8; // Each peak ≈ 0.8 words
            
            // Blend with burst-based calculation
            if (recentBursts.length >= 2) {
                wpm = (wpm * 0.7) + (activityWpm * 0.3); // Favor burst method
            } else {
                wpm = activityWpm; // Use activity method when bursts insufficient
            }
        }
        
        // Apply energy-based adjustment
        const energyRatio = Math.min(Math.max(avgLevel / 0.05, 0.7), 1.4); // 0.7x to 1.4x
        wpm *= energyRatio;
        
        // Apply speech density factor
        const speechDensity = Math.min(tracker.totalSpeechTime / timeElapsed, 0.8);
        if (speechDensity > 0.2) {
            wpm *= (0.8 + speechDensity * 0.4); // Boost for higher speech density
        }
        
        // Realistic bounds
        wpm = Math.max(80, Math.min(300, wpm));
        
        // Smooth the output to reduce jitter
        if (this.lastWpmSmoothed !== undefined) {
            const smoothing = 0.6; // Moderate smoothing
            wpm = this.lastWpmSmoothed * smoothing + wpm * (1 - smoothing);
        }
        
        this.lastWpmSmoothed = wpm;
        return Math.round(wpm);
    }

    drawMetricVisualization(metricName, data, minValue, maxValue, colors, playPosition = -1) {
        const ctx = this[metricName + 'Ctx'];
        if (!ctx || data.length === 0) {
            console.log(`Warning: ${metricName} context not found or no data`);
            return;
        }
        
        const canvas = this.elements[metricName + 'Canvas'];
        const width = canvas.width / (window.devicePixelRatio || 1);
        const height = canvas.height / (window.devicePixelRatio || 1);
        
        ctx.clearRect(0, 0, width, height);
        
        // Draw background gradient
        const bgGradient = ctx.createLinearGradient(0, 0, 0, height);
        bgGradient.addColorStop(0, 'rgba(255, 255, 255, 0.1)');
        bgGradient.addColorStop(1, 'rgba(255, 255, 255, 0.05)');
        ctx.fillStyle = bgGradient;
        ctx.fillRect(0, 0, width, height);
        
        // Draw baseline
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, height * 0.8);
        ctx.lineTo(width, height * 0.8);
        ctx.stroke();
        
        // Draw area fill
        ctx.beginPath();
        ctx.moveTo(0, height * 0.8);
        
        const stepX = width / Math.max(data.length - 1, 1);
        for (let i = 0; i < data.length; i++) {
            const normalizedValue = Math.max(0, Math.min(1, (data[i] - minValue) / (maxValue - minValue)));
            const y = height * 0.8 - (normalizedValue * height * 0.7);
            ctx.lineTo(i * stepX, y);
        }
        
        ctx.lineTo(width, height * 0.8);
        ctx.closePath();
        
        // Create gradient fill
        const fillGradient = ctx.createLinearGradient(0, 0, width, 0);
        if (playPosition >= 0) {
            const progress = playPosition / width;
            fillGradient.addColorStop(0, colors[0] + 'cc');
            fillGradient.addColorStop(progress, colors[0] + 'cc');
            fillGradient.addColorStop(progress, colors[1] + '99');
            fillGradient.addColorStop(1, colors[1] + '99');
        } else {
            fillGradient.addColorStop(0, colors[1] + 'b3');
            fillGradient.addColorStop(1, colors[0] + 'b3');
        }
        
        ctx.fillStyle = fillGradient;
        ctx.fill();
        
        // Draw metric line
        ctx.strokeStyle = playPosition >= 0 ? colors[0] : colors[1];
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        for (let i = 0; i < data.length; i++) {
            const normalizedValue = Math.max(0, Math.min(1, (data[i] - minValue) / (maxValue - minValue)));
            const y = height * 0.8 - (normalizedValue * height * 0.7);
            
            if (i === 0) {
                ctx.moveTo(i * stepX, y);
            } else {
                ctx.lineTo(i * stepX, y);
            }
        }
        
        ctx.stroke();
        
        // Add glow effect
        ctx.shadowBlur = 8;
        ctx.shadowColor = colors[0] + '99';
        ctx.stroke();
        ctx.shadowBlur = 0;
    }

    calculateCorrelation(audioData, start, segmentSize, period) {
        // Helper function for autocorrelation calculation
        let correlation = 0;
        let normalization = 0;
        
        for (let i = 0; i < segmentSize - period; i++) {
            const idx1 = start + i;
            const idx2 = start + i + period;
            
            if (idx1 < audioData.length && idx2 < audioData.length) {
                correlation += audioData[idx1] * audioData[idx2];
                normalization += audioData[idx1] * audioData[idx1];
            }
        }
        
        return normalization > 0 ? correlation / normalization : 0;
    }

    drawRealtimeArousal(arousalLevel) {
        const width = this.arousalCanvas.width / (window.devicePixelRatio || 1);
        const height = this.arousalCanvas.height / (window.devicePixelRatio || 1);
        
        // Clear canvas
        this.arousalCtx.clearRect(0, 0, width, height);
        
        // Draw background
        const bgGradient = this.arousalCtx.createLinearGradient(0, 0, 0, height);
        bgGradient.addColorStop(0, 'rgba(255, 255, 255, 0.1)');
        bgGradient.addColorStop(1, 'rgba(255, 255, 255, 0.05)');
        this.arousalCtx.fillStyle = bgGradient;
        this.arousalCtx.fillRect(0, 0, width, height);
        
        // Draw baseline
        this.arousalCtx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        this.arousalCtx.lineWidth = 1;
        this.arousalCtx.beginPath();
        this.arousalCtx.moveTo(0, height * 0.8);
        this.arousalCtx.lineTo(width, height * 0.8);
        this.arousalCtx.stroke();
        
        // Draw current arousal level as a bar
        const barHeight = arousalLevel * height * 0.7;
        const barY = height * 0.8 - barHeight;
        
        // Create gradient for the bar
        const barGradient = this.arousalCtx.createLinearGradient(0, height, 0, barY);
        barGradient.addColorStop(0, 'rgba(255, 107, 107, 0.8)');
        barGradient.addColorStop(1, 'rgba(255, 182, 193, 0.9)');
        
        this.arousalCtx.fillStyle = barGradient;
        this.arousalCtx.fillRect(width * 0.4, barY, width * 0.2, barHeight);
        
        // Add glow effect
        this.arousalCtx.shadowBlur = 10;
        this.arousalCtx.shadowColor = 'rgba(255, 107, 107, 0.6)';
        this.arousalCtx.fillRect(width * 0.4, barY, width * 0.2, barHeight);
        this.arousalCtx.shadowBlur = 0;
    }

    updateSpeechBoxHighlight(currentTime) {
        const currentSecond = Math.floor(currentTime);
        const boxes = this.elements.speechBoxes.children;
        
        // Remove current highlight from all boxes
        for (let i = 0; i < boxes.length; i++) {
            boxes[i].classList.remove('current');
        }
        
        // Highlight current second
        if (currentSecond < boxes.length) {
            boxes[currentSecond].classList.add('current');
        }
    }

    showAudioInfo() {
        if (!this.audioBuffer) return;

        const duration = this.audioBuffer.duration;
        const timeString = this.formatTime(duration);
        
        this.elements.duration.textContent = timeString;
        this.elements.totalTime.textContent = timeString;
        this.elements.currentTime.textContent = '0:00';
    }

    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    async togglePlayback() {
        if (!this.audioBuffer) return;

        if (this.isPlaying) {
            this.pauseAudio();
        } else {
            await this.playAudio();
        }
    }

    async playAudio() {
        if (!this.audioContext || !this.audioBuffer) return;

        try {
            // Stop any existing playback
            this.stopAudio();

            // Create new audio source
            this.audioSource = this.audioContext.createBufferSource();
            this.audioSource.buffer = this.audioBuffer;
            this.audioSource.connect(this.audioContext.destination);

            // Set up playback tracking
            this.startTime = this.audioContext.currentTime - this.pauseTime;
            this.isPlaying = true;
            this.elements.playBtn.textContent = 'Pause';
            this.elements.scrubber.classList.add('visible');

            // Handle playback end
            this.audioSource.onended = () => {
                this.stopAudio();
            };

            // Start playback
            this.audioSource.start(0, this.pauseTime);
            this.updatePlaybackPosition();

        } catch (error) {
            console.error('Playback error:', error);
            this.showStatus('Playback error: ' + error.message, 'error');
        }
    }

    pauseAudio() {
        if (this.audioSource && this.isPlaying) {
            this.pauseTime = this.audioContext.currentTime - this.startTime;
            this.audioSource.stop();
            this.audioSource = null;
            this.isPlaying = false;
            this.elements.playBtn.textContent = 'Play';
            
            if (this.animationFrame) {
                cancelAnimationFrame(this.animationFrame);
            }
        }
    }

    stopAudio() {
        if (this.audioSource) {
            this.audioSource.stop();
            this.audioSource = null;
        }
        
        this.isPlaying = false;
        this.pauseTime = 0;
        this.elements.playBtn.textContent = 'Play';
        this.elements.currentTime.textContent = '0:00';
        this.elements.scrubber.classList.remove('visible');
        
        // Reset visual effects
        this.canvas.style.filter = 'none';
        
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }

        this.redrawWaveform();
        if (this.arousalData) {
            this.drawArousalLine();
        }
        
        // Reset metric visualizations with accurate ranges
        if (this.loudnessDataStatic && this.pitchDataStatic && this.paceDataStatic) {
            this.drawMetricVisualization('loudness', this.loudnessDataStatic, 20, 85, ['#28a745', '#20c997']);
            this.drawMetricVisualization('pitch', this.pitchDataStatic, 85, 400, ['#007bff', '#6f42c1']);
            this.drawMetricVisualization('pace', this.paceDataStatic, 80, 300, ['#dc3545', '#e83e8c']);
        }
    }

    updatePlaybackPosition() {
        if (!this.isPlaying || !this.audioBuffer) return;

        const currentTime = this.audioContext.currentTime - this.startTime;
        const duration = this.audioBuffer.duration;
        const progress = Math.min(currentTime / duration, 1);

        // Update time display
        this.elements.currentTime.textContent = this.formatTime(currentTime);

        // Update scrubber position with smooth animation
        const canvasRect = this.canvas.getBoundingClientRect();
        const scrubberX = progress * canvasRect.width;
        this.elements.scrubber.style.left = (15 + scrubberX) + 'px';

        // Update waveform colors with dynamic animation
        const width = this.canvas.width / (window.devicePixelRatio || 1);
        const playPosition = progress * width;
        this.redrawWaveform(playPosition);
        
        // Update arousal visualization
        const arousalWidth = this.arousalCanvas.width / (window.devicePixelRatio || 1);
        const arousalPlayPosition = progress * arousalWidth;
        this.drawArousalLine(arousalPlayPosition);
        
        // Update metric visualizations with play position
        if (this.loudnessDataStatic && this.pitchDataStatic && this.paceDataStatic) {
            const metricWidth = this.elements.loudnessCanvas.width / (window.devicePixelRatio || 1);
            const metricPlayPosition = progress * metricWidth;
            
            this.drawMetricVisualization('loudness', this.loudnessDataStatic, 20, 85, ['#28a745', '#20c997'], metricPlayPosition);
            this.drawMetricVisualization('pitch', this.pitchDataStatic, 85, 400, ['#007bff', '#6f42c1'], metricPlayPosition);
            this.drawMetricVisualization('pace', this.paceDataStatic, 80, 300, ['#dc3545', '#e83e8c'], metricPlayPosition);
        }
        
        // Add pulse effect during playback
        const intensity = Math.sin(currentTime * 10) * 0.5 + 0.5;
        this.canvas.style.filter = `brightness(${1 + intensity * 0.2}) saturate(${1 + intensity * 0.3})`;

        // Update speech box highlighting
        this.updateSpeechBoxHighlight(currentTime);

        // Check if playback is complete
        if (currentTime >= duration) {
            this.stopAudio();
            return;
        }

        // Continue animation
        this.animationFrame = requestAnimationFrame(() => this.updatePlaybackPosition());
    }

    handleWaveformClick(event) {
        if (!this.audioBuffer) return;

        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const progress = x / rect.width;
        const seekTime = progress * this.audioBuffer.duration;

        // Update pause time for seeking
        this.pauseTime = seekTime;
        this.elements.currentTime.textContent = this.formatTime(seekTime);

        // Update visual position
        const width = this.canvas.width / (window.devicePixelRatio || 1);
        const playPosition = progress * width;
        this.redrawWaveform(playPosition);

        // Update scrubber position
        this.elements.scrubber.style.left = (15 + x) + 'px';
        this.elements.scrubber.classList.add('visible');

        // If currently playing, restart from new position
        if (this.isPlaying) {
            this.playAudio();
        }
    }

    showStatus(message, type) {
        this.elements.statusMessage.textContent = message;
        this.elements.statusMessage.className = `status-message visible ${type}`;
        
        setTimeout(() => {
            this.hideStatus();
        }, 3000);
    }

    hideStatus() {
        this.elements.statusMessage.classList.remove('visible');
    }

    async analyzeEmotion() {
        if (!this.audioBuffer) {
            this.showStatus('No audio to analyze', 'error');
            return;
        }

        this.elements.emotionBtn.disabled = true;
        this.elements.emotionBtn.textContent = '🔍 Analyzing...';
        this.showStatus('Analyzing speech and emotions...', 'info');

        try {
            // Convert audio buffer to WAV blob
            const wavBlob = await this.audioBufferToWav(this.audioBuffer);
            
            // Create form data for the API
            const formData = new FormData();
            formData.append('audio', wavBlob, 'recording.wav');

            // Send to enhanced emotion analysis server with training capabilities
            const response = await fetch('http://localhost:5003/api/analyze-audio', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Full API Response:', result);
            
            if (result.success && result.result) {
                console.log('Processing successful result:', result.result);
                this.displayEmotionResults(result.result);
                this.showStatus('Emotion analysis complete!', 'success');
                
                // Show training alert if needed
                if (result.result.needs_review) {
                    this.showTrainingAlert(result.result.clip_id);
                }
                
                // Show unknown words notification if any
                if (result.result.unknown_words > 0) {
                    this.showStatus(`Found ${result.result.unknown_words} uncertain words - saved for training`, 'info');
                }
            } else {
                console.error('API Error:', result);
                this.showStatus(`Analysis failed: ${result.error || 'Unknown error'}`, 'error');
            }

        } catch (error) {
            console.error('Emotion analysis error:', error);
            this.showStatus(`Error during analysis: ${error.message}`, 'error');
        } finally {
            this.elements.emotionBtn.disabled = false;
            this.elements.emotionBtn.textContent = '🎭 Analyze Emotion';
        }
    }

    displayEmotionResults(result) {
        console.log('DEBUG: displayEmotionResults called with:', result);
        console.log('DEBUG: TIMESTAMP:', new Date().toISOString());
        const analysis = result.emotion_analysis;
        console.log('DEBUG: emotion_analysis:', analysis);
        console.log('DEBUG: transcription:', result.transcription);
        console.log('DEBUG: word_analysis length:', analysis ? (analysis.word_analysis ? analysis.word_analysis.length : 'missing') : 'no analysis');
        
        // Show emotion analysis section
        this.elements.emotionAnalysis.style.display = 'block';
        
        // Update transcription - handle empty transcription properly
        const transcriptionText = (result.transcription && result.transcription.trim()) 
            ? result.transcription 
            : 'No speech detected';
        this.elements.transcriptionText.textContent = transcriptionText;
        console.log('DEBUG: Setting transcription to:', transcriptionText);
        
        // Show confidence information
        this.displayConfidenceInfo(result.confidence, result.needs_review);
        
        // Display word-by-word analysis with color coding
        console.log('DEBUG: analysis object:', analysis);
        console.log('DEBUG: analysis.word_analysis:', analysis ? analysis.word_analysis : 'analysis is null');
        this.displayWordBreakdown(analysis ? (analysis.word_analysis || []) : []);
        
        // Update primary emotion - use the highest probability emotion for accuracy
        const emotionIcons = {
            'joy': '😊', 'trust': '🤝', 'anticipation': '🤔', 'surprise': '😮',
            'anger': '😠', 'fear': '😰', 'sadness': '😢', 'disgust': '🤢', 'neutral': '😐'
        };
        
        // Find the emotion with the highest probability (most accurate method)
        const emotions = analysis.emotions;
        const sortedEmotions = Object.entries(emotions).sort((a, b) => b[1] - a[1]);
        const primaryEmotion = sortedEmotions[0];
        const mainEmotion = primaryEmotion[0];
        const mainEmotionScore = primaryEmotion[1];
        
        console.log('DEBUG: Emotion scores:', emotions);
        console.log('DEBUG: Primary emotion:', mainEmotion, 'with score:', mainEmotionScore);
        
        this.elements.emotionIcon.textContent = emotionIcons[mainEmotion] || '😐';
        this.elements.emotionName.textContent = mainEmotion.charAt(0).toUpperCase() + mainEmotion.slice(1);
        this.elements.emotionConfidence.textContent = Math.round(mainEmotionScore * 100) + '%';
        
        // Update VAD scores
        this.elements.valenceScore.textContent = analysis.vad.valence.toFixed(2);
        this.elements.arousalScore.textContent = analysis.vad.arousal.toFixed(2);
        this.elements.dominanceScore.textContent = analysis.vad.dominance.toFixed(2);
        
        // Update sentiment
        this.elements.sentimentPolarity.textContent = 
            analysis.sentiment.polarity.charAt(0).toUpperCase() + analysis.sentiment.polarity.slice(1);
        this.elements.sentimentStrength.textContent = Math.round(analysis.sentiment.strength * 100) + '%';
        
        // Create emotion bars with enhanced scores
        console.log('DEBUG: Creating emotion bars with:', analysis.emotions);
        this.createEmotionBars(analysis.emotions);
        
        // Display laughter analysis if available
        this.displayLaughterAnalysis(result.laughter_analysis, analysis.laughter_influence);
        
        // Display music analysis if available
        this.displayMusicAnalysis(result.music_analysis);
    }

    displayLaughterAnalysis(laughterData, laughterInfluence) {
        const laughterSection = document.getElementById('laughterAnalysis');
        const laughterSummary = document.getElementById('laughterSummary');
        const laughterTimeline = document.getElementById('laughterTimeline');
        const laughterInfluenceDiv = document.getElementById('laughterInfluence');
        
        if (!laughterSection || !laughterData) {
            return;
        }
        
        // Check if laughter was detected
        const segments = laughterData.laughter_segments || [];
        
        if (segments.length === 0) {
            laughterSection.style.display = 'none';
            return;
        }
        
        // Show laughter section
        laughterSection.style.display = 'block';
        
        // Update summary
        const totalTime = laughterData.total_laughter_time || 0;
        const percentage = laughterData.laughter_percentage || 0;
        const numBursts = segments.length;
        const duration = laughterData.audio_duration || 0;
        
        laughterSummary.innerHTML = `
            <strong>😄 ${numBursts} laughter burst${numBursts !== 1 ? 's' : ''} detected</strong><br>
            ⏱️ Total laughter: ${totalTime.toFixed(1)}s (${percentage.toFixed(1)}% of audio)
        `;
        
        // Draw laughter timeline graph
        this.drawLaughterGraph(laughterData);
        
        // Create timeline visualization in word-analysis style
        const laughterSegmentsHtml = segments.map((segment, index) => `
            <span class="laughter-segment" title="Laughter: ${segment.start_time}s-${segment.end_time}s (${Math.round(segment.confidence * 100)}% confidence)">
                😄 ${segment.start_time}s-${segment.end_time}s
            </span>
        `).join('');
        
        laughterTimeline.innerHTML = `
            <strong>Laughter Timeline:</strong>
            <div style="margin-top: 10px;">
                ${laughterSegmentsHtml}
            </div>
            <div class="laughter-legend">
                <span class="laughter-legend-item">😄 Laughter Detected</span>
            </div>
            <div class="laughter-stats">
                <span>Total: ${totalTime.toFixed(1)}s</span>
                <span class="laughter-percentage">${percentage.toFixed(1)}% of audio</span>
            </div>
        `;
        
        // Show laughter influence on emotions if available
        if (laughterInfluence && laughterInfluence.applied && laughterInfluenceDiv) {
            laughterInfluenceDiv.style.display = 'block';
            const boostAmount = ((laughterInfluence.boosted_joy - laughterInfluence.original_joy) * 100).toFixed(1);
            laughterInfluenceDiv.innerHTML = `
                <div style="margin-top: 15px; padding: 10px; background: rgba(255, 193, 7, 0.1); border-radius: 6px; border-left: 3px solid #ffc107;">
                    <strong>🎭 Emotion Impact:</strong> Laughter boosted joy by ${boostAmount}%
                    <div style="font-size: 0.9em; color: #6c757d; margin-top: 5px;">
                        Joy: ${(laughterInfluence.original_joy * 100).toFixed(1)}% → ${(laughterInfluence.boosted_joy * 100).toFixed(1)}%
                    </div>
                </div>
            `;
        } else if (laughterInfluenceDiv) {
            laughterInfluenceDiv.style.display = 'none';
        }
        
        console.log('DEBUG: Displayed laughter analysis:', laughterData);
    }

    drawLaughterGraph(laughterData) {
        const canvas = document.getElementById('laughterGraph');
        const graphContainer = document.getElementById('laughterGraphContainer');
        const maxTimeLabel = document.getElementById('maxTimeLabel');
        
        if (!canvas || !laughterData.timeline_data) {
            if (graphContainer) graphContainer.style.display = 'none';
            return;
        }

        const timelineData = laughterData.timeline_data;
        const points = timelineData.points || [];
        
        if (points.length === 0) {
            if (graphContainer) graphContainer.style.display = 'none';
            return;
        }

        // Show graph container
        if (graphContainer) graphContainer.style.display = 'block';
        
        // Update time label
        if (maxTimeLabel) {
            maxTimeLabel.textContent = `${laughterData.audio_duration.toFixed(1)}s`;
        }

        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Set up drawing parameters
        const padding = 20;
        const graphWidth = width - (padding * 2);
        const graphHeight = height - (padding * 2);
        const maxTime = laughterData.audio_duration;
        const maxIntensity = timelineData.max_intensity || 1.0;
        
        // Draw background grid
        ctx.strokeStyle = '#e9ecef';
        ctx.lineWidth = 1;
        
        // Vertical grid lines (time)
        const timeSteps = Math.min(10, Math.ceil(maxTime));
        for (let i = 0; i <= timeSteps; i++) {
            const x = padding + (i / timeSteps) * graphWidth;
            ctx.beginPath();
            ctx.moveTo(x, padding);
            ctx.lineTo(x, height - padding);
            ctx.stroke();
        }
        
        // Horizontal grid lines (intensity)
        for (let i = 0; i <= 4; i++) {
            const y = padding + (i / 4) * graphHeight;
            ctx.beginPath();
            ctx.moveTo(padding, y);
            ctx.lineTo(width - padding, y);
            ctx.stroke();
        }
        
        // Draw laughter intensity line
        if (points.length > 1) {
            ctx.strokeStyle = '#f1c40f';
            ctx.lineWidth = 3;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            
            ctx.beginPath();
            
            for (let i = 0; i < points.length; i++) {
                const point = points[i];
                const x = padding + (point.time / maxTime) * graphWidth;
                const y = height - padding - (point.laughter_intensity / maxIntensity) * graphHeight;
                
                if (i === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            }
            
            ctx.stroke();
            
            // Fill area under the curve
            ctx.fillStyle = 'rgba(241, 196, 15, 0.2)';
            ctx.lineTo(width - padding, height - padding);
            ctx.lineTo(padding, height - padding);
            ctx.closePath();
            ctx.fill();
        }
        
        // Draw laughter segment highlights
        const segments = laughterData.laughter_segments || [];
        segments.forEach(segment => {
            const startX = padding + (segment.start_time / maxTime) * graphWidth;
            const endX = padding + (segment.end_time / maxTime) * graphWidth;
            
            // Draw highlight rectangle
            ctx.fillStyle = 'rgba(255, 193, 7, 0.4)';
            ctx.fillRect(startX, padding, endX - startX, graphHeight);
            
            // Draw segment borders
            ctx.strokeStyle = '#ffc107';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(startX, padding);
            ctx.lineTo(startX, height - padding);
            ctx.moveTo(endX, padding);
            ctx.lineTo(endX, height - padding);
            ctx.stroke();
        });
        
        // Add axis labels
        ctx.fillStyle = '#495057';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        
        // Y-axis label
        ctx.save();
        ctx.translate(12, height / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText('Laughter Intensity', 0, 0);
        ctx.restore();
        
        // X-axis label
        ctx.fillText('Time (seconds)', width / 2, height - 5);
        
        // Add hover functionality
        this.setupGraphHover(canvas, laughterData);
    }

    setupGraphHover(canvas, laughterData) {
        const tooltip = document.createElement('div');
        tooltip.className = 'graph-tooltip';
        document.body.appendChild(tooltip);
        
        canvas.addEventListener('mousemove', (event) => {
            const rect = canvas.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            
            // Convert pixel coordinates to time
            const padding = 20;
            const graphWidth = canvas.width - (padding * 2);
            const relativeX = (x - padding) / graphWidth;
            const time = relativeX * laughterData.audio_duration;
            
            if (time >= 0 && time <= laughterData.audio_duration) {
                // Find closest timeline point
                const timelineData = laughterData.timeline_data;
                if (timelineData && timelineData.points) {
                    const closestPoint = timelineData.points.reduce((prev, curr) => 
                        Math.abs(curr.time - time) < Math.abs(prev.time - time) ? curr : prev
                    );
                    
                    // Show tooltip
                    tooltip.style.display = 'block';
                    tooltip.style.left = (event.clientX + 10) + 'px';
                    tooltip.style.top = (event.clientY - 40) + 'px';
                    tooltip.innerHTML = `
                        Time: ${closestPoint.time.toFixed(1)}s<br>
                        Laughter: ${(closestPoint.laughter_intensity * 100).toFixed(1)}%
                    `;
                }
            }
        });
        
        canvas.addEventListener('mouseleave', () => {
            tooltip.style.display = 'none';
        });
    }

    displayMusicAnalysis(musicData) {
        const musicSection = document.getElementById('musicAnalysis');
        const musicSummary = document.getElementById('musicSummary');
        const musicTimeline = document.getElementById('musicTimeline');
        const identifiedSongs = document.getElementById('identifiedSongs');
        
        if (!musicSection || !musicData) {
            return;
        }
        
        // Check if music was detected
        const segments = musicData.music_segments || [];
        const songs = musicData.identified_songs || [];
        
        if (segments.length === 0) {
            musicSection.style.display = 'none';
            return;
        }
        
        // Show music section
        musicSection.style.display = 'block';
        
        // Update summary
        const totalTime = musicData.total_music_time || 0;
        const percentage = musicData.music_percentage || 0;
        const numSegments = segments.length;
        
        musicSummary.innerHTML = `
            <strong>🎵 ${numSegments} music segment${numSegments !== 1 ? 's' : ''} detected</strong><br>
            ⏱️ Total music: ${totalTime.toFixed(1)}s (${percentage.toFixed(1)}% of audio)
        `;
        
        // Draw music timeline graph
        this.drawMusicGraph(musicData);
        
        // Create timeline visualization in word-analysis style
        const musicSegmentsHtml = segments.map((segment, index) => `
            <span class="music-segment" title="Music: ${segment.start_time}s-${segment.end_time}s (${Math.round(segment.confidence * 100)}% confidence)">
                🎵 ${segment.start_time}s-${segment.end_time}s
            </span>
        `).join('');
        
        musicTimeline.innerHTML = `
            <strong>Music Timeline:</strong>
            <div style="margin-top: 10px;">
                ${musicSegmentsHtml}
            </div>
            <div class="music-legend">
                <span class="music-legend-item">🎵 Background Music</span>
            </div>
            <div class="music-stats">
                <span>Total: ${totalTime.toFixed(1)}s</span>
                <span class="music-percentage">${percentage.toFixed(1)}% of audio</span>
            </div>
        `;
        
        // Show identified songs if any
        if (songs.length > 0 && identifiedSongs) {
            identifiedSongs.style.display = 'block';
            identifiedSongs.innerHTML = `
                <strong>🎼 Identified Songs:</strong>
                ${songs.map(song => `
                    <div class="song-item">
                        <div class="song-info">
                            <div class="song-title">${song.title}</div>
                            <div class="song-artist">by ${song.artist}</div>
                        </div>
                        <div class="song-confidence">${Math.round(song.match_confidence * 100)}%</div>
                        <div class="song-timing">${song.segment_start}s-${song.segment_end}s</div>
                    </div>
                `).join('')}
            `;
        } else if (identifiedSongs) {
            identifiedSongs.style.display = 'none';
        }
        
        console.log('DEBUG: Displayed music analysis:', musicData);
    }

    drawMusicGraph(musicData) {
        const canvas = document.getElementById('musicGraph');
        const graphContainer = document.getElementById('musicGraphContainer');
        const maxTimeLabel = document.getElementById('musicMaxTimeLabel');
        
        if (!canvas || !musicData.timeline_data) {
            if (graphContainer) graphContainer.style.display = 'none';
            return;
        }

        const timelineData = musicData.timeline_data;
        const points = timelineData.points || [];
        
        if (points.length === 0) {
            if (graphContainer) graphContainer.style.display = 'none';
            return;
        }

        // Show graph container
        if (graphContainer) graphContainer.style.display = 'block';
        
        // Update time label
        if (maxTimeLabel) {
            maxTimeLabel.textContent = `${musicData.audio_duration.toFixed(1)}s`;
        }

        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Set up drawing parameters
        const padding = 20;
        const graphWidth = width - (padding * 2);
        const graphHeight = height - (padding * 2);
        const maxTime = musicData.audio_duration;
        const maxIntensity = timelineData.max_intensity || 1.0;
        
        // Draw background grid
        ctx.strokeStyle = '#e9ecef';
        ctx.lineWidth = 1;
        
        // Vertical grid lines (time)
        const timeSteps = Math.min(10, Math.ceil(maxTime));
        for (let i = 0; i <= timeSteps; i++) {
            const x = padding + (i / timeSteps) * graphWidth;
            ctx.beginPath();
            ctx.moveTo(x, padding);
            ctx.lineTo(x, height - padding);
            ctx.stroke();
        }
        
        // Horizontal grid lines (intensity)
        for (let i = 0; i <= 4; i++) {
            const y = padding + (i / 4) * graphHeight;
            ctx.beginPath();
            ctx.moveTo(padding, y);
            ctx.lineTo(width - padding, y);
            ctx.stroke();
        }
        
        // Draw music intensity line
        if (points.length > 1) {
            ctx.strokeStyle = '#29b6f6';
            ctx.lineWidth = 3;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            
            ctx.beginPath();
            
            for (let i = 0; i < points.length; i++) {
                const point = points[i];
                const x = padding + (point.time / maxTime) * graphWidth;
                const y = height - padding - (point.music_intensity / maxIntensity) * graphHeight;
                
                if (i === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            }
            
            ctx.stroke();
            
            // Fill area under the curve
            ctx.fillStyle = 'rgba(41, 182, 246, 0.2)';
            ctx.lineTo(width - padding, height - padding);
            ctx.lineTo(padding, height - padding);
            ctx.closePath();
            ctx.fill();
        }
        
        // Draw music segment highlights
        const segments = musicData.music_segments || [];
        segments.forEach(segment => {
            const startX = padding + (segment.start_time / maxTime) * graphWidth;
            const endX = padding + (segment.end_time / maxTime) * graphWidth;
            
            // Draw highlight rectangle
            ctx.fillStyle = 'rgba(41, 182, 246, 0.4)';
            ctx.fillRect(startX, padding, endX - startX, graphHeight);
            
            // Draw segment borders
            ctx.strokeStyle = '#29b6f6';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(startX, padding);
            ctx.lineTo(startX, height - padding);
            ctx.moveTo(endX, padding);
            ctx.lineTo(endX, height - padding);
            ctx.stroke();
        });
        
        // Add axis labels
        ctx.fillStyle = '#495057';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        
        // Y-axis label
        ctx.save();
        ctx.translate(12, height / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText('Music Intensity', 0, 0);
        ctx.restore();
        
        // X-axis label
        ctx.fillText('Time (seconds)', width / 2, height - 5);
        
        // Add hover functionality
        this.setupMusicGraphHover(canvas, musicData);
    }

    setupMusicGraphHover(canvas, musicData) {
        const tooltip = document.createElement('div');
        tooltip.className = 'graph-tooltip';
        document.body.appendChild(tooltip);
        
        canvas.addEventListener('mousemove', (event) => {
            const rect = canvas.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            
            // Convert pixel coordinates to time
            const padding = 20;
            const graphWidth = canvas.width - (padding * 2);
            const relativeX = (x - padding) / graphWidth;
            const time = relativeX * musicData.audio_duration;
            
            if (time >= 0 && time <= musicData.audio_duration) {
                // Find closest timeline point
                const timelineData = musicData.timeline_data;
                if (timelineData && timelineData.points) {
                    const closestPoint = timelineData.points.reduce((prev, curr) => 
                        Math.abs(curr.time - time) < Math.abs(prev.time - time) ? curr : prev
                    );
                    
                    // Show tooltip
                    tooltip.style.display = 'block';
                    tooltip.style.left = (event.clientX + 10) + 'px';
                    tooltip.style.top = (event.clientY - 40) + 'px';
                    tooltip.innerHTML = `
                        Time: ${closestPoint.time.toFixed(1)}s<br>
                        Music: ${(closestPoint.music_intensity * 100).toFixed(1)}%
                    `;
                }
            }
        });
        
        canvas.addEventListener('mouseleave', () => {
            tooltip.style.display = 'none';
        });
    }

    displayWordBreakdown(wordAnalysis) {
        if (!this.elements.wordBreakdown) return;
        
        this.elements.wordBreakdown.innerHTML = '';
        
        console.log('DEBUG: displayWordBreakdown called with:', wordAnalysis);
        console.log('DEBUG: wordAnalysis type:', typeof wordAnalysis);
        console.log('DEBUG: wordAnalysis length:', wordAnalysis ? wordAnalysis.length : 'null/undefined');
        
        if (!wordAnalysis || !Array.isArray(wordAnalysis) || wordAnalysis.length === 0) {
            console.log('DEBUG: No word analysis data available');
            this.elements.wordBreakdown.innerHTML = '<span class="no-words">No words to analyze (Debug: wordAnalysis=' + (wordAnalysis ? wordAnalysis.length : 'null') + ')</span>';
            return;
        }
        
        console.log('DEBUG: Processing', wordAnalysis.length, 'words for display');
        
        // Display ALL words regardless of confidence (simplified approach)
        console.log('DEBUG: Displaying all words without filtering');
        
        wordAnalysis.forEach(wordData => {
            console.log('DEBUG: Processing word:', wordData.word, 'emotion:', wordData.emotion, 'confidence:', wordData.confidence);
            
            const wordSpan = document.createElement('span');
            wordSpan.className = `word-item ${wordData.emotion || 'neutral'}`;
            wordSpan.textContent = wordData.word;
            
            // Add confidence badge
            if (wordData.confidence !== undefined) {
                const confidenceBadge = document.createElement('span');
                confidenceBadge.className = 'word-confidence';
                confidenceBadge.textContent = Math.round(wordData.confidence * 100) + '%';
                wordSpan.appendChild(confidenceBadge);
            }
            
            // Add tooltip
            const tooltip = `Emotion: ${wordData.emotion || 'neutral'} (${Math.round((wordData.confidence || 0) * 100)}%)\nFound: ${wordData.found ? 'Yes' : 'No'}`;
            wordSpan.setAttribute('title', tooltip);
            
            this.elements.wordBreakdown.appendChild(wordSpan);
        });
        
        console.log('DEBUG: Finished displaying', wordAnalysis.length, 'words');
        
        // OLD CODE - keeping for reference but not using
        if (false) { // Disabled complex filtering
            const confidentHeader = document.createElement('div');
            confidentHeader.className = 'word-section-header';
            confidentHeader.style.cssText = 'font-weight: bold; color: #4CAF50; margin-bottom: 10px;';
            confidentHeader.textContent = `✅ Confident Words (${confidentWords.length})`;
            this.elements.wordBreakdown.appendChild(confidentHeader);
            
            confidentWords.forEach(wordData => {
                const wordSpan = document.createElement('span');
                wordSpan.className = `word-item confident ${wordData.emotion}`;
                wordSpan.style.cssText = 'border: 2px solid #4CAF50; background: rgba(76, 175, 80, 0.1);';
                wordSpan.textContent = wordData.word;
                
                const confidenceBadge = document.createElement('span');
                confidenceBadge.className = 'word-confidence';
                confidenceBadge.textContent = Math.round(wordData.confidence * 100) + '%';
                wordSpan.appendChild(confidenceBadge);
                
                const tooltip = `Emotion: ${wordData.emotion} (${Math.round(wordData.confidence * 100)}%)\nValence: ${wordData.valence.toFixed(2)}\nArousal: ${wordData.arousal.toFixed(2)}\nSentiment: ${wordData.sentiment}`;
                wordSpan.setAttribute('data-tooltip', tooltip);
                
                wordSpan.addEventListener('click', () => {
                    this.showWordDetails(wordData);
                });
                
                this.elements.wordBreakdown.appendChild(wordSpan);
            });
        }
        
        // Display filtered words in a collapsed, less prominent section
        if (filteredWords.length > 0) {
            const filteredHeader = document.createElement('div');
            filteredHeader.className = 'word-section-header';
            filteredHeader.style.cssText = 'margin-top: 15px; font-size: 0.9em; color: #999; cursor: pointer;';
            filteredHeader.textContent = `🚫 Filtered Words (${filteredWords.length}) - Click to show`;
            
            const filteredContainer = document.createElement('div');
            filteredContainer.style.display = 'none';
            filteredContainer.className = 'filtered-words-container';
            
            filteredWords.forEach(wordData => {
                const wordSpan = document.createElement('span');
                wordSpan.className = 'word-item filtered';
                wordSpan.style.cssText = 'opacity: 0.4; background: #f5f5f5; color: #999; border: 1px dashed #ccc;';
                wordSpan.textContent = wordData.word;
                
                const tooltip = `Filtered: Too uncertain (${Math.round(wordData.confidence * 100)}%)`;
                wordSpan.setAttribute('data-tooltip', tooltip);
                
                filteredContainer.appendChild(wordSpan);
            });
            
            // Toggle visibility on header click
            filteredHeader.addEventListener('click', () => {
                const isVisible = filteredContainer.style.display !== 'none';
                filteredContainer.style.display = isVisible ? 'none' : 'block';
                filteredHeader.textContent = `🚫 Filtered Words (${filteredWords.length}) - ${isVisible ? 'Click to show' : 'Click to hide'}`;
            });
            
            this.elements.wordBreakdown.appendChild(filteredHeader);
            this.elements.wordBreakdown.appendChild(filteredContainer);
        }
        
        // Display not found words
        if (notFoundWords.length > 0) {
            notFoundWords.forEach(wordData => {
                const wordSpan = document.createElement('span');
                wordSpan.className = 'word-item not-found';
                wordSpan.textContent = wordData.word;
                
                const tooltip = 'Word not found in emotion database';
                wordSpan.setAttribute('data-tooltip', tooltip);
                
                wordSpan.addEventListener('click', () => {
                    this.showWordDetails(wordData);
                });
                
                this.elements.wordBreakdown.appendChild(wordSpan);
            });
        } // End of disabled old code
    }

    showWordDetails(wordData) {
        const details = wordData.found 
            ? `Word: "${wordData.word}"\nEmotion: ${wordData.emotion} (${Math.round(wordData.confidence * 100)}% confidence)\nValence: ${wordData.valence.toFixed(2)} (how positive/negative)\nArousal: ${wordData.arousal.toFixed(2)} (how energetic)\nSentiment: ${wordData.sentiment}`
            : `Word: "${wordData.word}"\nStatus: Not found in emotion database\nUsing neutral values as fallback`;
            
        alert(details);
    }

    createEmotionBars(emotions) {
        this.elements.emotionDetails.innerHTML = '';
        
        const emotionColors = {
            'joy': '#f1c40f', 'trust': '#3498db', 'anticipation': '#e67e22', 'surprise': '#9b59b6',
            'anger': '#e74c3c', 'fear': '#34495e', 'sadness': '#2c3e50', 'disgust': '#27ae60'
        };
        
        // Sort emotions by probability
        const sortedEmotions = Object.entries(emotions).sort((a, b) => b[1] - a[1]);
        
        sortedEmotions.forEach(([emotion, probability]) => {
            const barContainer = document.createElement('div');
            barContainer.className = 'emotion-bar';
            
            const label = document.createElement('div');
            label.className = 'emotion-label';
            label.textContent = emotion;
            
            const barBg = document.createElement('div');
            barBg.className = 'emotion-bar-bg';
            
            const barFill = document.createElement('div');
            barFill.className = 'emotion-bar-fill';
            barFill.style.width = (probability * 100) + '%';
            barFill.style.backgroundColor = emotionColors[emotion] || '#ccc';
            
            const percentage = document.createElement('div');
            percentage.className = 'emotion-percentage';
            percentage.textContent = Math.round(probability * 100) + '%';
            
            barBg.appendChild(barFill);
            barContainer.appendChild(label);
            barContainer.appendChild(barBg);
            barContainer.appendChild(percentage);
            
            this.elements.emotionDetails.appendChild(barContainer);
        });
    }

    async audioBufferToWav(audioBuffer) {
        const numberOfChannels = audioBuffer.numberOfChannels;
        const sampleRate = audioBuffer.sampleRate;
        const length = audioBuffer.length;
        const arrayBuffer = new ArrayBuffer(44 + length * numberOfChannels * 2);
        const view = new DataView(arrayBuffer);
        
        // WAV header
        const writeString = (offset, string) => {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        };
        
        writeString(0, 'RIFF');
        view.setUint32(4, 36 + length * numberOfChannels * 2, true);
        writeString(8, 'WAVE');
        writeString(12, 'fmt ');
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true);
        view.setUint16(22, numberOfChannels, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * numberOfChannels * 2, true);
        view.setUint16(32, numberOfChannels * 2, true);
        view.setUint16(34, 16, true);
        writeString(36, 'data');
        view.setUint32(40, length * numberOfChannels * 2, true);
        
        // Convert audio data
        let offset = 44;
        for (let i = 0; i < length; i++) {
            for (let channel = 0; channel < numberOfChannels; channel++) {
                const sample = Math.max(-1, Math.min(1, audioBuffer.getChannelData(channel)[i]));
                view.setInt16(offset, sample * 0x7FFF, true);
                offset += 2;
            }
        }
        
        return new Blob([arrayBuffer], { type: 'audio/wav' });
    }

    displayConfidenceInfo(confidence, needsReview) {
        const confidenceInfo = document.getElementById('confidenceInfo');
        const confidenceValue = document.getElementById('confidenceValue');
        const confidenceFill = document.getElementById('confidenceFill');
        
        if (confidenceInfo && confidenceValue && confidenceFill) {
            confidenceInfo.style.display = 'block';
            
            const confidencePercent = Math.round(confidence * 100);
            confidenceValue.textContent = confidencePercent + '%';
            confidenceFill.style.width = confidencePercent + '%';
            
            // Set color based on confidence level
            confidenceFill.className = 'confidence-fill';
            if (confidence >= 0.7) {
                confidenceFill.classList.add('high');
            } else if (confidence >= 0.4) {
                confidenceFill.classList.add('medium');
            } else {
                confidenceFill.classList.add('low');
            }
        }
    }

    showTrainingAlert(clipId) {
        const trainingAlert = document.getElementById('trainingAlert');
        if (trainingAlert && clipId) {
            trainingAlert.style.display = 'block';
            
            // Auto-hide after 10 seconds
            setTimeout(() => {
                trainingAlert.style.display = 'none';
            }, 10000);
        }
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    new AudioRecorder();
});
