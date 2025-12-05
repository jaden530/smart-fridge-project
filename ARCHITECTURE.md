# Smart Fridge Project - Architecture Documentation

## 🏗️ System Architecture

This document describes the scalable, production-ready architecture for the Smart Fridge project.

---

## Overview

The Smart Fridge is a **multi-platform AI assistant** for refrigerator management with:
- Animated avatar interface
- Voice and text interaction
- Real-time inventory management
- Cross-platform support (Web, Kiosk, Mobile planned)

---

## Core Components

### 1. **Backend (Flask + Python)**
Location: `/src/main.py`

**Key Features:**
- RESTful API endpoints
- Server-Sent Events (SSE) for real-time streaming
- OpenAI GPT-4o-mini integration with function calling
- SQLAlchemy ORM for database
- User authentication with Flask-Login

**Architecture Pattern:**
- MVC-style with service layer
- Modular route handlers
- Tool/action registry for extensibility

### 2. **Frontend (Vanilla JS + Jinja2)**
Location: `/templates/`

**Component Structure:**
```
templates/
├── components/
│   ├── avatar.html          # Animated avatar (SVG + animations)
│   ├── chat_widget.html     # Chat interface with action handlers
│   └── weather_widget.html  # Weather display
├── dashboard.html           # Main dashboard
└── base.html               # Layout template
```

**Key Systems:**
- Avatar rendering and animation engine
- Chat streaming with SSE
- Action execution framework
- TTS queue management
- LocalStorage persistence

### 3. **Database (SQLAlchemy)**
Location: `/models.py`

**Models:**
- User (authentication, preferences)
- InventoryItem (food tracking)
- NutritionLog (health tracking)
- Family (multi-user support)

---

## AI Assistant Integration

### OpenAI Function Calling

The assistant uses **OpenAI's function calling API** (not text-based hacks) for reliable, type-safe actions.

**Available Tools:**

```python
# Backend: src/main.py lines 686-767
tools = [
    "navigate_to_page",      # Navigate user to specific pages
    "add_inventory_item",    # Add food to inventory
    "remove_inventory_item", # Remove food from inventory
    "highlight_element",     # Pulse UI elements
    "trigger_feature"        # Trigger app features
]
```

**How It Works:**

1. **User sends message** → Frontend `/chat/stream`
2. **GPT processes** → Decides if tools needed
3. **Function call** → Proper JSON parameters
4. **Backend translates** → Compatible action format
5. **Frontend executes** → Action handlers run

**Backwards Compatibility:**
Function calls are translated to action commands for frontend:
```
navigate_to_page({page: "dashboard"}) → [[NAVIGATE:dashboard]]
add_inventory_item({item: "carrot", qty: 2}) → [[ADD_ITEM:carrot,2,pcs]]
```

### Emotion System

The avatar displays **real-time emotions** using markers:

```
[HAPPY]     → Big smile, blush
[EXCITED]   → Huge smile, raised eyebrows, blush
[THINKING]  → Straight mouth, one eyebrow raised
[SURPRISED] → Small O mouth, wide eyes, raised eyebrows
[CONCERNED] → Slight frown, worried eyebrows
```

**Markers are:**
- Hidden from user display
- Parsed out of response text
- Trigger facial animations immediately

---

## Avatar System

### Component: `avatar.html` & `chat_widget.html`

**Architecture:**
- **SVG-based rendering** (scalable, lightweight)
- **Animation state machine** for expressions
- **Audio-reactive lip sync** (Web Audio API)
- **Phoneme mapping** for word-accurate mouth shapes

**Lip Sync System:**

```javascript
// Hybrid approach: Audio volume + text phonemes
1. Audio analyzer detects volume (when to move)
2. Text parser provides phonemes (what shape to show)
3. Frame-based timing (8 frames per character)
4. Result: Perfect sync with accurate shapes
```

**Mouth Shapes:**
```
CLOSED    → M, B, P sounds
WIDE      → A, AH vowels
ROUND     → O, OO, W sounds
E_SHAPE   → E, I, Y vowels
TH_SOUND  → Teeth + tongue visible
F_SOUND   → Teeth on lower lip
S_SOUND   → Teeth visible
L_SOUND   → Tongue visible
```

**Special Features:**
- South Park-style teeth/tongue (appear only when needed)
- Smile OR opening (never both - prevents blob overlay)
- Smooth transitions between expressions
- Eye tracking (pupils follow mouse)

---

## Action Execution Framework

### Frontend: Action Handlers
Location: `templates/components/chat_widget.html` lines 1421-1642

**Action Types:**

| Action | Purpose | Example |
|--------|---------|---------|
| `NAVIGATE` | Page navigation | Go to recipes page |
| `HIGHLIGHT` | UI highlighting | Show capture button |
| `ADD_ITEM` | Inventory add | Add 2 carrots |
| `REMOVE_ITEM` | Inventory remove | Remove milk |
| `ACTION` | Feature trigger | Capture photo |

**Execution Flow:**

```javascript
// 1. Parse action from response
parseEmotionsFromText(text) → {cleanText, emotions, actions}

// 2. Execute actions
executeAssistantActions(actions)

// 3. Specific handlers
navigateToPage(page)       → window.location.href = url
highlightElement(id)       → CSS animation + scroll
addInventoryItem(...)      → POST /api/inventory/add
removeInventoryItem(...)   → POST /api/inventory/remove
triggerFeature(feature)    → Call existing functions
```

**UI Highlighting:**
```css
.assistant-highlight {
    animation: assistant-pulse 2s ease-in-out 3;
    box-shadow: 0 0 0 20px rgba(102, 126, 234, 0);
    transform: scale(1.05);
}
```
- 3 pulses
- Purple gradient glow
- Smooth scroll to center
- Auto-remove after 6s

---

## Communication Layer

### Server-Sent Events (SSE)

**Why SSE over WebSocket:**
- Simpler (one-directional streaming)
- Built into HTTP (no extra protocol)
- Perfect for chat streaming
- Easy to scale

**Flow:**

```
Frontend          Backend
   |                |
   |-- POST msg --->|
   |                | OpenAI Streaming
   |<-- SSE chunk --|
   |<-- SSE chunk --|
   |<-- SSE done ---|
   |                |
```

**Event Types:**
```
data: <text content>           # Text to display
event: done\ndata: <full>      # Completion signal
event: error\ndata: <error>    # Error handling
```

### Future: WebSocket Addition

**When needed:** Voice commands, real-time sync, bidirectional

**Plan:**
```python
# Backend
from flask_socketio import SocketIO
socketio = SocketIO(app)

@socketio.on('voice_input')
def handle_voice(data):
    # Process voice, interrupt current TTS
    pass
```

```javascript
// Frontend
const socket = io();
socket.on('avatar_command', (cmd) => {
    // Real-time avatar control
});
```

---

## Multi-Platform Strategy

### Shared Core Logic

**Platform-Agnostic Components:**
- API client (service layer)
- Action handlers
- State management
- Avatar rendering logic

**Platform-Specific:**
- UI framework (Web: Vanilla JS, Mobile: React Native, Kiosk: Electron)
- Input methods (Touch, Voice, Keyboard)
- Screen sizes and orientations

### Planned Architecture:

```
shared/
├── api/
│   ├── client.js           # API calls
│   ├── auth.js             # Authentication
│   └── inventory.js        # Inventory service
├── avatar/
│   ├── renderer.js         # Avatar logic
│   ├── animations.js       # Animation state
│   └── lipSync.js          # Mouth sync
├── actions/
│   └── registry.js         # Action handlers
└── state/
    └── store.js            # Global state

platforms/
├── web/                    # Current implementation
├── mobile/                 # React Native (future)
│   ├── ios/
│   └── android/
└── kiosk/                  # Electron (future)
    └── fullscreen mode
```

---

## Scalability Plan

### Phase 1: Current (✅ Implemented)
- OpenAI function calling
- Modular action system
- Backwards-compatible architecture
- SSE streaming
- Avatar animations

### Phase 2: Production Ready (Next)
- [ ] Separate avatar into standalone module
- [ ] Create API service layer
- [ ] Add WebSocket support
- [ ] State management (Zustand/Redux)
- [ ] Component separation

### Phase 3: Multi-Platform (Future)
- [ ] React Native mobile app
- [ ] Electron kiosk mode
- [ ] Shared component library
- [ ] Platform abstraction layer

### Phase 4: Advanced Features (Future)
- [ ] Voice wake word detection
- [ ] Auto-ordering integration
- [ ] Advanced avatar (Lottie/Rive animations)
- [ ] Avatar movement around screen
- [ ] Custom ML models for food recognition

---

## Adding New Features

### How to Add a New Tool/Action

**1. Define Tool (Backend):**

```python
# src/main.py - Add to tools array
{
    "type": "function",
    "function": {
        "name": "create_shopping_list",
        "description": "Create a shopping list from missing ingredients",
        "parameters": {
            "type": "object",
            "properties": {
                "recipe_id": {"type": "string"}
            },
            "required": ["recipe_id"]
        }
    }
}
```

**2. Map to Action (Backend):**

```python
# src/main.py - Add to action_map
action_map = {
    # ... existing actions
    "create_shopping_list": {
        "type": "SHOPPING_LIST",
        "params": args.get("recipe_id", "")
    }
}
```

**3. Handle Action (Frontend):**

```javascript
// chat_widget.html - Add to executeAction()
case 'SHOPPING_LIST':
    await createShoppingList(params.trim());
    break;

// Implement handler
async function createShoppingList(recipeId) {
    const response = await fetch('/api/shopping-list/create', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ recipe_id: recipeId })
    });
    // Handle response
}
```

**4. Create API Endpoint (Backend):**

```python
@app.route('/api/shopping-list/create', methods=['POST'])
@login_required
def create_shopping_list():
    data = request.json
    recipe_id = data.get('recipe_id')
    # Create shopping list logic
    return jsonify({"success": True})
```

---

## Best Practices

### Code Organization

1. **Keep avatar logic separate** - Will need to reuse across platforms
2. **Use service layer for API calls** - Easier to mock/test
3. **Action handlers in registry** - Easy to extend
4. **Type-safe parameters** - Use OpenAI schemas
5. **Error handling everywhere** - Graceful degradation

### Performance

1. **Lazy load components** - Don't load everything at once
2. **Cache API responses** - Use localStorage/IndexedDB
3. **Optimize avatar animations** - requestAnimationFrame
4. **Debounce user input** - Reduce API calls
5. **Stream responses** - Don't wait for completion

### Security

1. **Validate all inputs** - Never trust frontend
2. **Use @login_required** - Protect API endpoints
3. **Sanitize inventory items** - Prevent injection
4. **Rate limiting** - Prevent abuse
5. **Secure API keys** - .env files, never commit

---

## Troubleshooting

### Avatar mouth not syncing
- Check audio context initialization
- Verify TTS queue is working
- Ensure analyser connected to audio element

### Function calling not working
- Check OpenAI API key
- Verify tool definitions match schema
- Look for JSON parsing errors in logs

### Actions not executing
- Check browser console for errors
- Verify action parsing regex
- Ensure API endpoints exist

### Chat history not saving
- Check localStorage quota
- Verify JSON.parse/stringify
- Test saveChatHistory() calls

---

## Resources

- **OpenAI Function Calling:** https://platform.openai.com/docs/guides/function-calling
- **Flask-SocketIO:** https://flask-socketio.readthedocs.io/
- **Web Audio API:** https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API
- **React Native:** https://reactnative.dev/

---

## Contact & Contribution

This architecture supports a **world-class commercial product**. The foundation is:
- ✅ Scalable
- ✅ Extensible
- ✅ Production-ready
- ✅ Multi-platform capable

**Key Principle:** Build features on this foundation, don't rebuild the foundation.
