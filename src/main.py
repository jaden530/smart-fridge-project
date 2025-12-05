import sys
import os
import urllib.request
import cv2
from core.module_manager import ModuleManager
from core.family_manager import FamilyManager
from camera.camera_manager import CameraManager
from ai.object_detection import ObjectDetector
from inventory.inventory_manager import InventoryManager
from recipes import find_matching_recipes, find_recipes_by_ingredients, get_recipe_details, RecipeManager
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session, Response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, User, InventoryItem, NutritionLog, HealthGoals, Family, FamilyMember, FamilyInvitation
from dotenv import load_dotenv
# OpenAI import moved to conditional block below to prevent errors when API key is missing
import io
from pydub import AudioSegment
from pydub.playback import play
import requests
import time
from forms import UserPreferencesForm, CreateFamilyForm, InviteFamilyMemberForm, UpdateFamilySettingsForm, UpdateMemberPermissionsForm
from datetime import datetime, timedelta
from waste_prevention.food_waste_manager import FoodWasteManager
from health.health_tracker import HealthTracker
from assistant.kitchen_assistant import KitchenAssistant

# Ensure the src folder is added to Python's module search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def download_file(url, file_name):
    if not os.path.exists(file_name):
        urllib.request.urlretrieve(url, file_name)

def setup_object_detection():
    model_dir = os.path.join(os.getcwd(), 'model_data')
    os.makedirs(model_dir, exist_ok=True)
    
    weights_path = os.path.join(model_dir, "yolov3.weights")
    config_path = os.path.join(model_dir, "yolov3.cfg")
    classes_path = os.path.join(model_dir, "coco.names")
    
    download_file("https://pjreddie.com/media/files/yolov3.weights", weights_path)
    download_file("https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3.cfg", config_path)
    download_file("https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names", classes_path)
    
    return weights_path, config_path, classes_path

def setup_cameras():
    camera_manager = CameraManager()
    camera_manager.add_camera('main', 'https://media.gettyimages.com/id/2151094361/photo/healthy-rainbow-colored-fruits-and-vegetables-background.webp?s=2048x2048&w=gi&k=20&c=eW6_Tp52NF3I_JJhYoFanTk9F72K8y_ngxkhyZMNLYI=')
    return camera_manager

# Load environment variables from current working directory (where .exe is located)
# This ensures .env works when running as PyInstaller bundle
env_path = os.path.join(os.getcwd(), '.env')
load_dotenv(env_path)
print(f"Loading .env from: {env_path}")
if os.path.exists(env_path):
    print("✅ .env file found!")
else:
    print("ℹ️  No .env file found (optional)")

# Initialize OpenAI client (optional - only if API key provided)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = None

# Only import and initialize OpenAI if we have a valid API key
if OPENAI_API_KEY and OPENAI_API_KEY.strip():
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        print("✅ OpenAI client initialized (voice & chat features enabled)")
    except ImportError:
        print("⚠️  OpenAI package not installed - voice & chat features disabled")
        client = None
    except Exception as e:
        print(f"⚠️  OpenAI initialization failed: {e}")
        client = None
else:
    print("ℹ️  No OpenAI API key - voice & chat features disabled")
    print("   To enable: Create .env file and add OPENAI_API_KEY=your-key-here")

# Initialize Nutritionix API keys (optional)
NUTRITIONIX_APP_ID = os.getenv('NUTRITIONIX_APP_ID')
NUTRITIONIX_API_KEY = os.getenv('NUTRITIONIX_API_KEY')
if not NUTRITIONIX_APP_ID or not NUTRITIONIX_API_KEY:
    print("ℹ️  No Nutritionix API keys - nutrition lookups disabled")

# Setup paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_folder = os.path.join(base_dir, 'static')
db_path = os.path.join(base_dir, 'smartfridge.db')

# Database will be created if it doesn't exist, preserved if it does

# Initialize all managers and modules
module_manager = ModuleManager()
camera_manager = setup_cameras()
inventory_manager = InventoryManager()
family_manager = FamilyManager()


# Setup object detection
print(f"Current working directory: {os.getcwd()}")
weights_path, config_path, classes_path = setup_object_detection()
object_detector = ObjectDetector(weights_path, config_path, classes_path)

# Initialize other components
health_tracker = HealthTracker(inventory_manager)
food_waste_manager = FoodWasteManager(inventory_manager)



class RecipeAPI:
    def __init__(self):
        self.find_recipes_by_ingredients = find_recipes_by_ingredients
        self.get_recipe_details = get_recipe_details

recipe_api = RecipeAPI()
recipe_manager = RecipeManager(recipe_api)
kitchen_assistant = KitchenAssistant(inventory_manager, recipe_manager)

# Register all modules
module_manager.register_module('camera', camera_manager)
module_manager.register_module('object_detector', object_detector)
module_manager.register_module('inventory', inventory_manager)
module_manager.register_module('food_waste', food_waste_manager)
module_manager.register_module('recipe_manager', recipe_manager)
module_manager.register_module('family', family_manager)
module_manager.register_module('health_tracker', health_tracker)

# Initialize Flask app
app = Flask(__name__, static_folder=static_folder, static_url_path='/static')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback_secret_key_for_development')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)  # Initialize the `db` instance
migrate = Migrate(app, db)

from models import User, InventoryItem


# Create tables
with app.app_context():
    db.create_all()  # This will create tables based on the models


    # Create a test user if it doesn't exist
    if not User.query.filter_by(username='testuser').first():
        test_user = User(username='testuser')
        test_user.set_password('testpassword')
        db.session.add(test_user)
        db.session.commit()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    if user_id.isdigit():
        return db.session.get(User, int(user_id))
    else:
        return User.query.filter_by(username=user_id).first()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    user_inventory = inventory_manager.get_inventory(current_user.id)
    return render_template('index.html', username=current_user.username, inventory=user_inventory)

def generate_and_play_speech(text):
    if not client:
        print(f"🔇 TTS disabled (no API key): {text}")
        return None

    try:
        response = client.audio.speech.create(
            model="tts-1-hd",
            voice="alloy",
            input=text
        )

        audio_data = io.BytesIO(response.content)
        audio = AudioSegment.from_file(audio_data, format="mp3")
        play(audio)
    except Exception as e:
        print(f"⚠️  TTS error: {e}")

def estimate_portion_size(object_size):
    if object_size < 1000:  # small objects
        return "small"
    elif object_size < 5000:  # medium objects
        return "medium"
    else:  # large objects
        return "large"

def get_nutritional_info(food_item, portion_size):
    if not NUTRITIONIX_APP_ID or not NUTRITIONIX_API_KEY:
        print(f"ℹ️  Nutrition lookup disabled (no API keys): {food_item}")
        return None

    try:
        url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
        headers = {
            "x-app-id": NUTRITIONIX_APP_ID,
            "x-app-key": NUTRITIONIX_API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "query": f"{portion_size} {food_item}"
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.json()['foods'][0]
        else:
            print(f"Error getting nutritional info: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"⚠️  Nutrition API error: {e}")
        return None

@app.route('/capture', methods=['POST'])
@login_required
def capture_image():
    print("Capture Image request received")
    image = camera_manager.capture_image('main')
    if image is not None:
        img_path = os.path.join(app.static_folder, 'captured_image.jpg')
        print(f"Saving image to: {os.path.abspath(img_path)}")
        success = cv2.imwrite(img_path, image)
        if success:
            print(f"Image saved successfully. Size: {os.path.getsize(img_path)} bytes")
        else:
            print("Failed to save image")
        return jsonify({"message": "Image captured successfully", "image_path": '/static/captured_image.jpg'})
    else:
        return jsonify({"error": "Failed to capture image"})

@app.route('/detect', methods=['POST'])
@login_required
def detect_objects():
    image = camera_manager.get_last_image('main')
    if image is not None:
        detected_objects = object_detector.detect(image)
        for obj in detected_objects:
            obj['portion_size'] = estimate_portion_size(obj['box']['width'] * obj['box']['height'])
            obj['nutritional_info'] = get_nutritional_info(obj['class'], obj['portion_size'])
        
        inventory_manager.update_from_detection(current_user.id, detected_objects)
        
        # Draw bounding boxes on the image
        for obj in detected_objects:
            x, y, w, h = obj['box'].values()
            cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
            label = f"{obj['class']} {obj['confidence']:.2f}"
            cv2.putText(image, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
        
        img_path = os.path.join(app.static_folder, 'detected_image.jpg')
        cv2.imwrite(img_path, image)
        
        # Get the updated inventory
        updated_inventory = inventory_manager.get_inventory(current_user.id)
        print(f"Updated inventory after detection: {updated_inventory}")  # Add this debug print
        
        return jsonify({
            "message": "Objects detected and inventory updated",
            "objects": detected_objects,
            "image_path": '/static/detected_image.jpg',
            "inventory": updated_inventory
        })
    else:
        return jsonify({"error": "No image available for detection"})

@app.route('/health-dashboard')
@login_required
def health_dashboard():
    return render_template('health_dashboard.html')

@app.route('/health/daily-summary')
@login_required
def get_daily_summary():
    date = request.args.get('date', datetime.now().date().isoformat())
    
    # Get logs from database
    logs = NutritionLog.query.filter_by(
        user_id=current_user.id,
        date=datetime.fromisoformat(date).date()
    ).all()
    
    # Get user's goals
    goals = HealthGoals.query.filter_by(user_id=current_user.id).first()
    
    summary = {
        'total_nutrients': {
            'calories': sum(log.calories or 0 for log in logs),
            'protein': sum(log.protein or 0 for log in logs),
            'carbs': sum(log.carbs or 0 for log in logs),
            'fat': sum(log.fat or 0 for log in logs),
            'fiber': sum(log.fiber or 0 for log in logs)
        },
        'items': [{
            'item': log.item_name,
            'quantity': log.quantity,
            'time': log.timestamp.isoformat()
        } for log in logs],
        'goals': {
            'calories': goals.calorie_goal if goals else None,
            'protein': goals.protein_goal if goals else None,
            'carbs': goals.carb_goal if goals else None,
            'fat': goals.fat_goal if goals else None,
            'fiber': goals.fiber_goal if goals else None
        }
    }
    
    return jsonify(summary)

@app.route('/health/weekly-summary')
@login_required
def get_weekly_summary():
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)
    
    logs = NutritionLog.query.filter(
        NutritionLog.user_id == current_user.id,
        NutritionLog.date >= start_date,
        NutritionLog.date <= end_date
    ).all()
    
    # Group logs by date
    daily_totals = {}
    for log in logs:
        date_str = log.date.isoformat()
        if date_str not in daily_totals:
            daily_totals[date_str] = {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0,
                'fiber': 0
            }
        
        daily_totals[date_str]['calories'] += log.calories or 0
        daily_totals[date_str]['protein'] += log.protein or 0
        daily_totals[date_str]['carbs'] += log.carbs or 0
        daily_totals[date_str]['fat'] += log.fat or 0
        daily_totals[date_str]['fiber'] += log.fiber or 0
    
    # Format for chart display
    summary = {
        'days': [
            {
                'date': date,
                'nutrients': nutrients
            }
            for date, nutrients in daily_totals.items()
        ]
    }
    
    return jsonify(summary)

@app.route('/health/log-consumption', methods=['POST'])
@login_required
def log_consumption():
    data = request.json
    item_name = data.get('item')
    quantity = data.get('quantity')
    
    if not item_name or not quantity:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Get item's nutritional info from inventory
    inventory = inventory_manager.get_inventory(current_user.id)
    if item_name not in inventory:
        return jsonify({'error': 'Item not found in inventory'}), 404
        
    item_details = inventory[item_name]
    nutritional_info = item_details.get('nutritional_info', {})
    
    # Create log entry
    log = NutritionLog(
        user_id=current_user.id,
        date=datetime.now().date(),
        item_name=item_name,
        quantity=quantity,
        calories=nutritional_info.get('nf_calories', 0) * quantity,
        protein=nutritional_info.get('nf_protein', 0) * quantity,
        carbs=nutritional_info.get('nf_total_carbohydrate', 0) * quantity,
        fat=nutritional_info.get('nf_total_fat', 0) * quantity,
        fiber=nutritional_info.get('nf_dietary_fiber', 0) * quantity
    )
    
    db.session.add(log)
    db.session.commit()
    
    # Update inventory quantity
    inventory_manager.remove_item(current_user.id, item_name, quantity)
    
    return jsonify({'success': True})

@app.route('/health/goals', methods=['GET', 'POST'])
@login_required
def manage_health_goals():
    if request.method == 'POST':
        data = request.json
        goals = HealthGoals.query.filter_by(user_id=current_user.id).first()
        
        if not goals:
            goals = HealthGoals(user_id=current_user.id)
            db.session.add(goals)
            
        goals.calorie_goal = data.get('calories')
        goals.protein_goal = data.get('protein')
        goals.carb_goal = data.get('carbs')
        goals.fat_goal = data.get('fat')
        goals.fiber_goal = data.get('fiber')
        goals.updated_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'success': True})
        
    else:
        goals = HealthGoals.query.filter_by(user_id=current_user.id).first()
        if goals:
            return jsonify({
                'calories': goals.calorie_goal,
                'protein': goals.protein_goal,
                'carbs': goals.carb_goal,
                'fat': goals.fat_goal,
                'fiber': goals.fiber_goal
            })
        return jsonify({})

@app.route('/preferences', methods=['GET', 'POST'])
@login_required
def user_preferences():
    form = UserPreferencesForm()
    if form.validate_on_submit():
        current_user.dietary_preference = form.dietary_preference.data
        current_user.calorie_goal = form.calorie_goal.data
        current_user.protein_goal = form.protein_goal.data
        current_user.carb_goal = form.carb_goal.data
        current_user.fat_goal = form.fat_goal.data
        db.session.commit()
        flash('Your preferences have been updated.', 'success')
        return redirect(url_for('user_preferences'))
    elif request.method == 'GET':
        form.dietary_preference.data = current_user.dietary_preference
        form.calorie_goal.data = current_user.calorie_goal
        form.protein_goal.data = current_user.protein_goal
        form.carb_goal.data = current_user.carb_goal
        form.fat_goal.data = current_user.fat_goal
    return render_template('user_preferences.html', form=form)

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    if not client:
        return jsonify({
            "response": "Chat assistant is disabled. Add OPENAI_API_KEY to .env file to enable this feature.",
            "audio_url": None,
            "response_type": {"has_safety_tip": False, "has_technique": False, "has_suggestion": False},
            "should_demonstrate": False
        }), 503

    message = request.json.get('message')
    generate_audio_only = request.json.get('generate_audio_only', False)

    # If only generating audio (for streaming TTS), skip GPT and just create TTS
    if generate_audio_only:
        # Remove emotion markers for TTS (they're visual only)
        import re
        clean_message = re.sub(r'\[(HAPPY|EXCITED|THINKING|SURPRISED|CONCERNED)\]', '', message).strip()

        # Generate TTS directly from the provided text
        speech_response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=clean_message
        )

        # Ensure static folder exists
        os.makedirs(app.static_folder, exist_ok=True)

        # Save audio with unique name
        audio_filename = f"response_{int(time.time() * 1000)}.mp3"  # Use milliseconds for uniqueness
        audio_path = os.path.join(app.static_folder, audio_filename)
        with open(audio_path, "wb") as f:
            f.write(speech_response.content)

        return jsonify({
            "audio_url": f"/static/{audio_filename}"
        })

    # Normal chat flow with GPT
    chat_history = request.json.get('history', [])
    inventory = inventory_manager.get_inventory(current_user.id)

    # Create a string with user preferences and nutritional goals
    user_context = f"The user's dietary preference is {current_user.dietary_preference or 'not set'}. "
    user_context += f"Their daily nutritional goals are: Calories: {current_user.calorie_goal or 'not set'}, "
    user_context += f"Protein: {current_user.protein_goal or 'not set'}g, "
    user_context += f"Carbs: {current_user.carb_goal or 'not set'}g, "
    user_context += f"Fat: {current_user.fat_goal or 'not set'}g."

    # Create teaching context based on message intent
    teaching_context = ""
    if any(word in message.lower() for word in ['how to', 'teach me', 'show me', 'explain']):
        teaching_context = """
        When explaining cooking techniques or steps:
        1. Break down complex actions into simple steps
        2. Mention safety precautions when relevant
        3. Explain why certain techniques are used
        4. Provide alternative methods when available
        5. Include tips for better results
        """

    # Enhanced system prompt with emotion markers for avatar expressions
    system_prompt = """
    You are a friendly and expressive Smart Fridge Assistant! Keep responses CONCISE (under 80 words).

    CRITICAL: Add emotion markers to animate your avatar! Use these EXACT markers:
    [HAPPY] - Good news, enthusiasm, compliments
    [EXCITED] - Really great ideas, discoveries
    [THINKING] - Considering options, pondering
    [SURPRISED] - Unexpected info, interesting facts
    [CONCERNED] - Warnings, safety tips, caution

    Example: "[HAPPY] Great choice! [THINKING] For chicken, I'd suggest..."

    These markers animate your face but stay HIDDEN from the user!

    Keep responses SHORT for fast voice playback. Be:
    - Helpful and encouraging
    - Educational but concise
    - Clear and simple
    - Safety-conscious
    - Warm and friendly
    """

    # Prepare the messages for the GPT model
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"Additional Context: {user_context}"},
        {"role": "system", "content": f"Current Inventory: {inventory}"},
    ]

    # Add teaching context if relevant
    if teaching_context:
        messages.append({"role": "system", "content": teaching_context})

    # Add chat history and current message
    messages.extend(chat_history)
    messages.append({"role": "user", "content": message})

    # Use STREAMING for instant responses!
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=150,
        temperature=0.8,
        stream=True  # Enable streaming!
    )

    # Collect the full response from stream
    assistant_response = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            assistant_response += chunk.choices[0].delta.content

    # Remove emotion markers for TTS
    import re
    clean_response = re.sub(r'\[(HAPPY|EXCITED|THINKING|SURPRISED|CONCERNED)\]', '', assistant_response).strip()

    # Generate speech from the assistant's response
    speech_response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=clean_response
    )

    # Ensure static folder exists (important for PyInstaller bundles)
    os.makedirs(app.static_folder, exist_ok=True)

    # Save the audio file with a unique name
    audio_filename = f"response_{int(time.time())}.mp3"
    audio_path = os.path.join(app.static_folder, audio_filename)
    with open(audio_path, "wb") as f:
        f.write(speech_response.content)

    # Analyze response for UI enhancements
    response_analysis = {
        "has_safety_tip": any(word in assistant_response.lower() for word in ['caution', 'careful', 'warning', 'safety', 'danger']),
        "has_technique": any(word in assistant_response.lower() for word in ['technique', 'method', 'step-by-step', 'procedure']),
        "has_suggestion": any(word in assistant_response.lower() for word in ['try', 'suggest', 'recommend', 'might want to']),
    }

    return jsonify({
        "response": assistant_response,
        "audio_url": f"/static/{audio_filename}",
        "response_type": response_analysis,
        "should_demonstrate": "show" in message.lower() or "demonstrate" in message.lower()
    })

@app.route('/chat/stream', methods=['POST'])
@login_required
def chat_stream():
    """Stream chat responses in real-time for instant feedback!"""
    if not client:
        return jsonify({"error": "OpenAI client not initialized"}), 500

    data = request.json
    message = data.get('message', '')
    chat_history = data.get('history', [])  # Get chat history from frontend
    weather_data = data.get('weather')  # Get current weather data
    location_data = data.get('location')  # Get user location
    current_page = data.get('currentPage', 'unknown')  # Get current page

    if not message:
        return jsonify({"error": "No message provided"}), 400

    # Same context setup as regular chat
    user_context = f"User: {current_user.username}, Skill level: {getattr(current_user, 'cooking_skill_level', 'beginner')}, Current Page: {current_page}"
    inventory = ', '.join([item.name for item in current_user.inventory_items[:5]]) if current_user.inventory_items else "No items tracked"

    # Add weather context if available
    weather_context = ""
    if weather_data:
        weather_context = f"""
        Current Weather: {weather_data.get('temp', 'N/A')}°F, {weather_data.get('description', 'N/A')}
        Location: {weather_data.get('city', 'Unknown')}
        Humidity: {weather_data.get('humidity', 'N/A')}%
        Wind: {weather_data.get('wind', 'N/A')} mph
        """

    system_prompt = """
    You are a friendly and expressive Smart Fridge Assistant with internet connectivity! Keep responses CONCISE (under 80 words).

    CRITICAL: Add emotion markers to animate your avatar! Use these EXACT markers:
    [HAPPY] - Good news, enthusiasm, compliments
    [EXCITED] - Really great ideas, discoveries
    [THINKING] - Considering options, pondering
    [SURPRISED] - Unexpected info, interesting facts
    [CONCERNED] - Warnings, safety tips, caution

    Example: "[HAPPY] Great choice! [THINKING] For chicken, I'd suggest..."

    These markers animate your face but stay HIDDEN from the user!

    CAPABILITIES:
    - Weather Information: You can access current weather data for the user's location
    - Location Services: You know the user's general location
    - Internet Knowledge: You have up-to-date information and can help with current events
    - Store Locations: You can help users find nearby grocery stores and restaurants

    When users ask about weather, describe the current conditions naturally. For questions about
    nearby stores or locations, acknowledge you can help and provide general guidance.

    Keep responses SHORT for fast voice playback. Be helpful, warm and friendly.

    AVAILABLE ACTIONS:
    You can perform actions to help users! When you want to:
    - Navigate to a page: Say "[[NAVIGATE:page_name]]" (e.g., [[NAVIGATE:inventory]])
    - Highlight UI element: Say "[[HIGHLIGHT:element_id]]" (e.g., [[HIGHLIGHT:capture-btn]])
    - Add inventory item: Say "[[ADD_ITEM:item_name,quantity,unit]]" (e.g., [[ADD_ITEM:carrot,3,pcs]])
    - Remove inventory item: Say "[[REMOVE_ITEM:item_name]]"
    - Trigger feature: Say "[[ACTION:feature_name]]" (e.g., [[ACTION:capture]])

    Pages: dashboard, inventory, users, health-dashboard, recipes, waste-prevention, preferences
    Features: capture (take photo), detect (detect objects), door-cycle (simulate door open/close)

    Use these actions naturally in conversation! Example:
    "Let me add that for you! [[ADD_ITEM:carrot,2,pcs]] Done! I've added 2 carrots."
    "Check the Capture button! [[HIGHLIGHT:capture-btn]] [[NAVIGATE:dashboard]]"
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"Additional Context: {user_context}"},
        {"role": "system", "content": f"Current Inventory: {inventory}"},
    ]

    # Add weather context if available
    if weather_context:
        messages.append({"role": "system", "content": weather_context})

    # Add chat history to maintain context
    messages.extend(chat_history)

    # Add current message
    messages.append({"role": "user", "content": message})

    def generate():
        """Generator function for Server-Sent Events streaming"""
        full_response = ""

        try:
            # Stream from GPT
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=150,
                temperature=0.8,
                stream=True
            )

            # Stream chunks to frontend
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    # Send as Server-Sent Event
                    yield f"data: {content}\n\n"

            # Signal completion
            yield f"event: done\ndata: {full_response}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {str(e)}\n\n"

    return Response(generate(), mimetype='text/event-stream')

@app.route('/family/create', methods=['GET', 'POST'])
@login_required
def create_family():
    form = CreateFamilyForm()
    if form.validate_on_submit():
        try:
            family = family_manager.create_family(
                name=form.name.data,
                creator=current_user,
                shopping_day=form.shopping_day.data,
                budget=form.get_budget()  # Use the new method here
            )
            flash(f'Family "{family.name}" created successfully!', 'success')
            return redirect(url_for('family_dashboard', family_id=family.id))
        except Exception as e:
            flash(f'Error creating family: {str(e)}', 'error')
    return render_template('family/create_family.html', form=form)

@app.route('/family/<int:family_id>/dashboard')
@login_required
def family_dashboard(family_id):
    family = Family.query.get_or_404(family_id)
    member = FamilyMember.query.filter_by(
        family_id=family_id,
        user_id=current_user.id
    ).first_or_404()
    
    members = family_manager.get_family_members(family_id)
    return render_template('family/dashboard.html',
                         family=family,
                         members=members,
                         current_member=member)

@app.route('/family/<int:family_id>/invite', methods=['GET', 'POST'])
@login_required
def invite_family_member(family_id):
    member = FamilyMember.query.filter_by(
        family_id=family_id,
        user_id=current_user.id
    ).first_or_404()
    
    if not member.can_invite_members:
        flash('You do not have permission to invite members.', 'error')
        return redirect(url_for('family_dashboard', family_id=family_id))
    
    form = InviteFamilyMemberForm()
    if form.validate_on_submit():
        try:
            token = family_manager.invite_member(
                family_id=family_id,
                inviter_id=current_user.id,
                invitee_email=form.email.data,
                role=form.role.data
            )
            # Here you would typically send an email with the invitation link
            flash(f'Invitation sent to {form.email.data}', 'success')
            return redirect(url_for('family_dashboard', family_id=family_id))
        except Exception as e:
            flash(f'Error sending invitation: {str(e)}', 'error')
    
    return render_template('family/invite_member.html', form=form)

@app.route('/family/invitation/<token>', methods=['GET', 'POST'])
@login_required
def process_invitation(token):
    if request.method == 'POST':
        accept = request.form.get('accept', 'false') == 'true'
        success, message = family_manager.process_invitation(token, accept)
        flash(message, 'success' if success else 'error')
        if success and accept:
            invitation = FamilyInvitation.query.filter_by(token=token).first()
            return redirect(url_for('family_dashboard', family_id=invitation.family_id))
    else:
        invitation = FamilyInvitation.query.filter_by(token=token).first_or_404()
        return render_template('family/process_invitation.html', invitation=invitation)
    
    return redirect(url_for('index'))

@app.route('/family/<int:family_id>/settings', methods=['GET', 'POST'])
@login_required
def family_settings(family_id):
    member = FamilyMember.query.filter_by(
        family_id=family_id,
        user_id=current_user.id
    ).first_or_404()
    
    if member.role != 'admin':
        flash('Only family admins can modify settings.', 'error')
        return redirect(url_for('family_dashboard', family_id=family_id))
    
    family = Family.query.get_or_404(family_id)
    form = UpdateFamilySettingsForm(obj=family)
    
    if form.validate_on_submit():
        success, message = family_manager.update_family_settings(
            family_id,
            {
                'name': form.name.data,
                'shopping_day': form.shopping_day.data,
                'budget': form.budget.data
            }
        )
        flash(message, 'success' if success else 'error')
        return redirect(url_for('family_dashboard', family_id=family_id))
    
    return render_template('family/settings.html', form=form, family=family)

@app.route('/family/<int:family_id>/member/<int:user_id>/permissions', methods=['GET', 'POST'])
@login_required
def update_member_permissions(family_id, user_id):
    admin_member = FamilyMember.query.filter_by(
        family_id=family_id,
        user_id=current_user.id
    ).first_or_404()
    
    if admin_member.role != 'admin':
        flash('Only family admins can modify member permissions.', 'error')
        return redirect(url_for('family_dashboard', family_id=family_id))
    
    member = FamilyMember.query.filter_by(
        family_id=family_id,
        user_id=user_id
    ).first_or_404()
    
    form = UpdateMemberPermissionsForm(obj=member)
    
    if form.validate_on_submit():
        success, message = family_manager.update_member_permissions(
            family_id,
            user_id,
            {
                'role': form.role.data,
                'can_edit_inventory': form.can_edit_inventory.data,
                'can_edit_shopping_list': form.can_edit_shopping_list.data,
                'can_invite_members': form.can_invite_members.data
            }
        )
        flash(message, 'success' if success else 'error')
        return redirect(url_for('family_dashboard', family_id=family_id))
    
    return render_template('family/member_permissions.html', form=form, member=member)

@app.route('/voice_query', methods=['POST'])
@login_required
def voice_query():
    if not client:
        return jsonify({
            "response": "Voice assistant is disabled. Add OPENAI_API_KEY to .env file to enable this feature."
        }), 503

    query = request.json.get('query')
    inventory = inventory_manager.get_inventory(current_user.id)

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for a smart fridge. The user will ask about nutritional information for items in their fridge."},
                {"role": "user", "content": f"Given this inventory: {inventory}, answer this query: {query}"}
            ]
        )

        answer = response.choices[0].message.content
        generate_and_play_speech(answer)

        return jsonify({"response": answer})
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"}), 500


# ==============================================================================
# LIVE CAMERA FEED ROUTES
# ==============================================================================

@app.route('/camera-feed')
@login_required
def camera_feed_page():
    """Render the live camera feed page."""
    return render_template('camera_feed.html')


def generate_camera_stream(camera_index):
    """Generator function for MJPEG streaming."""
    import cv2

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"Error: Could not open camera {camera_index}")
        return

    try:
        while True:
            success, frame = cap.read()
            if not success:
                break

            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue

            frame_bytes = buffer.tobytes()

            # Yield frame in MJPEG format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        cap.release()


@app.route('/video_feed/<int:camera_id>')
@login_required
def video_feed(camera_id):
    """Stream MJPEG video from specified camera."""
    from flask import Response
    return Response(
        generate_camera_stream(camera_id),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/capture_frame', methods=['POST'])
@login_required
def capture_frame():
    """Capture a single frame from specified camera."""
    data = request.json
    camera_id = data.get('camera_id', 0)

    try:
        import cv2
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            return jsonify({"success": False, "error": f"Could not open camera {camera_id}"})

        success, frame = cap.read()
        cap.release()

        if success:
            # Save frame
            img_path = os.path.join(static_folder, f'captured_camera_{camera_id}.jpg')
            cv2.imwrite(img_path, frame)
            return jsonify({
                "success": True,
                "image_path": f"/static/captured_camera_{camera_id}.jpg?t={int(time.time())}"
            })
        else:
            return jsonify({"success": False, "error": "Failed to capture frame"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/detect_from_camera', methods=['POST'])
@login_required
def detect_from_camera():
    """Detect objects from specified camera and update inventory."""
    data = request.json
    camera_id = data.get('camera_id', 0)

    try:
        import cv2

        # Capture frame
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            return jsonify({"success": False, "error": f"Could not open camera {camera_id}"})

        success, frame = cap.read()
        cap.release()

        if not success:
            return jsonify({"success": False, "error": "Failed to capture frame"})

        # Detect objects
        detector = ObjectDetector()
        detections = detector.detect_objects(frame)

        # Save annotated image
        annotated_frame = frame.copy()
        for detection in detections:
            box = detection['box']
            x, y, w, h = box['x'], box['y'], box['width'], box['height']
            cv2.rectangle(annotated_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            label = f"{detection['class']}: {detection['confidence']:.2f}"
            cv2.putText(annotated_frame, label, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        img_path = os.path.join(static_folder, f'detected_camera_{camera_id}.jpg')
        cv2.imwrite(img_path, annotated_frame)

        return jsonify({
            "success": True,
            "objects": detections,
            "image_path": f"/static/detected_camera_{camera_id}.jpg?t={int(time.time())}"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/inventory')
@login_required
def get_inventory():
    inventory = inventory_manager.get_inventory(current_user.id)
    return jsonify(inventory)

@app.route('/clear_inventory', methods=['POST'])
@login_required
def clear_inventory():
    inventory_manager.clear_inventory(current_user.id)
    return jsonify({"message": "Inventory cleared successfully"})

@app.route('/inventory_data')
@login_required
def get_inventory_data():
    inventory = inventory_manager.get_inventory(current_user.id)  # Pass the current user's id here
    categorized_inventory = {}
    for item, details in inventory.items():
        category = details['category']
        if category not in ['non_food', 'other']:  # Filter out non-food and other categories
            if category not in categorized_inventory:
                categorized_inventory[category] = {'items': [], 'quantities': []}
            categorized_inventory[category]['items'].append(item)
            categorized_inventory[category]['quantities'].append(details['quantity'])
    return jsonify(inventory_manager.get_inventory_by_category(current_user.id))

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/nutrition_summary')
@login_required
def nutrition_summary():
    inventory = inventory_manager.get_inventory(current_user.id)
    total_nutrition = inventory_manager.get_total_nutrition(current_user.id)
    
    return render_template('nutrition_summary.html', 
                           nutrition=total_nutrition, 
                           inventory=inventory)

@app.route('/expiring-soon')
@login_required
def get_expiring_soon():
    days = request.args.get('days', default=3, type=int)
    expiring_items = inventory_manager.get_expiring_soon(current_user.id, days)
    return jsonify(expiring_items)

@app.route('/inventory_trends')
@login_required
def inventory_trends():
    # Simulate data for the last 7 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    dates = [start_date + timedelta(days=i) for i in range(8)]
    
    # Get inventory data for each day
    trends = {}
    for date in dates:
        inventory = inventory_manager.get_inventory(current_user.id, date)
        for item, details in inventory.items():
            if item not in trends:
                trends[item] = []
            trends[item].append({'date': date.strftime('%Y-%m-%d'), 'quantity': details['quantity']})
    
    return jsonify(trends)

@app.route('/waste-prevention')
@login_required
def waste_prevention_dashboard():
    return render_template('waste_prevention.html', username=current_user.username)

@app.route('/api/waste-analysis')
@login_required
def get_waste_analysis():
    waste_manager = module_manager.get_module('food_waste')
    analysis = waste_manager.analyze_waste_risk(current_user.id)
    suggestions = waste_manager.get_waste_prevention_suggestions(current_user.id)
    return jsonify({
        'analysis': analysis,
        'suggestions': suggestions
    })


@app.route('/advanced-recipe-search')
@login_required
def advanced_recipe_search():
    return render_template('advanced_recipe_search.html')

@app.route('/api/search-recipes', methods=['POST'])
@login_required
def search_recipes():
    data = request.json
    print(f"Received search data: {data}")  # Debug print
    
    recipe_manager = module_manager.get_module('recipe_manager')
    
    try:
        recipes = recipe_manager.search_recipes(
            ingredients=data.get('ingredients'),
            dietary_restrictions=data.get('dietary_restrictions'),
            max_cooking_time=data.get('max_cooking_time'),
            nutrition_requirements=data.get('nutrition_requirements'),
            difficulty_level=data.get('difficulty_level')
        )
        print(f"Found recipes: {recipes}")  # Debug print
        
        if current_user.calorie_goal or current_user.protein_goal:
            recipes = recipe_manager.filter_by_health_goals(
                recipes,
                calorie_target=current_user.calorie_goal,
                protein_target=current_user.protein_goal,
                carb_target=current_user.carb_goal,
                fat_target=current_user.fat_goal
            )
            print(f"After health goal filtering: {recipes}")  # Debug print
        
        return jsonify(recipes)
    except Exception as e:
        print(f"Error in recipe search: {str(e)}")  # Debug print
        return jsonify({"error": str(e)}), 500

@app.route('/api/inventory/add', methods=['POST'])
@login_required
def add_inventory_item_api():
    """Add an item to inventory via assistant"""
    data = request.json
    item_name = data.get('name')
    quantity = data.get('quantity', 1)
    unit = data.get('unit', 'pcs')

    if not item_name:
        return jsonify({"error": "Item name required"}), 400

    try:
        # Add to inventory with default values
        from datetime import datetime, timedelta

        # Check if item already exists
        existing_item = InventoryItem.query.filter_by(
            user_id=current_user.id,
            name=item_name
        ).first()

        if existing_item:
            # Update quantity
            existing_item.quantity = float(quantity)
            existing_item.unit = unit
            db.session.commit()
            return jsonify({
                "success": True,
                "message": f"Updated {item_name} quantity to {quantity} {unit}",
                "item": item_name
            })
        else:
            # Create new item
            expiry_date = datetime.now() + timedelta(days=7)  # Default 7 days
            new_item = InventoryItem(
                user_id=current_user.id,
                name=item_name,
                quantity=float(quantity),
                unit=unit,
                category='other',
                expiry_date=expiry_date
            )
            db.session.add(new_item)
            db.session.commit()

            return jsonify({
                "success": True,
                "message": f"Added {quantity} {unit} of {item_name} to inventory",
                "item": item_name
            })
    except Exception as e:
        print(f"Error adding inventory item: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/inventory/remove', methods=['POST'])
@login_required
def remove_inventory_item_api():
    """Remove an item from inventory via assistant"""
    data = request.json
    item_name = data.get('name')

    if not item_name:
        return jsonify({"error": "Item name required"}), 400

    try:
        # Find and remove item
        item = InventoryItem.query.filter_by(
            user_id=current_user.id,
            name=item_name
        ).first()

        if item:
            db.session.delete(item)
            db.session.commit()
            return jsonify({
                "success": True,
                "message": f"Removed {item_name} from inventory",
                "item": item_name
            })
        else:
            return jsonify({
                "success": False,
                "message": f"{item_name} not found in inventory",
                "item": item_name
            }), 404
    except Exception as e:
        print(f"Error removing inventory item: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/search', methods=['POST'])
@login_required
def web_search():
    """Perform a web search for general queries"""
    data = request.json
    query = data.get('query')

    if not query:
        return jsonify({"error": "Query required"}), 400

    try:
        # Use DuckDuckGo Instant Answer API (no key required)
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        search_data = response.json()

        # Extract relevant information
        result = {
            "abstract": search_data.get('AbstractText', ''),
            "source": search_data.get('AbstractSource', ''),
            "url": search_data.get('AbstractURL', ''),
            "heading": search_data.get('Heading', ''),
            "related": [topic.get('Text', '') for topic in search_data.get('RelatedTopics', [])[:3] if 'Text' in topic]
        }

        return jsonify(result)
    except Exception as e:
        print(f"Web search error: {str(e)}")
        return jsonify({"error": "Search failed", "abstract": ""}), 500

@app.route('/api/weather', methods=['POST'])
@login_required
def get_weather():
    """Get weather data based on user's location"""
    data = request.json
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if not latitude or not longitude:
        return jsonify({"error": "Location data required"}), 400

    # Get OpenWeatherMap API key from environment
    weather_api_key = os.getenv('OPENWEATHER_API_KEY')

    if not weather_api_key:
        # Return default/mock data if no API key
        return jsonify({
            "temp": 72,
            "feels_like": 70,
            "humidity": 65,
            "wind": 5,
            "weather": "Clear",
            "description": "clear sky",
            "city": "Your Location",
            "icon": "01d"
        })

    try:
        # Call OpenWeatherMap API
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={weather_api_key}&units=imperial"
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        weather_data = response.json()

        return jsonify({
            "temp": weather_data['main']['temp'],
            "feels_like": weather_data['main']['feels_like'],
            "humidity": weather_data['main']['humidity'],
            "wind": weather_data['wind']['speed'],
            "weather": weather_data['weather'][0]['main'],
            "description": weather_data['weather'][0]['description'],
            "city": weather_data.get('name', 'Your Location'),
            "icon": weather_data['weather'][0]['icon']
        })
    except Exception as e:
        print(f"Weather API error: {str(e)}")
        # Return default data on error
        return jsonify({
            "temp": 72,
            "feels_like": 70,
            "humidity": 65,
            "wind": 5,
            "weather": "Clear",
            "description": "clear sky",
            "city": "Your Location",
            "icon": "01d"
        })

@app.route('/update-expiry', methods=['POST'])
@login_required
def update_expiry():
    data = request.json
    item_name = data.get('item_name')
    new_expiry = data.get('new_expiry')
    if item_name and new_expiry:
        inventory_manager.update_expiry_date(current_user.id, item_name, new_expiry)
        return jsonify({"message": f"Expiry date for {item_name} updated"})
    return jsonify({"error": "Invalid data"}), 400

@app.route('/generate_shopping_list')
@login_required
def generate_shopping_list():
    meal_plan = get_meal_plan()
    print(f"Generating shopping list for meal plan: {meal_plan}")  # Debug print
    inventory = inventory_manager.get_inventory(current_user.id)
    print(f"Current inventory: {inventory}")  # Debug print
    
    shopping_list = {}
    for day, meals in meal_plan.items():
        for meal, recipe_id in meals.items():
            if recipe_id:
                recipe = get_recipe_details(recipe_id)
                print(f"Recipe details for {recipe_id}: {recipe}")  # Debug print
                if recipe and isinstance(recipe, dict) and 'extendedIngredients' in recipe:
                    for ingredient in recipe['extendedIngredients']:
                        name = ingredient['name']
                        amount = ingredient.get('amount', 0)
                        unit = ingredient.get('unit', '')
                        if name not in inventory or inventory[name]['quantity'] < amount:
                            if name not in shopping_list:
                                shopping_list[name] = {'amount': 0, 'unit': unit}
                            shopping_list[name]['amount'] += amount
                else:
                    print(f"Couldn't get details for recipe {recipe_id}")
    
    print(f"Generated shopping list: {shopping_list}")  # Debug print
    if not shopping_list:
        return jsonify({"message": "No items needed for the current meal plan."})
    return jsonify(shopping_list)

@app.route('/save_meal_plan', methods=['POST'])
@login_required
def save_meal_plan():
    meal_plan = request.json
    session['current_meal_plan'] = meal_plan
    print(f"Saving meal plan for user {current_user.id}: {meal_plan}")
    return jsonify({"message": "Meal plan saved successfully"})

@app.route('/get_meal_plan')
@login_required
def get_meal_plan():
    return session.get('current_meal_plan', {
        "Monday": {"breakfast": None, "lunch": None, "dinner": None},
        "Tuesday": {"breakfast": None, "lunch": None, "dinner": None},
        "Wednesday": {"breakfast": None, "lunch": None, "dinner": None},
        "Thursday": {"breakfast": None, "lunch": None, "dinner": None},
        "Friday": {"breakfast": None, "lunch": None, "dinner": None},
        "Saturday": {"breakfast": None, "lunch": None, "dinner": None},
        "Sunday": {"breakfast": None, "lunch": None, "dinner": None}
    })

@app.route('/toggle_teaching_mode', methods=['POST'])
@login_required
def toggle_teaching_mode():
    data = request.json
    enabled = data.get('enabled', False)
    
    # Store the teaching mode state in the session
    session['teaching_mode'] = enabled
    
    return jsonify({
        "success": True,
        "teaching_mode": enabled
    })

@app.route('/suggest_recipes')
@login_required
def suggest_recipes():
    inventory = inventory_manager.get_inventory(current_user.id)
    available_ingredients = list(inventory.keys())
    
    if not available_ingredients:
        return jsonify({"message": "No ingredients in inventory. Please add some items to your inventory first."}), 404
    
    recipes = find_recipes_by_ingredients(available_ingredients, current_user.dietary_preference)
    
    if recipes:
        # Simplify the recipe data to include only essential information
        simplified_recipes = [
            {
                "id": recipe.get("id"),
                "title": recipe.get("title"),
                "image": recipe.get("image"),
                "usedIngredientCount": recipe.get("usedIngredientCount"),
                "missedIngredientCount": recipe.get("missedIngredientCount")
            }
            for recipe in recipes
        ]
        return jsonify(simplified_recipes)
    else:
        return jsonify({"message": "No recipes found. Try adding more ingredients or try again later."}), 404

@app.route('/recipe_details/<int:recipe_id>')
@login_required
def get_recipe_details(recipe_id):
    try:
        recipe_manager = module_manager.get_module('recipe_manager')
        details = recipe_manager.get_recipe_details(recipe_id)
        
        if 'error' in details:
            return jsonify(details), 400
            
        simplified_details = {
            'title': details.get('title', 'Unknown Recipe'),
            'image': details.get('image', ''),
            'readyInMinutes': details.get('readyInMinutes', 'undefined'),
            'servings': details.get('servings', 'Not specified'),
            'instructions': [],
            'ingredients': [],
            'nutrition': details.get('nutrition', {})
        }
        
        # Extract instructions
        if 'analyzedInstructions' in details and details['analyzedInstructions']:
            simplified_details['instructions'] = [
                step['step'] for step in details['analyzedInstructions'][0].get('steps', [])
            ]
            
        # Extract ingredients
        if 'extendedIngredients' in details:
            simplified_details['ingredients'] = [
                ingredient.get('original', '') for ingredient in details['extendedIngredients']
            ]
            
        return jsonify(simplified_details)
        
    except Exception as e:
        print(f"Error processing recipe details: {e}")
        return jsonify({
            'error': 'Failed to load recipe details',
            'message': str(e)
        }), 500


@app.route('/users')
@login_required
def user_management():
    """User management page."""
    return render_template('user_management.html')


if __name__ == '__main__':
    if not os.path.exists(app.static_folder):
        os.makedirs(app.static_folder)
    app.run(host='0.0.0.0', port=8080, debug=True)