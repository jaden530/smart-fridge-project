# Smart Fridge - Modular JavaScript Architecture

## 📁 Directory Structure

```
static/js/
├── avatar/
│   └── AvatarCore.js          # Standalone avatar system
├── services/
│   └── ApiService.js          # Centralized API calls
├── actions/
│   └── ActionRegistry.js      # Extensible action system
└── state/
    └── (future) AppState.js   # State management
```

---

## 🎯 Core Modules

### 1. **AvatarCore.js** - Avatar System

**Platform-independent avatar engine** that works everywhere.

**Features:**
- SVG rendering (scalable, lightweight)
- Emotion system with facial expressions
- Audio-reactive lip sync
- Phoneme-based mouth shapes
- Eye tracking (pupils follow mouse)
- Modular, extensible design

**Usage:**

```javascript
// Create avatar
const avatar = new AvatarCore('avatar-container', {
    size: 140,
    enableEyeTracking: true,
    enableLipSync: true,
    enableEmotions: true
});

// Set emotions
avatar.setEmotion('HAPPY');     // Big smile + blush
avatar.setEmotion('EXCITED');   // Huge smile + raised eyebrows
avatar.setEmotion('THINKING');  // Straight mouth + pondering
avatar.setEmotion('SURPRISED'); // O mouth + wide eyes
avatar.setEmotion('CONCERNED'); // Frown + worried eyebrows

// Start speaking with lip sync
const audio = document.getElementById('audio-element');
avatar.startSpeaking(audio, "Hello! I'm speaking!");

// Stop speaking
avatar.stopSpeaking();

// Get state
const state = avatar.getState();
console.log(state.currentEmotion); // 'HAPPY'

// Cleanup
avatar.destroy();
```

**Configuration Options:**

```javascript
{
    size: 140,                    // Avatar size in pixels
    enableEyeTracking: true,      // Pupils follow mouse
    enableLipSync: true,          // Audio-reactive mouth
    enableEmotions: true          // Facial expressions
}
```

**Available Emotions:**
- `NEUTRAL` - Default expression
- `HAPPY` - Smile + blush
- `EXCITED` - Big smile + raised eyebrows + blush
- `THINKING` - Straight mouth + one eyebrow raised
- `SURPRISED` - O mouth + wide eyes + raised eyebrows
- `CONCERNED` - Frown + worried eyebrows

---

### 2. **ApiService.js** - API Layer

**Centralized API communication** with error handling.

**Features:**
- Clean async/await interface
- Automatic error handling
- Type-safe requests
- Easy to mock for testing
- All endpoints in one place

**Usage:**

```javascript
// Import (or use global singleton)
// const api = apiService;

// Inventory operations
await apiService.addInventoryItem('carrot', 2, 'pcs');
await apiService.removeInventoryItem('milk');
const inventory = await apiService.getInventory();
const expiring = await apiService.getExpiringItems(3);

// Chat operations
const response = await apiService.streamChat('What recipes can I make?', {
    history: chatHistory,
    weather: currentWeather,
    location: userLocation,
    currentPage: 'dashboard'
});

// TTS generation
const tts = await apiService.generateTTS('Hello world');

// Weather
const weather = await apiService.getWeather(lat, lon);

// Recipes
const recipes = await apiService.searchRecipes({
    ingredients: ['chicken', 'rice'],
    dietary_restrictions: ['gluten-free']
});

// Features
await apiService.captureImage();
await apiService.detectObjects();
await apiService.simulateDoorCycle();

// Web search
const results = await apiService.webSearch('best cooking tips');
```

**Adding New Endpoints:**

```javascript
// In ApiService.js
async myNewEndpoint(data) {
    return this.post('/api/my-endpoint', data);
}

// Usage
await apiService.myNewEndpoint({ foo: 'bar' });
```

---

### 3. **ActionRegistry.js** - Action System

**Extensible action registry** for assistant commands.

**Features:**
- Easy registration of new actions
- Before/after/error hooks
- Action history/logging
- Type-safe handlers
- Built-in actions ready

**Usage:**

```javascript
// Execute built-in actions
await actionRegistry.execute('NAVIGATE', 'dashboard');
await actionRegistry.execute('HIGHLIGHT', 'capture-btn');
await actionRegistry.execute('ADD_ITEM', 'carrot,2,pcs');
await actionRegistry.execute('REMOVE_ITEM', 'milk');
await actionRegistry.execute('ACTION', 'capture');

// Register custom action
actionRegistry.register('SEND_EMAIL', async (params) => {
    const [recipient, subject, body] = params.split(',');
    // Send email logic
    return { success: true, recipient };
}, {
    description: 'Send email to user',
    schema: { recipient: 'string', subject: 'string', body: 'string' }
});

// Execute custom action
await actionRegistry.execute('SEND_EMAIL', 'user@example.com,Hello,Test');

// Add hooks
actionRegistry.addHook('before', (data) => {
    console.log(`About to execute: ${data.actionType}`);
});

actionRegistry.addHook('after', (data) => {
    console.log(`Completed: ${data.actionType}`, data.result);
});

actionRegistry.addHook('error', (data) => {
    console.error(`Failed: ${data.actionType}`, data.error);
});

// View history
const history = actionRegistry.getHistory(10);

// List all actions
const actions = actionRegistry.listActions();
console.log(actions); // ['NAVIGATE', 'HIGHLIGHT', 'ADD_ITEM', ...]
```

**Built-in Actions:**

| Action | Params | Description |
|--------|--------|-------------|
| `NAVIGATE` | page name | Navigate to page |
| `HIGHLIGHT` | element ID | Pulse UI element |
| `ADD_ITEM` | name,qty,unit | Add to inventory |
| `REMOVE_ITEM` | name | Remove from inventory |
| `ACTION` | feature name | Trigger feature |

---

## 🚀 How to Use in Your App

### Web App (Current)

```html
<!-- Load modules -->
<script src="/static/js/avatar/AvatarCore.js"></script>
<script src="/static/js/services/ApiService.js"></script>
<script src="/static/js/actions/ActionRegistry.js"></script>

<script>
// Initialize avatar
const avatar = new AvatarCore('my-avatar-container');

// Use API service
async function loadInventory() {
    const items = await apiService.getInventory();
    console.log(items);
}

// Execute actions
async function handleAssistantCommand(action, params) {
    await actionRegistry.execute(action, params);
}
</script>
```

### Mobile App (React Native - Future)

```javascript
// Import modules
import AvatarCore from './avatar/AvatarCore';
import apiService from './services/ApiService';
import actionRegistry from './actions/ActionRegistry';

// Use in React component
function MyComponent() {
    useEffect(() => {
        const avatar = new AvatarCore('avatar-container');
        avatar.setEmotion('HAPPY');

        return () => avatar.destroy();
    }, []);

    const handleAction = async () => {
        await actionRegistry.execute('ADD_ITEM', 'carrot,2,pcs');
    };

    return <View>...</View>;
}
```

### Kiosk Mode (Electron - Future)

```javascript
// Same modules work in Electron!
const { AvatarCore, apiService, actionRegistry } = require('./js');

// Full screen avatar
const avatar = new AvatarCore('fullscreen-avatar', {
    size: 500  // Larger for kiosk
});

// Voice command integration
voiceService.on('command', async (command) => {
    await actionRegistry.execute(command.action, command.params);
});
```

---

## 🎨 Benefits of Modular Architecture

### ✅ **Easy to Extend**

Add new features without touching existing code:

```javascript
// Add new action in 5 minutes
actionRegistry.register('ORDER_GROCERIES', async (params) => {
    const items = params.split(',');
    const orderId = await apiService.orderGroceries(items);
    return { success: true, orderId };
});
```

### ✅ **Easy to Test**

Mock dependencies easily:

```javascript
// Mock API for testing
class MockApiService extends ApiService {
    async getInventory() {
        return [{ name: 'carrot', qty: 2 }];
    }
}

const mockApi = new MockApiService();
```

### ✅ **Platform Independent**

Same code works everywhere:
- Web (✅ current)
- Mobile (🔜 React Native)
- Kiosk (🔜 Electron)
- Desktop (🔜 Any platform)

### ✅ **Easy to Debug**

Action history shows what happened:

```javascript
const history = actionRegistry.getHistory();
// See exactly what actions were executed
```

### ✅ **Team Friendly**

Clear separation of concerns:
- Avatar team works on `avatar/`
- Backend team works on `services/`
- Features team works on `actions/`
- No conflicts!

---

## 📦 Migration Guide

### From Current Implementation

The current implementation (in `chat_widget.html`) works perfectly.
This modular system is **optional** and can be migrated gradually:

**Option 1: Keep Current (Recommended for now)**
- Everything works
- No breaking changes
- Migrate when ready

**Option 2: Gradual Migration**
- Start using `ApiService` for new API calls
- Use `ActionRegistry` for new actions
- Keep old code working alongside

**Option 3: Full Migration**
- Refactor `chat_widget.html` to use modules
- Extract all avatar logic to `AvatarCore`
- Replace inline code with module imports

---

## 🔮 Future Modules

### Coming Soon:

**AppState.js** - State Management
```javascript
const state = new AppState({
    inventory: [],
    weather: null,
    user: {}
});

state.on('inventory:change', () => {
    // React to changes
});
```

**AvatarLipSync.js** - Advanced Lip Sync
```javascript
import { LipSyncEngine } from './AvatarLipSync';
const lipSync = new LipSyncEngine(audioContext);
lipSync.syncToAudio(audioElement, text);
```

**AvatarMovement.js** - Screen Movement
```javascript
import { AvatarMovement } from './AvatarMovement';
const movement = new AvatarMovement(avatar);
movement.moveTo(x, y, duration);
movement.followCursor();
```

---

## 💡 Best Practices

1. **Import what you need** - Don't load all modules if you don't use them
2. **Use singleton instances** - `apiService`, `actionRegistry` are shared
3. **Register actions early** - During app initialization
4. **Cleanup on unmount** - Always call `avatar.destroy()`
5. **Handle errors** - All async operations can fail
6. **Use hooks** - For logging, analytics, debugging

---

## 🎯 Summary

**You now have:**
- ✅ **Modular avatar system** - Works everywhere
- ✅ **Centralized API layer** - Clean, testable
- ✅ **Extensible actions** - Easy to add features
- ✅ **Platform independent** - Web, mobile, kiosk ready
- ✅ **Team friendly** - Clear separation of concerns

**Keep building features!** The foundation is solid and scales.
