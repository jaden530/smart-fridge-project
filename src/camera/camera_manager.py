import cv2
import numpy as np
import requests
from io import BytesIO

class CameraManager:
    def __init__(self):
        self.cameras = {}
        self.is_running = False
        self.last_image = None

    def add_camera(self, camera_id, source):
        self.cameras[camera_id] = source

    def remove_camera(self, camera_id):
        if camera_id in self.cameras:
            del self.cameras[camera_id]

    def start(self):
        self.is_running = True

    def stop(self):
        self.is_running = False

    def capture_image(self, camera_id):
        source = self.cameras.get(camera_id)
        if source.startswith('http'):
            # If source is a URL, download the image
            response = requests.get(source)
            img_array = np.array(bytearray(response.content), dtype=np.uint8)
            self.last_image = cv2.imdecode(img_array, -1)
        else:
            # If source is a local file path, read the image
            self.last_image = cv2.imread(source)
        return self.last_image

    def get_last_image(self, camera_id):
        return self.last_image