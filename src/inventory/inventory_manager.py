# src/inventory/inventory_manager.py

import json
from datetime import datetime, timedelta

class InventoryManager:
    def __init__(self, inventory_file='inventory.json'):
        self.inventory_file = inventory_file
        self.inventories = self.load_inventory()
        self.categories = {
            'fruits': ['apple', 'banana', 'orange', 'grape', 'strawberry', 'blueberry'],
            'vegetables': ['carrot', 'tomato', 'cucumber', 'lettuce', 'broccoli', 'pepper'],
            'dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream'],
            'grains': ['bread', 'rice', 'pasta', 'cereal', 'oats'],
            'protein': ['chicken', 'beef', 'fish', 'eggs', 'tofu', 'beans'],
            'beverages': ['water', 'juice', 'soda', 'coffee', 'tea'],
            'non_food': ['bowl', 'plate', 'utensil', 'container'],
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
            json.dump(self.inventories, f, indent=2)

    def get_category(self, item):
        item_lower = item.lower()
        for category, items in self.categories.items():
            if item_lower in items:
                return category
        return 'other'

    def get_default_expiry(self, item_name):
        days = self.expiration_database.get(item_name.lower(), 7)  # Default to 7 days if not found
        return (datetime.now() + timedelta(days=days)).isoformat()

    def add_item(self, user_id, item_name, quantity=1, expiry_date=None):
        user_id = str(user_id)
        if user_id not in self.inventories:
            self.inventories[user_id] = {}
        if item_name not in self.inventories[user_id]:
            self.inventories[user_id][item_name] = {
                'quantity': quantity,
                'expiry_date': expiry_date or self.get_default_expiry(item_name),
                'added_date': datetime.now().isoformat(),
                'last_detected': datetime.now().isoformat(),
                'category': self.get_category(item_name)
            }
        else:
            self.inventories[user_id][item_name]['quantity'] += quantity
            self.inventories[user_id][item_name]['last_detected'] = datetime.now().isoformat()
        self.save_inventory()

    def remove_item(self, user_id, item_name, quantity=1):
        user_id = str(user_id)
        if user_id in self.inventories and item_name in self.inventories[user_id]:
            self.inventories[user_id][item_name]['quantity'] -= quantity
            if self.inventories[user_id][item_name]['quantity'] <= 0:
                del self.inventories[user_id][item_name]
            self.save_inventory()

    def get_inventory(self, user_id):
        inventory = self.inventories.get(str(user_id), {})
        print(f"Debug: Inventory for user {user_id}: {inventory}")  # Add this debug print
        return inventory

    def clear_inventory(self, user_id):
        user_id = str(user_id)
        if user_id in self.inventories:
            self.inventories[user_id] = {}
            self.save_inventory()

    def update_from_detection(self, user_id, detected_items):
        user_id = str(user_id)
        if user_id not in self.inventories:
            self.inventories[user_id] = {}
        current_items = set(self.inventories[user_id].keys())
        detected_item_names = set(item['class'] for item in detected_items)

        # Items to be added or updated
        for item in detected_items:
            if item['class'] not in current_items:
                 self.add_item(user_id, item['class'])
            else:
                self.inventories[user_id][item['class']]['quantity'] += 1
                self.inventories[user_id][item['class']]['last_detected'] = datetime.now().isoformat()

        # Items to be removed (no longer detected)
        for item in current_items - detected_item_names:
            self.remove_item(user_id, item)

        self.save_inventory()

    def get_inventory_by_category(self, user_id):
        user_inventory = self.get_inventory(user_id)
        categorized_inventory = {}
        for item, details in user_inventory.items():
            category = details['category']
            if category not in categorized_inventory:
                categorized_inventory[category] = {'items': [], 'quantities': []}
            categorized_inventory[category]['items'].append(item)
            categorized_inventory[category]['quantities'].append(details['quantity'])
        return categorized_inventory

    def get_expiring_soon(self, user_id, days=3):
        user_inventory = self.get_inventory(user_id)
        now = datetime.now()
        expiring_soon = []
        for item, details in user_inventory.items():
            expiry_date = datetime.fromisoformat(details['expiry_date'])
            if (expiry_date - now).days <= days:
                expiring_soon.append((item, details))
        return expiring_soon

    def update_expiry_date(self, user_id, item_name, new_expiry_date):
        user_id = str(user_id)
        if user_id in self.inventories and item_name in self.inventories[user_id]:
            self.inventories[user_id][item_name]['expiry_date'] = new_expiry_date
            self.save_inventory()