/**
 * TTSService.js - Text-to-Speech Queue Management
 *
 * Handles TTS generation, queuing, and playback with:
 * - Ordered playback (sentences play in correct sequence)
 * - Pending queue for async TTS generation
 * - Audio element management
 * - Callbacks for lip sync integration
 */

class TTSService {
    constructor(apiService) {
        this.apiService = apiService;

        // Audio queue and state
        this.audioQueue = [];
        this.pendingQueue = new Map();
        this.isPlaying = false;
        this.sequenceNumber = 0;
        this.nextToAdd = 0;

        // Audio element
        this.audioElement = null;

        // Callbacks
        this.callbacks = {
            onPlay: null,
            onEnd: null,
            onError: null
        };
    }

    /**
     * Initialize with audio element
     */
    init(audioElementId) {
        this.audioElement = document.getElementById(audioElementId);
        if (!this.audioElement) {
            throw new Error(`Audio element '${audioElementId}' not found`);
        }
    }

    /**
     * Set callbacks for events
     */
    setCallbacks({ onPlay, onEnd, onError }) {
        if (onPlay) this.callbacks.onPlay = onPlay;
        if (onEnd) this.callbacks.onEnd = onEnd;
        if (onError) this.callbacks.onError = onError;
    }

    /**
     * Generate TTS for a sentence and add to queue
     */
    async generateAndQueue(text) {
        const mySequence = this.sequenceNumber++;

        try {
            // Generate TTS via API
            const response = await this.apiService.generateTTS(text);

            if (response && response.audio_url) {
                const audioData = {
                    url: response.audio_url,
                    text: text,
                    sequence: mySequence
                };

                // Add to pending queue
                this.pendingQueue.set(mySequence, audioData);

                // Try to add to playback queue in order
                this.processPendingQueue();
            }
        } catch (error) {
            console.error('TTS generation error:', error);
            if (this.callbacks.onError) {
                this.callbacks.onError(error);
            }
        }
    }

    /**
     * Process pending queue and add items in order
     */
    processPendingQueue() {
        // Add items in sequence order
        while (this.pendingQueue.has(this.nextToAdd)) {
            const audioData = this.pendingQueue.get(this.nextToAdd);
            this.pendingQueue.delete(this.nextToAdd);

            // Add to audio queue
            this.audioQueue.push(audioData);

            // Start playing if not already
            if (!this.isPlaying) {
                this.playNext();
            }

            this.nextToAdd++;
        }
    }

    /**
     * Play next item in queue
     */
    playNext() {
        if (this.audioQueue.length === 0) {
            this.isPlaying = false;
            return;
        }

        this.isPlaying = true;
        const audioData = this.audioQueue.shift();

        if (!this.audioElement) {
            console.error('Audio element not initialized');
            return;
        }

        this.audioElement.src = audioData.url;

        // Play event handler
        const handlePlay = () => {
            if (this.callbacks.onPlay) {
                this.callbacks.onPlay(audioData);
            }
        };

        // End event handler
        const handleEnded = () => {
            if (this.callbacks.onEnd) {
                this.callbacks.onEnd(audioData);
            }

            // Cleanup listeners
            this.audioElement.removeEventListener('play', handlePlay);
            this.audioElement.removeEventListener('ended', handleEnded);

            // Play next
            this.playNext();
        };

        // Error handler
        const handleError = (error) => {
            console.error('Audio playback error:', error);
            if (this.callbacks.onError) {
                this.callbacks.onError(error);
            }

            // Cleanup and continue
            this.audioElement.removeEventListener('play', handlePlay);
            this.audioElement.removeEventListener('ended', handleEnded);
            this.playNext();
        };

        // Attach listeners
        this.audioElement.addEventListener('play', handlePlay);
        this.audioElement.addEventListener('ended', handleEnded);
        this.audioElement.addEventListener('error', handleError);

        // Start playback
        this.audioElement.play().catch(handleError);
    }

    /**
     * Clear all queues and reset
     */
    clear() {
        this.audioQueue = [];
        this.pendingQueue.clear();
        this.sequenceNumber = 0;
        this.nextToAdd = 0;

        if (this.audioElement) {
            this.audioElement.pause();
            this.audioElement.src = '';
        }

        this.isPlaying = false;
    }

    /**
     * Stop current playback
     */
    stop() {
        if (this.audioElement) {
            this.audioElement.pause();
            this.audioElement.currentTime = 0;
        }
        this.isPlaying = false;
    }

    /**
     * Get current state
     */
    getState() {
        return {
            isPlaying: this.isPlaying,
            queueLength: this.audioQueue.length,
            pendingCount: this.pendingQueue.size
        };
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TTSService;
}
