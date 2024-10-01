import os
import urllib.request
from flask import Flask, render_template, jsonify, request
from core.module_manager import ModuleManager
from camera.camera_manager import CameraManager
from ai.object_detection import ObjectDetector
from inventory.inventory_manager import InventoryManager

app = Flask(__name__)

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

# Initialize modules
module_manager = ModuleManager()
camera_manager = CameraManager()
inventory_manager = InventoryManager()

# Setup object detection
print(f"Current working directory: {os.getcwd()}")
weights_path, config_path, classes_path = setup_object_detection()  # Call the function here
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
        img_path = os.path.join('static', 'captured_image.jpg')
        cv2.imwrite(img_path, image)
        return jsonify({"message": "Image captured successfully", "image_path": '/' + img_path})
    else:
        return jsonify({"error": "Failed to capture image"})

@app.route('/detect', methods=['POST'])
@app.route('/detect', methods=['POST'])
def detect_objects():
    image = camera_manager.get_last_image('main')
    if image is not None:
        detected_objects = object_detector.detect(image)
        inventory_manager.update_from_detection(detected_objects)
        
        # Draw bounding boxes on the image
        for obj in detected_objects:
            x, y, w, h = obj['box']
            cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(image, f"{obj['class']} {obj['confidence']:.2f}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
        
        img_path = os.path.join('static', 'detected_image.jpg')
        cv2.imwrite(img_path, image)
        
        # Get the updated inventory
        updated_inventory = inventory_manager.get_inventory()
        
        return jsonify({
            "message": "Objects detected and inventory updated",
            "objects": detected_objects,
            "image_path": '/' + img_path,
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

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)  # Ensure static directory exists
    camera_manager.add_camera('main', 'https://raw.githubusercontent.com/pjreddie/darknet/master/data/dog.jpg')
    camera_manager.start()
    app.run(host='0.0.0.0', port=8080, debug=True)