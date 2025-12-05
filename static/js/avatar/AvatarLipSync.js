/**
 * AvatarLipSync.js - South Park Style Lip Sync
 *
 * RESTORED from working pre-refactor version
 * Combines audio volume analysis with character-by-character phoneme mapping
 */

class AvatarLipSync {
    constructor(avatarCore) {
        this.avatarCore = avatarCore;

        // Audio analysis
        this.audioContext = null;
        this.analyser = null;
        this.animationFrameId = null;

        // Lip sync state
        this.currentText = '';
        this.charIndex = 0;
        this.lastVolume = 0;
        this.volumeThreshold = 15;

        // Mouth shapes (ORIGINAL working version)
        this.MOUTH_SHAPES = {
            // Bilabial (M, B, P) - Lips closed
            CLOSED: {
                smilePath: 'M 58 74 L 82 74',
                smileVisible: true,
                opening: { opacity: 0, rx: 0, ry: 0 },
                teeth: { visible: false },
                tongue: { visible: false }
            },

            // Open vowels (A, AH) - Wide open
            WIDE: {
                smilePath: 'M 52 70 Q 70 72 88 70',
                smileVisible: true,
                opening: { opacity: 1, rx: 13, ry: 9, cy: 77 },
                teeth: { visible: false },
                tongue: { visible: false }
            },

            // Round vowels (O, OO, W) - Round opening
            ROUND: {
                smilePath: 'M 60 72 Q 70 73 80 72',
                smileVisible: true,
                opening: { opacity: 1, rx: 8, ry: 8, cy: 76 },
                teeth: { visible: false },
                tongue: { visible: false }
            },

            // E/I vowels - Smile with opening
            E_SHAPE: {
                smilePath: 'M 54 71 Q 70 75 86 71',
                smileVisible: true,
                opening: { opacity: 1, rx: 11, ry: 6, cy: 76 },
                teeth: { visible: false },
                tongue: { visible: false }
            },

            // TH sound - Teeth visible, tongue between
            TH_SOUND: {
                smilePath: 'M 56 72 Q 70 74 84 72',
                smileVisible: true,
                opening: { opacity: 0.6, rx: 9, ry: 5, cy: 76 },
                teeth: { visible: true, opacity: 1 },
                tongue: { visible: true, opacity: 0.9, cy: 76, ry: 2 }
            },

            // F/V sound - Teeth on lower lip
            F_SOUND: {
                smilePath: 'M 58 73 Q 70 75 82 73',
                smileVisible: true,
                opening: { opacity: 0.5, rx: 8, ry: 4, cy: 76 },
                teeth: { visible: true, opacity: 0.9, y: 74 },
                tongue: { visible: false }
            },

            // S sound - Teeth visible, narrow opening
            S_SOUND: {
                smilePath: 'M 56 73 Q 70 74 84 73',
                smileVisible: true,
                opening: { opacity: 0.7, rx: 10, ry: 3, cy: 75 },
                teeth: { visible: true, opacity: 1 },
                tongue: { visible: false }
            },

            // L sound - Tongue visible
            L_SOUND: {
                smilePath: 'M 56 72 Q 70 76 84 72',
                smileVisible: true,
                opening: { opacity: 0.8, rx: 9, ry: 5, cy: 76 },
                teeth: { visible: false },
                tongue: { visible: true, opacity: 0.8, cy: 75, ry: 2 }
            },

            // Small opening (default consonants)
            SMALL: {
                smilePath: 'M 56 72 Q 70 76 84 72',
                smileVisible: true,
                opening: { opacity: 0.8, rx: 7, ry: 5, cy: 76 },
                teeth: { visible: false },
                tongue: { visible: false }
            },

            // Resting smile
            SMILE: {
                smilePath: 'M 55 72 Q 70 78 85 72',
                smileVisible: true,
                opening: { opacity: 0, rx: 0, ry: 0 },
                teeth: { visible: false },
                tongue: { visible: false }
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

        this.currentText = text.replace(/\s+/g, ''); // Remove spaces
        this.charIndex = 0;
        this.lastVolume = 0;

        // Start animation loop
        this.animate();
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
        this.setMouthShape(this.MOUTH_SHAPES.SMILE);

        this.currentText = '';
        this.charIndex = 0;
    }

    /**
     * Map character to phoneme shape
     */
    getPhonemeShape(char) {
        char = char.toUpperCase();

        // Specific consonants
        if ('MBP'.includes(char)) return this.MOUTH_SHAPES.CLOSED;
        if ('FV'.includes(char)) return this.MOUTH_SHAPES.F_SOUND;
        if ('SZ'.includes(char)) return this.MOUTH_SHAPES.S_SOUND;
        if ('L'.includes(char)) return this.MOUTH_SHAPES.L_SOUND;

        // Vowels
        if ('A'.includes(char)) return this.MOUTH_SHAPES.WIDE;
        if ('OUW'.includes(char)) return this.MOUTH_SHAPES.ROUND;
        if ('EIY'.includes(char)) return this.MOUTH_SHAPES.E_SHAPE;

        // Default
        return this.MOUTH_SHAPES.SMALL;
    }

    /**
     * Main animation loop - combines audio volume with text phonemes
     */
    animate() {
        if (!this.analyser) return;

        const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
        this.analyser.getByteFrequencyData(dataArray);

        // Calculate average volume
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;

        // Detect significant volume change (new sound)
        if (Math.abs(average - this.lastVolume) > this.volumeThreshold) {
            // Move to next character when sound changes
            if (this.charIndex < this.currentText.length && average > 10) {
                this.charIndex++;
            }
        }
        this.lastVolume = average;

        // Determine mouth shape based on current character + volume
        let shape;

        if (average < 10) {
            // Silent - close mouth
            shape = this.MOUTH_SHAPES.CLOSED;
        } else if (this.charIndex < this.currentText.length) {
            // Use phoneme from text
            const currentChar = this.currentText[this.charIndex];
            const nextChar = this.currentText[this.charIndex + 1];

            // Check for TH combination
            if (currentChar === 'T' && nextChar === 'H') {
                shape = this.MOUTH_SHAPES.TH_SOUND;
                this.charIndex++; // Skip H
            } else {
                shape = this.getPhonemeShape(currentChar);
            }

            // Adjust opening size based on volume
            if (shape.opening && average > 20) {
                shape = {...shape}; // Clone
                shape.opening = {...shape.opening}; // Clone opening
                const volumeMultiplier = Math.min(average / 50, 1.5);
                shape.opening.rx *= volumeMultiplier;
                shape.opening.ry *= volumeMultiplier;
            }
        } else {
            // Past end of text, use volume-based
            if (average < 30) {
                shape = this.MOUTH_SHAPES.SMALL;
            } else if (average < 60) {
                shape = this.MOUTH_SHAPES.ROUND;
            } else {
                shape = this.MOUTH_SHAPES.WIDE;
            }
        }

        this.setMouthShape(shape);

        // Continue animation
        this.animationFrameId = requestAnimationFrame(() => this.animate());
    }

    /**
     * Apply mouth shape to avatar
     */
    setMouthShape(shape) {
        const container = this.avatarCore.container;
        if (!container) return;

        const mouth = container.querySelector('.mouth-smile');
        const opening = container.querySelector('.mouth-opening');
        const teeth = container.querySelector('.mouth-teeth');
        const tongue = container.querySelector('.mouth-tongue');

        if (mouth && shape.smilePath) {
            mouth.setAttribute('d', shape.smilePath);
            mouth.style.opacity = shape.smileVisible ? '1' : '0';
        }

        if (opening && shape.opening) {
            opening.setAttribute('opacity', shape.opening.opacity);
            opening.setAttribute('rx', shape.opening.rx);
            opening.setAttribute('ry', shape.opening.ry);
            if (shape.opening.cy) opening.setAttribute('cy', shape.opening.cy);
        }

        if (teeth) {
            teeth.setAttribute('opacity', shape.teeth.visible ? (shape.teeth.opacity || 1) : 0);
            if (shape.teeth.y) {
                teeth.querySelectorAll('rect').forEach(rect => {
                    rect.setAttribute('y', shape.teeth.y);
                });
            }
        }

        if (tongue) {
            tongue.setAttribute('opacity', shape.tongue.visible ? (shape.tongue.opacity || 0.8) : 0);
            if (shape.tongue.cy) tongue.setAttribute('cy', shape.tongue.cy);
            if (shape.tongue.ry) tongue.setAttribute('ry', shape.tongue.ry);
        }
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
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AvatarLipSync;
}
