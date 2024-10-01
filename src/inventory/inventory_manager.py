# src/inventory/inventory_manager.py

import json
from datetime import datetime

class InventoryManager:
    def __init__(self, inventory_file='inventory.json'):
        self.inventory_file = inventory_file
        self.inventory = self.load_inventory()

    def load_inventory(self):
        try:
            with open(self.inventory_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_inventory(self):
        with open(self.inventory_file, 'w') as f:
            json.dump(self.inventory, f, indent=2)

    def add_item(self, item_name, quantity=1, expiry_date=None):
        if item_name not in self.inventory:
            self.inventory[item_name] = {
                'quantity': quantity,
                'expiry_date': expiry_date,
                'added_date': datetime.now().isoformat()
            }
        else:
            self.inventory[item_name]['quantity'] += quantity
        self.save_inventory()

    def remove_item(self, item_name, quantity=1):
        if item_name in self.inventory:
            self.inventory[item_name]['quantity'] -= quantity
            if self.inventory[item_name]['quantity'] <= 0:
                del self.inventory[item_name]
            self.save_inventory()

    def get_inventory(self):
        return self.inventory
        
    def clear_inventory(self):
        self.inventory = {}
        self.save_inventory()    
        
    def update_from_detection(self, detected_items):
        current_items = set(self.inventory.keys())
        detected_item_names = set(item['class'] for item in detected_items)

        # Items to be added (new detections)
        for item in detected_items:
            if item['class'] not in current_items:
                self.add_item(item['class'])

        # Items to be removed (no longer detected)
        for item in current_items - detected_item_names:
            self.remove_item(item)

        self.save_inventory()