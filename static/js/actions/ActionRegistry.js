/**
 * ActionRegistry.js - Extensible Action System
 *
 * Central registry for all assistant actions with:
 * - Easy registration of new actions
 * - Type-safe handlers
 * - Before/after hooks
 * - Error handling
 * - Action history/logging
 */

class ActionRegistry {
    constructor() {
        this.actions = new Map();
        this.hooks = {
            before: [],
            after: [],
            error: []
        };
        this.history = [];

        // Register built-in actions
        this.registerBuiltInActions();
    }

    /**
     * Register a new action
     */
    register(actionType, handler, options = {}) {
        if (this.actions.has(actionType)) {
            console.warn(`Action '${actionType}' is already registered. Overwriting.`);
        }

        this.actions.set(actionType, {
            handler,
            description: options.description || '',
            schema: options.schema || null,
            async: options.async !== false // Default to async
        });

        console.log(`✅ Registered action: ${actionType}`);
    }

    /**
     * Execute an action
     */
    async execute(actionType, params = {}) {
        if (!this.actions.has(actionType)) {
            throw new Error(`Action '${actionType}' not found in registry`);
        }

        const action = this.actions.get(actionType);

        try {
            // Run before hooks
            await this.runHooks('before', { actionType, params });

            // Execute action
            const result = action.async
                ? await action.handler(params)
                : action.handler(params);

            // Log to history
            this.history.push({
                type: actionType,
                params,
                result,
                timestamp: Date.now(),
                success: true
            });

            // Run after hooks
            await this.runHooks('after', { actionType, params, result });

            return result;

        } catch (error) {
            console.error(`Action execution failed [${actionType}]:`, error);

            // Log error
            this.history.push({
                type: actionType,
                params,
                error: error.message,
                timestamp: Date.now(),
                success: false
            });

            // Run error hooks
            await this.runHooks('error', { actionType, params, error });

            throw error;
        }
    }

    /**
     * Add a hook (before, after, error)
     */
    addHook(hookType, callback) {
        if (!this.hooks[hookType]) {
            throw new Error(`Invalid hook type: ${hookType}`);
        }
        this.hooks[hookType].push(callback);
    }

    /**
     * Run hooks
     */
    async runHooks(hookType, data) {
        const hooks = this.hooks[hookType] || [];
        for (const hook of hooks) {
            try {
                await hook(data);
            } catch (error) {
                console.error(`Hook error [${hookType}]:`, error);
            }
        }
    }

    /**
     * Get action history
     */
    getHistory(limit = 10) {
        return this.history.slice(-limit);
    }

    /**
     * Clear history
     */
    clearHistory() {
        this.history = [];
    }

    /**
     * List all registered actions
     */
    listActions() {
        return Array.from(this.actions.keys());
    }

    /**
     * Register built-in actions
     */
    registerBuiltInActions() {
        // NAVIGATE - Page navigation
        this.register('NAVIGATE', (params) => {
            const pageMap = {
                'dashboard': '/dashboard',
                'inventory': '/',
                'users': '/users',
                'health-dashboard': '/health-dashboard',
                'health': '/health-dashboard',
                'recipes': '/advanced-recipe-search',
                'waste-prevention': '/waste-prevention',
                'waste': '/waste-prevention',
                'preferences': '/preferences',
                'settings': '/preferences',
                'family': '/family/create'
            };

            const url = pageMap[params.toLowerCase()] || '/dashboard';
            console.log(`Navigating to: ${url}`);

            // Delay for UX (let user see message)
            setTimeout(() => {
                window.location.href = url;
            }, 1500);

            return { url, success: true };
        }, {
            description: 'Navigate to a page',
            schema: { page: 'string' }
        });

        // HIGHLIGHT - UI element highlighting
        this.register('HIGHLIGHT', (params) => {
            const elementId = params;
            let element = document.getElementById(elementId);

            // Try multiple selectors
            if (!element) {
                element = document.querySelector(`[onclick*="${elementId}"]`) ||
                          document.querySelector(`.${elementId}`);
            }

            if (!element) {
                console.warn(`Element not found: ${elementId}`);
                return { success: false, reason: 'Element not found' };
            }

            // Add highlight class
            element.classList.add('assistant-highlight');

            // Inject CSS if not exists
            if (!document.getElementById('assistant-highlight-styles')) {
                const style = document.createElement('style');
                style.id = 'assistant-highlight-styles';
                style.textContent = `
                    .assistant-highlight {
                        animation: assistant-pulse 2s ease-in-out 3;
                        position: relative;
                        z-index: 9999;
                    }
                    @keyframes assistant-pulse {
                        0%, 100% {
                            box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7);
                            transform: scale(1);
                        }
                        50% {
                            box-shadow: 0 0 0 20px rgba(102, 126, 234, 0);
                            transform: scale(1.05);
                        }
                    }
                `;
                document.head.appendChild(style);
            }

            // Scroll into view
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });

            // Remove after animation
            setTimeout(() => {
                element.classList.remove('assistant-highlight');
            }, 6000);

            return { success: true, elementId };
        }, {
            description: 'Highlight UI element with pulse',
            schema: { elementId: 'string' }
        });

        // ADD_ITEM - Add to inventory
        this.register('ADD_ITEM', async (params) => {
            const [itemName, quantity, unit] = params.split(',').map(s => s.trim());

            // Import API service (assume it's available globally or imported)
            if (typeof apiService === 'undefined') {
                throw new Error('ApiService not available');
            }

            const result = await apiService.addInventoryItem(
                itemName,
                parseFloat(quantity) || 1,
                unit || 'pcs'
            );

            // Refresh stats if function exists
            if (typeof updateStats === 'function') {
                updateStats();
            }

            return { success: true, item: itemName, quantity, unit };
        }, {
            description: 'Add item to inventory',
            schema: { itemName: 'string', quantity: 'number', unit: 'string' }
        });

        // REMOVE_ITEM - Remove from inventory
        this.register('REMOVE_ITEM', async (params) => {
            const itemName = params.trim();

            if (typeof apiService === 'undefined') {
                throw new Error('ApiService not available');
            }

            const result = await apiService.removeInventoryItem(itemName);

            // Refresh stats
            if (typeof updateStats === 'function') {
                updateStats();
            }

            return { success: true, item: itemName };
        }, {
            description: 'Remove item from inventory',
            schema: { itemName: 'string' }
        });

        // ACTION - Trigger features
        this.register('ACTION', async (params) => {
            const featureName = params.trim().toLowerCase();

            switch (featureName) {
                case 'capture':
                case 'detect':
                    if (typeof captureAndDetect === 'function') {
                        await captureAndDetect();
                        return { success: true, feature: 'capture' };
                    }
                    break;

                case 'door-cycle':
                case 'door':
                    if (typeof simulateDoorCycle === 'function') {
                        await simulateDoorCycle();
                        return { success: true, feature: 'door-cycle' };
                    }
                    break;

                default:
                    throw new Error(`Unknown feature: ${featureName}`);
            }

            return { success: false, reason: 'Function not available' };
        }, {
            description: 'Trigger app features',
            schema: { feature: 'string' }
        });
    }
}

// Singleton instance
const actionRegistry = new ActionRegistry();

// Export for use (Node.js)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = actionRegistry;
}

// Make available globally for browsers
if (typeof window !== 'undefined') {
    window.actionRegistry = actionRegistry;
}
