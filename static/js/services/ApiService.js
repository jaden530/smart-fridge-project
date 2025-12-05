/**
 * ApiService.js - Centralized API Communication Layer
 *
 * Handles all backend API calls with:
 * - Error handling
 * - Loading states
 * - Request/response interceptors
 * - Type safety
 * - Easy to mock for testing
 */

class ApiService {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
    }

    /**
     * Generic fetch wrapper with error handling
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Handle different response types
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }

            return await response.text();
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    }

    /**
     * GET request
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;

        return this.request(url, {
            method: 'GET'
        });
    }

    /**
     * POST request
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT request
     */
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE request
     */
    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }

    // ========================================
    // Inventory API
    // ========================================

    async getInventory() {
        return this.get('/inventory');
    }

    async addInventoryItem(itemName, quantity = 1, unit = 'pcs') {
        return this.post('/api/inventory/add', {
            name: itemName,
            quantity: quantity,
            unit: unit
        });
    }

    async removeInventoryItem(itemName) {
        return this.post('/api/inventory/remove', {
            name: itemName
        });
    }

    async updateExpiryDate(itemName, newExpiry) {
        return this.post('/update-expiry', {
            item_name: itemName,
            new_expiry: newExpiry
        });
    }

    async getExpiringItems(days = 3) {
        return this.get('/expiring-soon', { days });
    }

    // ========================================
    // Chat API
    // ========================================

    /**
     * Stream chat responses with Server-Sent Events
     */
    async streamChat(message, context = {}) {
        const response = await fetch('/chat/stream', {
            method: 'POST',
            headers: this.defaultHeaders,
            body: JSON.stringify({
                message: message,
                history: context.history || [],
                weather: context.weather || null,
                location: context.location || null,
                currentPage: context.currentPage || 'unknown'
            })
        });

        if (!response.ok) {
            throw new Error(`Chat stream failed: ${response.statusText}`);
        }

        return response; // Return response for SSE processing
    }

    /**
     * Generate TTS audio for text
     */
    async generateTTS(text) {
        return this.post('/chat', {
            message: text,
            generate_audio_only: true
        });
    }

    // ========================================
    // Weather API
    // ========================================

    async getWeather(latitude, longitude) {
        return this.post('/api/weather', {
            latitude,
            longitude
        });
    }

    // ========================================
    // Recipe API
    // ========================================

    async searchRecipes(filters = {}) {
        return this.post('/api/search-recipes', filters);
    }

    async getRecipeDetails(recipeId) {
        return this.get(`/recipe/${recipeId}`);
    }

    // ========================================
    // Health API
    // ========================================

    async getHealthDashboard() {
        return this.get('/health-data');
    }

    async logNutrition(data) {
        return this.post('/log-nutrition', data);
    }

    // ========================================
    // Feature Actions
    // ========================================

    async captureImage() {
        return this.post('/capture');
    }

    async detectObjects() {
        return this.post('/detect');
    }

    async simulateDoorCycle() {
        return this.post('/api/simulate-door-cycle');
    }

    // ========================================
    // Web Search (for assistant)
    // ========================================

    async webSearch(query) {
        return this.post('/api/search', { query });
    }
}

// Singleton instance
const apiService = new ApiService();

// Export for use (Node.js)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = apiService;
}

// Make available globally for browsers
if (typeof window !== 'undefined') {
    window.apiService = apiService;
}
