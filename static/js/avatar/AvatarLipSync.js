/**
 * AvatarLipSync.js - Advanced Lip Sync Engine
 *
 * Provides realistic lip sync for avatar with:
 * - Audio analysis (frequency + amplitude)
 * - Phoneme-based mouth shapes
 * - Text-to-phoneme estimation
 * - Smooth transitions between shapes
 * - Integration with AvatarCore
 */

class AvatarLipSync {
    constructor(avatarCore) {
        this.avatarCore = avatarCore;

        // Audio analysis
        this.audioContext = null;
        this.analyser = null;
        this.animationFrameId = null;

        // Phoneme mapping
        this.phonemeMap = this.createPhonemeMap();

        // Current state
        this.currentShape = 'SMILE';
        this.targetShape = 'SMILE';
        this.transitionProgress = 1;

        // Timing
        this.lastUpdateTime = 0;
        this.transitionDuration = 100; // ms
    }

    /**
     * Create phoneme to mouth shape mapping
     */
    createPhonemeMap() {
        return {
            // Closed mouth sounds
            'CLOSED': {
                phonemes: ['M', 'B', 'P'],
                words: ['me', 'my', 'be', 'by', 'please', 'maybe'],
                mouth: { rx: 0, ry: 0, opacity: 0 },
                shape: 'M 60 74 L 80 74'
            },

            // Small opening (EE, I sounds)
            'SMALL': {
                phonemes: ['IY', 'IH', 'EY'],
                words: ['see', 'it', 'is', 'in', 'this', 'we', 'me'],
                mouth: { rx: 4, ry: 2, opacity: 0.3 },
                shape: 'M 60 74 Q 70 76 80 74'
            },

            // Medium opening (EH, AE, UH sounds)
            'MEDIUM': {
                phonemes: ['EH', 'AE', 'AH', 'UH'],
                words: ['get', 'can', 'and', 'that', 'up', 'just'],
                mouth: { rx: 8, ry: 4, opacity: 0.6 },
                shape: 'M 58 72 Q 70 78 82 72'
            },

            // Large opening (AA, AO sounds)
            'LARGE': {
                phonemes: ['AA', 'AO', 'AW'],
                words: ['not', 'all', 'are', 'on', 'what', 'how'],
                mouth: { rx: 12, ry: 8, opacity: 0.9 },
                shape: 'M 56 70 Q 70 82 84 70'
            },

            // Wide opening (AY, OW sounds)
            'WIDE': {
                phonemes: ['AY', 'OW', 'OY'],
                words: ['I', 'my', 'now', 'how', 'go', 'so', 'oh'],
                mouth: { rx: 14, ry: 6, opacity: 0.8 },
                shape: 'M 54 74 Q 70 84 86 74'
            },

            // Rounded (OO, UW sounds)
            'ROUND': {
                phonemes: ['UW', 'OW', 'OO'],
                words: ['you', 'to', 'too', 'do', 'who', 'through'],
                mouth: { rx: 6, ry: 8, opacity: 0.7 },
                shape: 'M 62 72 Q 70 80 78 72'
            },

            // F/V sounds (teeth on lip)
            'FV': {
                phonemes: ['F', 'V'],
                words: ['for', 'from', 'have', 'of', 'very', 'if'],
                mouth: { rx: 5, ry: 2, opacity: 0.4 },
                shape: 'M 60 71 L 80 71'
            },

            // L sounds
            'L': {
                phonemes: ['L'],
                words: ['let', 'like', 'will', 'all', 'well'],
                mouth: { rx: 6, ry: 3, opacity: 0.5 },
                shape: 'M 60 73 Q 70 77 80 73'
            },

            // Default smile
            'SMILE': {
                phonemes: [],
                words: [],
                mouth: { rx: 0, ry: 0, opacity: 0 },
                shape: 'M 55 72 Q 70 78 85 72'
            }
        };
    }

    /**
     * Initialize with audio element
     */
    init(audioElement) {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            this.analyser.smoothingTimeConstant = 0.8;

            const source = this.audioContext.createMediaElementSource(audioElement);
            source.connect(this.analyser);
            this.analyser.connect(this.audioContext.destination);
        }
    }

    /**
     * Start lip sync with text and audio
     */
    startSpeaking(audioElement, text) {
        // Initialize if needed
        if (!this.audioContext) {
            this.init(audioElement);
        }

        // Parse text into phoneme sequence
        const phonemeSequence = this.textToPhonemes(text);

        // Start animation loop
        this.animate(phonemeSequence);
    }

    /**
     * Stop lip sync
     */
    stopSpeaking() {
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }

        // Return to smile
        this.setMouthShape('SMILE');
    }

    /**
     * Convert text to estimated phoneme sequence
     */
    textToPhonemes(text) {
        const words = text.toLowerCase().split(/\s+/);
        const sequence = [];

        for (const word of words) {
            // Find matching phoneme category
            let foundMatch = false;

            for (const [shapeName, data] of Object.entries(this.phonemeMap)) {
                if (data.words.some(w => word.includes(w))) {
                    sequence.push({
                        shape: shapeName,
                        duration: word.length * 80 // Approximate duration
                    });
                    foundMatch = true;
                    break;
                }
            }

            // Default to MEDIUM if no match
            if (!foundMatch) {
                sequence.push({
                    shape: 'MEDIUM',
                    duration: word.length * 80
                });
            }
        }

        return sequence;
    }

    /**
     * Main animation loop
     */
    animate(phonemeSequence = null) {
        if (!this.analyser) return;

        const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
        this.analyser.getByteFrequencyData(dataArray);

        // Calculate average volume
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        const normalizedVolume = average / 255;

        // Determine mouth shape based on volume
        let targetShape = 'SMILE';

        if (normalizedVolume > 0.15) {
            // Speaking - use volume to determine shape
            if (normalizedVolume > 0.5) {
                targetShape = 'LARGE';
            } else if (normalizedVolume > 0.35) {
                targetShape = 'MEDIUM';
            } else if (normalizedVolume > 0.2) {
                targetShape = 'SMALL';
            } else {
                targetShape = 'SMALL';
            }
        }

        // Update mouth shape
        this.setMouthShape(targetShape);

        // Continue animation
        this.animationFrameId = requestAnimationFrame(() => this.animate(phonemeSequence));
    }

    /**
     * Set mouth shape with smooth transition
     */
    setMouthShape(shapeName) {
        const shape = this.phonemeMap[shapeName];
        if (!shape) return;

        const container = this.avatarCore.container;
        if (!container) return;

        // Update mouth elements
        const mouth = container.querySelector('.mouth-smile');
        const mouthOpening = container.querySelector('.mouth-opening');

        if (mouth) {
            mouth.setAttribute('d', shape.shape);
        }

        if (mouthOpening) {
            mouthOpening.setAttribute('rx', shape.mouth.rx);
            mouthOpening.setAttribute('ry', shape.mouth.ry);
            mouthOpening.style.opacity = shape.mouth.opacity;
        }

        this.currentShape = shapeName;
    }

    /**
     * Cleanup
     */
    destroy() {
        this.stopSpeaking();

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
    }

    /**
     * Get current state
     */
    getState() {
        return {
            currentShape: this.currentShape,
            isAnimating: !!this.animationFrameId
        };
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AvatarLipSync;
}
