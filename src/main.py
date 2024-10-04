import sys
import os
import urllib.request
import cv2
from core.module_manager import ModuleManager
from camera.camera_manager import CameraManager
from ai.object_detection import ObjectDetector
from inventory.inventory_manager import InventoryManager
from recipes import find_matching_recipes
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, User, InventoryItem
from recipes.recipe_api import find_recipes_by_ingredients, get_recipe_details
from dotenv import load_dotenv
from openai import OpenAI
import io
from pydub import AudioSegment
from pydub.playback import play
import requests
import time
from forms import UserPreferencesForm

# Ensure the src folder is added to Python's module search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
NUTRITIONIX_APP_ID = os.getenv('NUTRITIONIX_APP_ID')
NUTRITIONIX_API_KEY = os.getenv('NUTRITIONIX_API_KEY')

load_dotenv()  # This loads the variables from .env

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_folder = os.path.join(base_dir, 'static')

# Define the path to your database file
db_path = os.path.join(base_dir, 'smartfridge.db')

if os.path.exists(db_path):
    os.remove(db_path)
    print("Existing database deleted.")

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
    # You can add more cameras here in the future
    return camera_manager

def generate_and_play_speech(text):
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
    
    audio_data = io.BytesIO(response.content)
    audio = AudioSegment.from_file(audio_data, format="mp3")
    play(audio)

def estimate_portion_size(object_size):
    if object_size < 1000:  # small objects
        return "small"
    elif object_size < 5000:  # medium objects
        return "medium"
    else:  # large objects
        return "large"

def get_nutritional_info(food_item, portion_size):
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

# Initialize modules
module_manager = ModuleManager()
camera_manager = setup_cameras()  # Use the new setup_cameras function
inventory_manager = InventoryManager()

# Setup object detection
print(f"Current working directory: {os.getcwd()}")
weights_path, config_path, classes_path = setup_object_detection()
print(f"Weights path: {weights_path}")
print(f"Config path: {config_path}")
print(f"Classes path: {classes_path}")
object_detector = ObjectDetector(weights_path, config_path, classes_path)

# Register modules
module_manager.register_module('camera', camera_manager)
module_manager.register_module('object_detector', object_detector)
module_manager.register_module('inventory', inventory_manager)

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
    message = request.json.get('message')
    chat_history = request.json.get('history', [])
    inventory = inventory_manager.get_inventory(current_user.id)
    
    # Prepare the messages for the GPT model
    messages = [
        {"role": "system", "content": "You are a helpful kitchen assistant for a smart fridge. You can provide recipe suggestions, nutritional information, and general cooking advice based on the user's inventory."},
        {"role": "system", "content": f"The current inventory is: {inventory}"},
    ] + chat_history + [{"role": "user", "content": message}]
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    
    assistant_response = response.choices[0].message.content
    
    # Generate speech from the assistant's response
    speech_response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=assistant_response
    )
    
    # Save the audio file with a unique name
    audio_filename = f"response_{int(time.time())}.mp3"
    audio_path = os.path.join(app.static_folder, audio_filename)
    with open(audio_path, "wb") as f:
        f.write(speech_response.content)
    
    return jsonify({
        "response": assistant_response,
        "audio_url": f"/static/{audio_filename}"
    })
        
@app.route('/voice_query', methods=['POST'])
@login_required
def voice_query():
    query = request.json.get('query')
    inventory = inventory_manager.get_inventory(current_user.id)
    
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

@app.route('/suggest_recipes')
@login_required
def suggest_recipes():
    # Use the inventory_manager to get the inventory instead of querying the database directly
    inventory = inventory_manager.get_inventory(current_user.id)
    available_ingredients = list(inventory.keys())
    print(f"Available ingredients: {available_ingredients}")  # Debug print
    
    if not available_ingredients:
        print("No ingredients in inventory")
        return jsonify({"message": "No ingredients in inventory. Please add some items to your inventory first."}), 404
    
    recipes = find_recipes_by_ingredients(available_ingredients)
    print(f"API response: {recipes}")  # Debug print
    
    if recipes:
        return jsonify(recipes)
    else:
        print("No recipes found or an error occurred")  # Debug print
        return jsonify({"message": "No recipes found. Try adding more ingredients or try again later."}), 404

if __name__ == '__main__':
    if not os.path.exists(app.static_folder):
        os.makedirs(app.static_folder)
    app.run(host='0.0.0.0', port=8080, debug=True)