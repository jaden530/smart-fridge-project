# src/waste_prevention/food_waste_manager.py

from datetime import datetime, timedelta

class FoodWasteManager:
    def __init__(self, inventory_manager):
        self.inventory_manager = inventory_manager
        self.usage_patterns = {}  # Will store item usage patterns
        self.waste_risk_thresholds = {
            'high': 2,  # days until expiry
            'medium': 5,
            'low': 7
        }

    def analyze_waste_risk(self, user_id):
        """Analyzes inventory for items at risk of being wasted."""
        inventory = self.inventory_manager.get_inventory(user_id)
        at_risk_items = {
            'high_risk': [],
            'medium_risk': [],
            'low_risk': []
        }
        
        current_date = datetime.now()
        
        for item, details in inventory.items():
            if 'expiry_date' not in details:
                continue
                
            expiry_date = datetime.fromisoformat(details['expiry_date'])
            days_until_expiry = (expiry_date - current_date).days
            
            if days_until_expiry <= self.waste_risk_thresholds['high']:
                at_risk_items['high_risk'].append({
                    'item': item,
                    'days_left': days_until_expiry,
                    'quantity': details['quantity'],
                    'category': details.get('category', 'uncategorized')
                })
            elif days_until_expiry <= self.waste_risk_thresholds['medium']:
                at_risk_items['medium_risk'].append({
                    'item': item,
                    'days_left': days_until_expiry,
                    'quantity': details['quantity'],
                    'category': details.get('category', 'uncategorized')
                })
            elif days_until_expiry <= self.waste_risk_thresholds['low']:
                at_risk_items['low_risk'].append({
                    'item': item,
                    'days_left': days_until_expiry,
                    'quantity': details['quantity'],
                    'category': details.get('category', 'uncategorized')
                })
        
        return at_risk_items

    def get_waste_prevention_suggestions(self, user_id):
        """Generates suggestions for preventing waste of at-risk items."""
        at_risk_items = self.analyze_waste_risk(user_id)
        suggestions = []
        
        # Prioritize high-risk items
        if at_risk_items['high_risk']:
            suggestions.append({
                'priority': 'high',
                'message': 'These items need immediate attention:',
                'items': at_risk_items['high_risk'],
                'actions': ['Cook today', 'Freeze if possible']
            })
            
        if at_risk_items['medium_risk']:
            suggestions.append({
                'priority': 'medium',
                'message': 'Plan to use these items soon:',
                'items': at_risk_items['medium_risk'],
                'actions': ['Plan meals', 'Consider freezing']
            })
            
        if at_risk_items['low_risk']:
            suggestions.append({
                'priority': 'low',
                'message': 'Keep an eye on these items:',
                'items': at_risk_items['low_risk'],
                'actions': ['Include in meal planning']
            })
            
        return suggestions

    def track_consumption_pattern(self, user_id, item_name, quantity_used):
        """Tracks how quickly items are typically used."""
        if user_id not in self.usage_patterns:
            self.usage_patterns[user_id] = {}
            
        if item_name not in self.usage_patterns[user_id]:
            self.usage_patterns[user_id][item_name] = []
            
        self.usage_patterns[user_id][item_name].append({
            'date': datetime.now(),
            'quantity': quantity_used
        })