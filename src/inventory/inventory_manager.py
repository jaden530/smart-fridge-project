# src/inventory/inventory_manager.py

import json
from datetime import datetime, timedelta

class InventoryManager:
    def __init__(self, inventory_file='inventory.json'):
        self.inventory_file = inventory_file
        self.inventory = self.load_inventory()
        self.categories = {
            'vehicle': ['truck', 'car', 'bicycle'],
            'animal': ['dog', 'cat', 'bird'],
            'furniture': ['chair', 'table', 'sofa'],
            'electronics': ['tv', 'laptop', 'phone'],
            'other': []
        }
        self.expiration_database = {
            'milk': 7,  # days
            'bread': 5,
            'eggs': 21,
            'cheese': 14,
            'apple': 14,
            'banana': 5,
            # Add more items as needed
        }

    def load_inventory(self):
        try:
            with open(self.inventory_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_inventory(self):
        with open(self.inventory_file, 'w') as f:
            json.dump(self.inventory, f, indent=2)

    def get_category(self, item):
        for category, items in self.categories.items():
            if item in items:
                return category
        return 'other'

    def get_default_expiry(self, item_name):
        days = self.expiration_database.get(item_name.lower(), 7)  # Default to 7 days if not found
        return (datetime.now() + timedelta(days=days)).isoformat()

    def add_item(self, item_name, quantity=1, expiry_date=None):
        if item_name not in self.inventory:
            self.inventory[item_name] = {
                'quantity': quantity,
                'expiry_date': expiry_date or self.get_default_expiry(item_name),
                'added_date': datetime.now().isoformat(),
                'last_detected': datetime.now().isoformat(),
                'category': self.get_category(item_name)
            }
        else:
            self.inventory[item_name]['quantity'] += quantity
            self.inventory[item_name]['last_detected'] = datetime.now().isoformat()
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

        # Items to be added or updated
        for item in detected_items:
            if item['class'] not in current_items:
                self.add_item(item['class'])
            else:
                self.inventory[item['class']]['quantity'] += 1
                self.inventory[item['class']]['last_detected'] = datetime.now().isoformat()

        # Items to be removed (no longer detected)
        for item in current_items - detected_item_names:
            self.remove_item(item)

        self.save_inventory()

    def get_inventory_by_category(self):
        categorized_inventory = {}
        for item, details in self.inventory.items():
            category = details['category']
            if category not in categorized_inventory:
                categorized_inventory[category] = {'items': [], 'quantities': []}
            categorized_inventory[category]['items'].append(item)
            categorized_inventory[category]['quantities'].append(details['quantity'])
        return categorized_inventory

    def get_expiring_soon(self, days=3):
        now = datetime.now()
        expiring_soon = []
        for item, details in self.inventory.items():
            expiry_date = datetime.fromisoformat(details['expiry_date'])
            if (expiry_date - now).days <= days:
                expiring_soon.append((item, details))
        return expiring_soon

    def update_expiry_date(self, item_name, new_expiry_date):
        if item_name in self.inventory:
            self.inventory[item_name]['expiry_date'] = new_expiry_date
            self.save_inventory()