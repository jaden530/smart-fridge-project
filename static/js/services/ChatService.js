/**
 * ChatService.js - Chat Streaming and Message Processing
 *
 * Handles chat communication with backend including:
 * - SSE streaming responses
 * - Message parsing (emotions, actions, text)
 * - Integration with TTSService for audio
 * - Integration with ActionRegistry for commands
 * - Chat history management
 * - Event-driven updates
 */

class ChatService {
    constructor(apiService, ttsService = null, actionRegistry = null) {
        this.apiService = apiService;
        this.ttsService = ttsService;
        this.actionRegistry = actionRegistry;

        // Chat state
        this.chatHistory = [];
        this.isStreaming = false;
        this.currentMessage = '';
        this.currentEmotion = 'NEUTRAL';

        // Callbacks
        this.callbacks = {
            onMessageStart: null,
            onMessageChunk: null,
            onMessageComplete: null,
            onEmotion: null,
            onAction: null,
            onError: null
        };

        // Sentence buffering for TTS
        this.sentenceBuffer = '';
        this.sentenceEndRegex = /[.!?]\s+/;
    }

    /**
     * Set callbacks for events
     */
    setCallbacks({ onMessageStart, onMessageChunk, onMessageComplete, onEmotion, onAction, onError }) {
        if (onMessageStart) this.callbacks.onMessageStart = onMessageStart;
        if (onMessageChunk) this.callbacks.onMessageChunk = onMessageChunk;
        if (onMessageComplete) this.callbacks.onMessageComplete = onMessageComplete;
        if (onEmotion) this.callbacks.onEmotion = onEmotion;
        if (onAction) this.callbacks.onAction = onAction;
        if (onError) this.callbacks.onError = onError;
    }

    /**
     * Send a message and stream the response
     */
    async sendMessage(message, context = {}) {
        if (this.isStreaming) {
            console.warn('Already streaming a response');
            return;
        }

        try {
            this.isStreaming = true;
            this.currentMessage = '';
            this.sentenceBuffer = '';

            // Add user message to history
            this.chatHistory.push({
                role: 'user',
                content: message,
                timestamp: Date.now()
            });

            // Trigger message start callback
            if (this.callbacks.onMessageStart) {
                this.callbacks.onMessageStart({ message });
            }

            // Start streaming
            const response = await this.apiService.streamChat(message, {
                history: this.chatHistory,
                weather: context.weather,
                location: context.location,
                currentPage: context.currentPage
            });

            // Process SSE stream
            await this.processStream(response);

        } catch (error) {
            console.error('Chat error:', error);
            this.isStreaming = false;

            if (this.callbacks.onError) {
                this.callbacks.onError(error);
            }
        }
    }

    /**
     * Process SSE stream
     */
    async processStream(response) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        try {
            while (true) {
                const { done, value } = await reader.read();

                if (done) {
                    // Stream complete
                    this.handleStreamComplete();
                    break;
                }

                // Decode and add to buffer
                buffer += decoder.decode(value, { stream: true });

                // Process complete lines
                const lines = buffer.split('\n');
                buffer = lines.pop(); // Keep incomplete line in buffer

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6).trim();

                        if (data === '[DONE]') {
                            this.handleStreamComplete();
                            return;
                        }

                        await this.processMessageChunk(data);
                    }
                }
            }
        } catch (error) {
            console.error('Stream processing error:', error);
            if (this.callbacks.onError) {
                this.callbacks.onError(error);
            }
        } finally {
            this.isStreaming = false;
        }
    }

    /**
     * Process a single message chunk
     */
    async processMessageChunk(chunk) {
        // Check for emotion tags [[EMOTION:value]]
        const emotionMatch = chunk.match(/\[\[EMOTION:(.*?)\]\]/);
        if (emotionMatch) {
            const emotion = emotionMatch[1];
            this.currentEmotion = emotion;

            if (this.callbacks.onEmotion) {
                this.callbacks.onEmotion({ emotion });
            }
            return; // Don't add emotion tags to message
        }

        // Check for action tags [[ACTION_TYPE:params]]
        const actionMatch = chunk.match(/\[\[(.*?):(.*?)\]\]/);
        if (actionMatch) {
            const [, actionType, params] = actionMatch;

            if (this.callbacks.onAction) {
                this.callbacks.onAction({ actionType, params });
            }

            // Execute action if actionRegistry is available
            if (this.actionRegistry) {
                try {
                    await this.actionRegistry.execute(actionType, params);
                } catch (error) {
                    console.error('Action execution error:', error);
                }
            }
            return; // Don't add action tags to message
        }

        // Regular text chunk
        this.currentMessage += chunk;
        this.sentenceBuffer += chunk;

        // Trigger chunk callback
        if (this.callbacks.onMessageChunk) {
            this.callbacks.onMessageChunk({
                chunk,
                fullMessage: this.currentMessage,
                emotion: this.currentEmotion
            });
        }

        // Check for complete sentences and queue TTS
        this.processSentences();
    }

    /**
     * Process complete sentences for TTS
     */
    processSentences() {
        if (!this.ttsService) return;

        const match = this.sentenceBuffer.match(this.sentenceEndRegex);

        if (match) {
            const endIndex = match.index + match[0].length;
            const sentence = this.sentenceBuffer.slice(0, endIndex).trim();

            if (sentence.length > 0) {
                // Queue TTS for sentence
                this.ttsService.generateAndQueue(sentence);
            }

            // Remove processed sentence from buffer
            this.sentenceBuffer = this.sentenceBuffer.slice(endIndex);
        }
    }

    /**
     * Handle stream completion
     */
    handleStreamComplete() {
        // Process any remaining sentence buffer
        if (this.sentenceBuffer.trim().length > 0 && this.ttsService) {
            this.ttsService.generateAndQueue(this.sentenceBuffer.trim());
            this.sentenceBuffer = '';
        }

        // Add assistant message to history
        this.chatHistory.push({
            role: 'assistant',
            content: this.currentMessage,
            emotion: this.currentEmotion,
            timestamp: Date.now()
        });

        // Trigger completion callback
        if (this.callbacks.onMessageComplete) {
            this.callbacks.onMessageComplete({
                message: this.currentMessage,
                emotion: this.currentEmotion,
                history: this.getChatHistory()
            });
        }

        this.isStreaming = false;
    }

    /**
     * Stop current streaming
     */
    stop() {
        this.isStreaming = false;
        this.currentMessage = '';
        this.sentenceBuffer = '';
    }

    /**
     * Clear chat history
     */
    clearHistory() {
        this.chatHistory = [];
    }

    /**
     * Get chat history
     */
    getChatHistory(limit = null) {
        if (limit) {
            return this.chatHistory.slice(-limit);
        }
        return [...this.chatHistory];
    }

    /**
     * Get current state
     */
    getState() {
        return {
            isStreaming: this.isStreaming,
            currentMessage: this.currentMessage,
            currentEmotion: this.currentEmotion,
            historyLength: this.chatHistory.length
        };
    }

    /**
     * Set emotion manually (for UI interactions)
     */
    setEmotion(emotion) {
        this.currentEmotion = emotion;
        if (this.callbacks.onEmotion) {
            this.callbacks.onEmotion({ emotion });
        }
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChatService;
}
