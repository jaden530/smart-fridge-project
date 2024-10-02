import os
import urllib.request
import cv2
from flask import Flask, render_template, jsonify, request, send_from_directory
from core.module_manager import ModuleManager
from camera.camera_manager import CameraManager
from ai.object_detection import ObjectDetector
from inventory.inventory_manager import InventoryManager

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_folder = os.path.join(base_dir, 'static')

app = Flask(__name__, static_folder=static_folder, static_url_path='/static')

@app.route('/')
def home():
    return render_template('index.html')

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
def detect_objects():
    image = camera_manager.get_last_image('main')
    if image is not None:
        detected_objects = object_detector.detect(image)
        inventory_manager.update_from_detection(detected_objects)
        
        # Draw bounding boxes on the image
        for obj in detected_objects:
            x, y, w, h = obj['box'].values()
            cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
            label = f"{obj['class']} {obj['confidence']:.2f}"
            cv2.putText(image, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
        
        img_path = os.path.join(app.static_folder, 'detected_image.jpg')
        cv2.imwrite(img_path, image)
        
        # Get the updated inventory
        updated_inventory = inventory_manager.get_inventory()
        
        return jsonify({
            "message": "Objects detected and inventory updated",
            "objects": detected_objects,
            "image_path": '/static/detected_image.jpg',
            "inventory": updated_inventory
        })
    else:
        return jsonify({"error": "No image available for detection"})

@app.route('/inventory')
def get_inventory():
    inventory = inventory_manager.get_inventory()
    return jsonify(inventory)

@app.route('/clear_inventory', methods=['POST'])
def clear_inventory():
    inventory_manager.clear_inventory()
    return jsonify({"message": "Inventory cleared successfully"})

@app.route('/inventory_data')
def get_inventory_data():
    return jsonify(inventory_manager.get_inventory_by_category())

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/expiring-soon')
def get_expiring_soon():
    days = request.args.get('days', default=3, type=int)
    expiring_items = inventory_manager.get_expiring_soon(days)
    return jsonify(expiring_items)

@app.route('/update-expiry', methods=['POST'])
def update_expiry():
    data = request.json
    item_name = data.get('item_name')
    new_expiry = data.get('new_expiry')
    if item_name and new_expiry:
        inventory_manager.update_expiry_date(item_name, new_expiry)
        return jsonify({"message": f"Expiry date for {item_name} updated"})
    return jsonify({"error": "Invalid data"}), 400

if __name__ == '__main__':
    if not os.path.exists(app.static_folder):
        os.makedirs(app.static_folder)
    app.run(host='0.0.0.0', port=8080, debug=True)