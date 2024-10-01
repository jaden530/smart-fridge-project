# src/gui.py

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLabel
from PyQt6.QtCore import QTimer

class SmartFridgeGUI(QMainWindow):
    def __init__(self, module_manager):
        super().__init__()
        self.module_manager = module_manager
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Smart Fridge')
        self.setGeometry(100, 100, 600, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout()
        central_widget.setLayout(layout)

        # Inventory list
        inventory_layout = QVBoxLayout()
        self.inventory_list = QListWidget()
        inventory_layout.addWidget(QLabel('Inventory:'))
        inventory_layout.addWidget(self.inventory_list)

        # Controls
        controls_layout = QVBoxLayout()
        self.capture_button = QPushButton('Capture Image')
        self.capture_button.clicked.connect(self.capture_image)
        controls_layout.addWidget(self.capture_button)

        self.detect_button = QPushButton('Detect Objects')
        self.detect_button.clicked.connect(self.detect_objects)
        controls_layout.addWidget(self.detect_button)

        layout.addLayout(inventory_layout)
        layout.addLayout(controls_layout)

        # Timer to update inventory
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_inventory_display)
        self.timer.start(5000)  # Update every 5 seconds

    def update_inventory_display(self):
        inventory_manager = self.module_manager.get_module('inventory')
        inventory = inventory_manager.get_inventory()
        self.inventory_list.clear()
        for item, details in inventory.items():
            self.inventory_list.addItem(f"{item}: {details['quantity']}")

    def capture_image(self):
        camera_manager = self.module_manager.get_module('camera')
        camera_manager.capture_image('main')  # Assuming 'main' is the camera ID

    def detect_objects(self):
        camera_manager = self.module_manager.get_module('camera')
        object_detector = self.module_manager.get_module('object_detector')
        inventory_manager = self.module_manager.get_module('inventory')

        image = camera_manager.get_last_image('main')  # Assuming 'main' is the camera ID
        if image is not None:
            detected_objects = object_detector.detect(image)
            inventory_manager.update_from_detection(detected_objects)
            self.update_inventory_display()