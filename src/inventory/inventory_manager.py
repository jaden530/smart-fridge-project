# src/inventory/inventory_manager.py

import json
from datetime import datetime, timedelta
import requests

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

    def add_item(self, user_id, item_name, quantity=1, expiry_date=None, portion_size=None, nutritional_info=None):
        user_id = str(user_id)
        if user_id not in self.inventories:
            self.inventories[user_id] = {}
        if item_name not in self.inventories[user_id]:
            if nutritional_info is None:
                nutritional_info = self.fetch_nutritional_info(item_name)
            self.inventories[user_id][item_name] = {
                'quantity': quantity,
                'expiry_date': expiry_date or self.get_default_expiry(item_name),
                'added_date': datetime.now().isoformat(),
                'last_detected': datetime.now().isoformat(),
                'category': self.get_category(item_name),
                'portion_size': portion_size,
                'nutritional_info': nutritional_info
            }
        else:
            self.inventories[user_id][item_name]['quantity'] += quantity
            self.inventories[user_id][item_name]['last_detected'] = datetime.now().isoformat()
            if portion_size:
                self.inventories[user_id][item_name]['portion_size'] = portion_size
            if nutritional_info:
                self.inventories[user_id][item_name]['nutritional_info'] = nutritional_info
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
                 self.add_item(user_id, item['class'], portion_size=item.get('portion_size'), nutritional_info=item.get('nutritional_info'))
            else:
                self.inventories[user_id][item['class']]['quantity'] += 1
                self.inventories[user_id][item['class']]['last_detected'] = datetime.now().isoformat()
                if 'portion_size' in item:
                    self.inventories[user_id][item['class']]['portion_size'] = item['portion_size']
                if 'nutritional_info' in item:
                    self.inventories[user_id][item['class']]['nutritional_info'] = item['nutritional_info']

        # Items to be removed (no longer detected)
        for item in current_items - detected_item_names:
            self.remove_item(user_id, item)

        self.save_inventory()

    def fetch_nutritional_info(self, item_name):
        # This is a placeholder. Replace with actual API call to Nutritionix or similar service
        api_url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
        headers = {
            "x-app-id": "YOUR_NUTRITIONIX_APP_ID",
            "x-app-key": "YOUR_NUTRITIONIX_API_KEY",
            "Content-Type": "application/json"
        }
        data = {"query": item_name}
        try:
            response = requests.post(api_url, json=data, headers=headers)
            if response.status_code == 200:
                return response.json()['foods'][0]
        except Exception as e:
            print(f"Error fetching nutritional info: {e}")
        return None

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

    def get_total_nutrition(self, user_id):
        inventory = self.get_inventory(user_id)
        total_nutrition = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0
        }
        for item, details in inventory.items():
            if details.get('nutritional_info'):
                nutrition = details['nutritional_info']
                quantity = details['quantity']
                total_nutrition['calories'] += nutrition.get('nf_calories', 0) * quantity
                total_nutrition['protein'] += nutrition.get('nf_protein', 0) * quantity
                total_nutrition['carbs'] += nutrition.get('nf_total_carbohydrate', 0) * quantity
                total_nutrition['fat'] += nutrition.get('nf_total_fat', 0) * quantity
        return total_nutrition

    def update_expiry_date(self, user_id, item_name, new_expiry_date):
        user_id = str(user_id)
        if user_id in self.inventories and item_name in self.inventories[user_id]:
            self.inventories[user_id][item_name]['expiry_date'] = new_expiry_date
            self.save_inventory()

    def remove_item(self, user_id, item_name, quantity=1):
        user_id = str(user_id)
        if user_id in self.inventories and item_name in self.inventories[user_id]:
            self.inventories[user_id][item_name]['quantity'] -= quantity
            if self.inventories[user_id][item_name]['quantity'] <= 0:
                del self.inventories[user_id][item_name]
            self.save_inventory()