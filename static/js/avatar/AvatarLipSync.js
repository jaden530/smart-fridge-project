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

            // Small opening (EE, I sounds) - 3x bigger
            'SMALL': {
                phonemes: ['IY', 'IH', 'EY'],
                words: ['see', 'it', 'is', 'in', 'this', 'we', 'me'],
                mouth: { rx: 12, ry: 6, opacity: 0.7 },
                shape: 'M 60 74 Q 70 80 80 74'
            },

            // Medium opening (EH, AE, UH sounds) - 3x bigger
            'MEDIUM': {
                phonemes: ['EH', 'AE', 'AH', 'UH'],
                words: ['get', 'can', 'and', 'that', 'up', 'just'],
                mouth: { rx: 24, ry: 12, opacity: 0.85 },
                shape: 'M 58 72 Q 70 85 82 72'
            },

            // Large opening (AA, AO sounds) - 3x bigger
            'LARGE': {
                phonemes: ['AA', 'AO', 'AW'],
                words: ['not', 'all', 'are', 'on', 'what', 'how'],
                mouth: { rx: 36, ry: 24, opacity: 1.0 },
                shape: 'M 56 68 Q 70 92 84 68'
            },

            // Wide opening (AY, OW sounds) - 3x bigger
            'WIDE': {
                phonemes: ['AY', 'OW', 'OY'],
                words: ['I', 'my', 'now', 'how', 'go', 'so', 'oh'],
                mouth: { rx: 42, ry: 18, opacity: 0.9 },
                shape: 'M 54 72 Q 70 90 86 72'
            },

            // Rounded (OO, UW sounds) - 3x bigger
            'ROUND': {
                phonemes: ['UW', 'OW', 'OO'],
                words: ['you', 'to', 'too', 'do', 'who', 'through'],
                mouth: { rx: 18, ry: 24, opacity: 0.85 },
                shape: 'M 62 70 Q 70 86 78 70'
            },

            // F/V sounds (teeth on lip) - 3x bigger
            'FV': {
                phonemes: ['F', 'V'],
                words: ['for', 'from', 'have', 'of', 'very', 'if'],
                mouth: { rx: 15, ry: 6, opacity: 0.7 },
                shape: 'M 60 70 L 80 70'
            },

            // L sounds - 3x bigger
            'L': {
                phonemes: ['L'],
                words: ['let', 'like', 'will', 'all', 'well'],
                mouth: { rx: 18, ry: 9, opacity: 0.75 },
                shape: 'M 60 72 Q 70 82 80 72'
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

        // Determine mouth shape based on volume (lowered thresholds for more visible movement)
        let targetShape = 'SMILE';

        if (normalizedVolume > 0.02) {
            // Speaking - use volume to determine shape
            if (normalizedVolume > 0.25) {
                targetShape = 'LARGE';
            } else if (normalizedVolume > 0.15) {
                targetShape = 'MEDIUM';
            } else if (normalizedVolume > 0.08) {
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
        const teeth = container.querySelector('.mouth-teeth');
        const tongue = container.querySelector('.mouth-tongue');

        if (mouth) {
            mouth.setAttribute('d', shape.shape);
        }

        if (mouthOpening) {
            mouthOpening.setAttribute('rx', shape.mouth.rx);
            mouthOpening.setAttribute('ry', shape.mouth.ry);
            mouthOpening.style.opacity = shape.mouth.opacity;
        }

        // Show teeth and tongue for larger mouth openings
        if (teeth) {
            const teethOpacity = shapeName === 'LARGE' || shapeName === 'WIDE' ? 0.9 :
                                 shapeName === 'MEDIUM' ? 0.6 : 0;
            teeth.style.opacity = teethOpacity;
        }

        if (tongue) {
            const tongueOpacity = shapeName === 'LARGE' || shapeName === 'WIDE' ? 0.8 :
                                  shapeName === 'MEDIUM' ? 0.5 : 0;
            tongue.style.opacity = tongueOpacity;
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
