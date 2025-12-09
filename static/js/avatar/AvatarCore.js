/**
 * AvatarCore.js - Main Avatar System
 *
 * Platform-independent avatar engine for Smart Fridge Assistant
 * Can be used in web, mobile, kiosk, or any JavaScript environment
 *
 * Features:
 * - SVG rendering (scalable, lightweight)
 * - Emotion system with facial expressions
 * - Audio-reactive lip sync
 * - Phoneme-based mouth shapes
 * - Eye tracking
 * - Modular, extensible design
 */

class AvatarCore {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);

        if (!this.container) {
            throw new Error(`Container element '${containerId}' not found`);
        }

        // Configuration
        this.config = {
            size: options.size || 140,
            enableEyeTracking: options.enableEyeTracking !== false,
            enableLipSync: options.enableLipSync !== false,
            enableEmotions: options.enableEmotions !== false,
            ...options
        };

        // State
        this.state = {
            currentEmotion: 'NEUTRAL',
            isSpeaking: false,
            isListening: false,
            mouthShape: 'SMILE',
            eyePosition: { x: 0, y: 0 }
        };

        // Audio context for lip sync
        this.audioContext = null;
        this.analyser = null;
        this.animationFrameId = null;

        // Initialize
        this.init();
    }

    /**
     * Initialize the avatar
     */
    init() {
        this.render();
        if (this.config.enableEyeTracking) {
            this.setupEyeTracking();
        }
    }

    /**
     * Render the SVG avatar
     */
    render() {
        const svg = this.createAvatarSVG();
        this.container.innerHTML = svg;
        this.cacheElements();
    }

    /**
     * Create SVG markup for avatar
     */
    createAvatarSVG() {
        const size = this.config.size;

        return `
            <svg width="${size}" height="${size}" viewBox="0 0 140 140" id="${this.containerId}-svg" class="avatar-svg">
                <defs>
                    <radialGradient id="${this.containerId}-glow">
                        <stop offset="0%" style="stop-color:#4CAF50;stop-opacity:0.8"/>
                        <stop offset="100%" style="stop-color:#2196F3;stop-opacity:0"/>
                    </radialGradient>
                </defs>

                <!-- Background -->
                <circle cx="70" cy="70" r="65" fill="rgba(255, 255, 255, 0.95)" class="avatar-background"/>

                <!-- Glow -->
                <circle cx="70" cy="70" r="60" fill="url(#${this.containerId}-glow)" class="avatar-glow"/>

                <!-- Body -->
                <ellipse cx="70" cy="95" rx="25" ry="30" fill="#4CAF50" class="avatar-body"/>

                <!-- Head -->
                <circle cx="70" cy="60" r="35" fill="#2196F3" class="avatar-head"/>

                <!-- Face -->
                <g class="avatar-face">
                    <!-- Eyes -->
                    <g class="eyes-container">
                        <g class="eye-left eyes-blink">
                            <ellipse cx="58" cy="55" rx="6" ry="6" fill="white"/>
                            <circle cx="58" cy="55" r="4" fill="#333" class="avatar-pupil-left"/>
                        </g>
                        <g class="eye-right eyes-blink">
                            <ellipse cx="82" cy="55" rx="6" ry="6" fill="white"/>
                            <circle cx="82" cy="55" r="4" fill="#333" class="avatar-pupil-right"/>
                        </g>
                    </g>

                    <!-- Eyebrows -->
                    <path d="M 50 47 Q 58 45 66 47" stroke="#333" stroke-width="2.5" fill="none" stroke-linecap="round" class="eyebrow-left"/>
                    <path d="M 74 47 Q 82 45 90 47" stroke="#333" stroke-width="2.5" fill="none" stroke-linecap="round" class="eyebrow-right"/>

                    <!-- Mouth system -->
                    <ellipse id="${this.containerId}-mouth-opening" cx="70" cy="76" rx="0" ry="0" fill="#2d2d2d" opacity="0" class="mouth-opening"/>

                    <g id="${this.containerId}-mouth-teeth" opacity="0" class="mouth-teeth">
                        <rect x="64" y="73" width="3" height="4" fill="white" rx="1"/>
                        <rect x="67.5" y="73" width="3" height="4" fill="white" rx="1"/>
                        <rect x="71" y="73" width="3" height="4" fill="white" rx="1"/>
                    </g>

                    <ellipse id="${this.containerId}-mouth-tongue" cx="70" cy="78" rx="5" ry="3" fill="#ff6b9d" opacity="0" class="mouth-tongue"/>

                    <path id="${this.containerId}-avatar-mouth" d="M 55 72 Q 70 78 85 72" stroke="#333" stroke-width="3" fill="none" stroke-linecap="round" class="mouth-smile"/>

                    <!-- Blush -->
                    <circle cx="48" cy="67" r="5" fill="#ff6b9d" opacity="0" class="blush-left"/>
                    <circle cx="92" cy="67" r="5" fill="#ff6b9d" opacity="0" class="blush-right"/>
                </g>

                <!-- Arms -->
                <g class="arms-group">
                    <ellipse cx="40" cy="95" rx="8" ry="20" fill="#4CAF50" class="arm-left" transform="rotate(-20 40 95)"/>
                    <ellipse cx="100" cy="95" rx="8" ry="20" fill="#4CAF50" class="arm-right" transform="rotate(20 100 95)"/>
                </g>
            </svg>
        `;
    }

    /**
     * Cache DOM elements for performance
     */
    cacheElements() {
        this.elements = {
            svg: document.getElementById(`${this.containerId}-svg`),
            mouth: document.getElementById(`${this.containerId}-avatar-mouth`),
            mouthOpening: document.getElementById(`${this.containerId}-mouth-opening`),
            mouthTeeth: document.getElementById(`${this.containerId}-mouth-teeth`),
            mouthTongue: document.getElementById(`${this.containerId}-mouth-tongue`),
            pupilLeft: this.container.querySelector('.avatar-pupil-left'),
            pupilRight: this.container.querySelector('.avatar-pupil-right'),
            eyebrowLeft: this.container.querySelector('.eyebrow-left'),
            eyebrowRight: this.container.querySelector('.eyebrow-right'),
            blushLeft: this.container.querySelector('.blush-left'),
            blushRight: this.container.querySelector('.blush-right'),
            eyes: this.container.querySelectorAll('.eyes-blink')
        };
    }

    /**
     * Set emotion/expression
     */
    setEmotion(emotion) {
        if (!this.config.enableEmotions) return;

        this.state.currentEmotion = emotion;

        const { mouth, eyebrowLeft, eyebrowRight, blushLeft, blushRight, eyes } = this.elements;

        // Reset previous styles
        this.resetEmotion();

        switch (emotion.toUpperCase()) {
            case 'HAPPY':
                mouth.setAttribute('d', 'M 55 70 Q 70 85 85 70');
                blushLeft.style.opacity = '0.6';
                blushRight.style.opacity = '0.6';
                break;

            case 'EXCITED':
                mouth.setAttribute('d', 'M 52 68 Q 70 90 88 68');
                eyebrowLeft.setAttribute('d', 'M 50 43 Q 58 40 66 43');
                eyebrowRight.setAttribute('d', 'M 74 43 Q 82 40 90 43');
                blushLeft.style.opacity = '0.8';
                blushRight.style.opacity = '0.8';
                break;

            case 'THINKING':
                mouth.setAttribute('d', 'M 58 74 L 82 74');
                eyebrowLeft.setAttribute('d', 'M 50 45 Q 58 43 66 47');
                eyebrowRight.setAttribute('d', 'M 74 49 Q 82 47 90 47');
                break;

            case 'SURPRISED':
                mouth.setAttribute('d', 'M 65 75 Q 70 82 75 75');
                eyebrowLeft.setAttribute('d', 'M 50 42 Q 58 38 66 42');
                eyebrowRight.setAttribute('d', 'M 74 42 Q 82 38 90 42');
                eyes.forEach(eye => eye.style.transform = 'scale(1.2)');
                break;

            case 'CONCERNED':
                mouth.setAttribute('d', 'M 55 76 Q 70 72 85 76');
                eyebrowLeft.setAttribute('d', 'M 50 49 Q 58 46 66 45');
                eyebrowRight.setAttribute('d', 'M 74 45 Q 82 46 90 49');
                break;

            default:
                // NEUTRAL
                this.resetEmotion();
        }
    }

    /**
     * Reset to neutral expression
     */
    resetEmotion() {
        const { mouth, eyebrowLeft, eyebrowRight, blushLeft, blushRight, eyes } = this.elements;

        mouth.setAttribute('d', 'M 55 72 Q 70 78 85 72');
        eyebrowLeft.setAttribute('d', 'M 50 47 Q 58 45 66 47');
        eyebrowRight.setAttribute('d', 'M 74 47 Q 82 45 90 47');
        blushLeft.style.opacity = '0';
        blushRight.style.opacity = '0';
        eyes.forEach(eye => eye.style.transform = '');
    }

    /**
     * Setup eye tracking (pupils follow mouse)
     */
    setupEyeTracking() {
        document.addEventListener('mousemove', (e) => {
            const svg = this.elements.svg;
            if (!svg) return;

            const rect = svg.getBoundingClientRect();
            const avatarCenterX = rect.left + rect.width / 2;
            const avatarCenterY = rect.top + rect.height / 2.5;

            const angle = Math.atan2(e.clientY - avatarCenterY, e.clientX - avatarCenterX);
            const distance = Math.min(
                Math.hypot(e.clientX - avatarCenterX, e.clientY - avatarCenterY) / 150,
                2.5
            );

            const moveX = Math.cos(angle) * distance;
            const moveY = Math.sin(angle) * distance;

            this.state.eyePosition = { x: moveX, y: moveY };

            if (this.elements.pupilLeft && this.elements.pupilRight) {
                this.elements.pupilLeft.style.transform = `translate(${moveX}px, ${moveY}px)`;
                this.elements.pupilRight.style.transform = `translate(${moveX}px, ${moveY}px)`;
            }
        });
    }

    /**
     * Start speaking with lip sync
     */
    startSpeaking(audioElement, text) {
        if (!this.config.enableLipSync) return;

        this.state.isSpeaking = true;
        this.state.currentText = text;

        // Initialize audio context if needed
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;

            const source = this.audioContext.createMediaElementSource(audioElement);
            source.connect(this.analyser);
            this.analyser.connect(this.audioContext.destination);
        }

        this.animateLipSync();
    }

    /**
     * Stop speaking
     */
    stopSpeaking() {
        this.state.isSpeaking = false;
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
        }
        this.setMouthShape('SMILE');
    }

    /**
     * Animate lip sync (hybrid: audio + phonemes)
     */
    animateLipSync() {
        // This will be implemented by AvatarLipSync.js
        // Placeholder for modular design
    }

    /**
     * Set mouth shape
     */
    setMouthShape(shape) {
        // Mouth shapes defined by AvatarAnimations.js
        // Placeholder for modular design
    }

    /**
     * Destroy avatar and cleanup
     */
    destroy() {
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
        }
        if (this.audioContext) {
            this.audioContext.close();
        }
        this.container.innerHTML = '';
    }

    /**
     * Get current state
     */
    getState() {
        return { ...this.state };
    }
}

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AvatarCore;
}
