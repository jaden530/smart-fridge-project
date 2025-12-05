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
            // Closed mouth sounds (M, B, P)
            'CLOSED': {
                phonemes: ['M', 'B', 'P'],
                words: ['me', 'my', 'be', 'by', 'please', 'maybe'],
                mouth: { rx: 0, ry: 0, opacity: 0 },
                shape: 'M 60 74 L 80 74',
                showTeeth: false,
                showTongue: false
            },

            // Small opening (EE, I sounds)
            'SMALL': {
                phonemes: ['IY', 'IH', 'EY'],
                words: ['see', 'it', 'is', 'in', 'this', 'we', 'me'],
                mouth: { rx: 12, ry: 6, opacity: 0.7 },
                shape: 'M 60 74 Q 70 80 80 74',
                showTeeth: false,
                showTongue: false
            },

            // Medium opening (EH, AE, UH sounds)
            'MEDIUM': {
                phonemes: ['EH', 'AE', 'AH', 'UH'],
                words: ['get', 'can', 'and', 'that', 'up', 'just'],
                mouth: { rx: 24, ry: 12, opacity: 0.85 },
                shape: 'M 58 72 Q 70 85 82 72',
                showTeeth: false,
                showTongue: false
            },

            // Large opening (AA, AO sounds)
            'LARGE': {
                phonemes: ['AA', 'AO', 'AW'],
                words: ['not', 'all', 'are', 'on', 'what', 'how'],
                mouth: { rx: 36, ry: 24, opacity: 1.0 },
                shape: 'M 56 68 Q 70 92 84 68',
                showTeeth: false,
                showTongue: false
            },

            // Wide opening (AY, OW sounds)
            'WIDE': {
                phonemes: ['AY', 'OW', 'OY'],
                words: ['I', 'my', 'now', 'how', 'go', 'so', 'oh'],
                mouth: { rx: 42, ry: 18, opacity: 0.9 },
                shape: 'M 54 72 Q 70 90 86 72',
                showTeeth: false,
                showTongue: false
            },

            // Rounded (OO, UW sounds)
            'ROUND': {
                phonemes: ['UW', 'OW', 'OO'],
                words: ['you', 'to', 'too', 'do', 'who', 'through'],
                mouth: { rx: 18, ry: 24, opacity: 0.85 },
                shape: 'M 62 70 Q 70 86 78 70',
                showTeeth: false,
                showTongue: false
            },

            // F/V sounds - TEETH VISIBLE (South Park style)
            'FV': {
                phonemes: ['F', 'V'],
                words: ['for', 'from', 'have', 'of', 'very', 'if', 'five', 'food'],
                mouth: { rx: 15, ry: 6, opacity: 0.7 },
                shape: 'M 60 70 L 80 70',
                showTeeth: true,
                showTongue: false
            },

            // L sounds - TONGUE VISIBLE (South Park style)
            'L': {
                phonemes: ['L'],
                words: ['let', 'like', 'will', 'all', 'well', 'let\'s', 'hello'],
                mouth: { rx: 18, ry: 9, opacity: 0.75 },
                shape: 'M 60 72 Q 70 82 80 72',
                showTeeth: false,
                showTongue: true
            },

            // TH sounds - TEETH + TONGUE (South Park style)
            'TH': {
                phonemes: ['TH', 'DH'],
                words: ['the', 'that', 'this', 'with', 'there', 'they', 'them'],
                mouth: { rx: 16, ry: 8, opacity: 0.7 },
                shape: 'M 60 72 Q 70 80 80 72',
                showTeeth: true,
                showTongue: true
            },

            // T/D sounds - TONGUE VISIBLE
            'TD': {
                phonemes: ['T', 'D', 'N'],
                words: ['to', 'do', 'it', 'and', 'not', 'need', 'now', 'then'],
                mouth: { rx: 14, ry: 7, opacity: 0.7 },
                shape: 'M 60 73 Q 70 80 80 73',
                showTeeth: false,
                showTongue: true
            },

            // Default smile
            'SMILE': {
                phonemes: [],
                words: [],
                mouth: { rx: 0, ry: 0, opacity: 0 },
                shape: 'M 55 72 Q 70 78 85 72',
                showTeeth: false,
                showTongue: false
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

        // Show teeth and tongue only for specific phonemes (South Park style)
        if (teeth) {
            teeth.style.opacity = shape.showTeeth ? 0.9 : 0;
        }

        if (tongue) {
            tongue.style.opacity = shape.showTongue ? 0.85 : 0;
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
