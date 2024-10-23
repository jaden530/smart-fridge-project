# src/health/health_tracker.py

from datetime import datetime, timedelta

class HealthTracker:
    def __init__(self, inventory_manager):
        self.inventory_manager = inventory_manager
        self.daily_logs = {}  # Store daily nutritional intake
        self.goals = {}       # Store user's nutritional goals

    def log_consumption(self, user_id, item_name, quantity, date=None):
        """Log consumption of an item and its nutritional values"""
        if date is None:
            date = datetime.now().date().isoformat()
            
        user_id = str(user_id)
        if user_id not in self.daily_logs:
            self.daily_logs[user_id] = {}
            
        if date not in self.daily_logs[user_id]:
            self.daily_logs[user_id][date] = {
                'items': [],
                'total_nutrients': {
                    'calories': 0,
                    'protein': 0,
                    'carbs': 0,
                    'fat': 0,
                    'fiber': 0,
                    'vitamins': {}
                }
            }
            
        # Get item's nutritional info from inventory
        inventory = self.inventory_manager.get_inventory(user_id)
        if item_name in inventory and inventory[item_name].get('nutritional_info'):
            nutrition = inventory[item_name]['nutritional_info']
            
            # Log the item
            self.daily_logs[user_id][date]['items'].append({
                'item': item_name,
                'quantity': quantity,
                'time': datetime.now().isoformat(),
                'nutrition': nutrition
            })
            
            # Update daily totals
            totals = self.daily_logs[user_id][date]['total_nutrients']
            totals['calories'] += nutrition.get('nf_calories', 0) * quantity
            totals['protein'] += nutrition.get('nf_protein', 0) * quantity
            totals['carbs'] += nutrition.get('nf_total_carbohydrate', 0) * quantity
            totals['fat'] += nutrition.get('nf_total_fat', 0) * quantity
            totals['fiber'] += nutrition.get('nf_dietary_fiber', 0) * quantity

    def get_daily_summary(self, user_id, date=None):
        """Get nutritional summary for a specific date"""
        if date is None:
            date = datetime.now().date().isoformat()
            
        user_id = str(user_id)
        if user_id in self.daily_logs and date in self.daily_logs[user_id]:
            return self.daily_logs[user_id][date]
        return None

    def get_weekly_summary(self, user_id):
        """Get nutritional summary for the past week"""
        weekly_summary = {
            'days': [],
            'averages': {
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0,
                'fiber': 0
            }
        }
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        for i in range(7):
            date = (start_date + timedelta(days=i)).isoformat()
            daily_summary = self.get_daily_summary(user_id, date)
            if daily_summary:
                weekly_summary['days'].append({
                    'date': date,
                    'nutrients': daily_summary['total_nutrients']
                })
                
                # Update averages
                for nutrient in weekly_summary['averages']:
                    weekly_summary['averages'][nutrient] += daily_summary['total_nutrients'][nutrient]
        
        # Calculate averages
        days_logged = len(weekly_summary['days'])
        if days_logged > 0:
            for nutrient in weekly_summary['averages']:
                weekly_summary['averages'][nutrient] /= days_logged
                
        return weekly_summary

    def analyze_trends(self, user_id):
        """Analyze nutritional trends and provide recommendations"""
        weekly_summary = self.get_weekly_summary(user_id)
        recommendations = []
        
        # Compare with goals
        if user_id in self.goals:
            goals = self.goals[user_id]
            averages = weekly_summary['averages']
            
            if 'calories' in goals and averages['calories'] < goals['calories'] * 0.9:
                recommendations.append("Your caloric intake is below your goal. Consider eating more nutrient-dense foods.")
            elif 'calories' in goals and averages['calories'] > goals['calories'] * 1.1:
                recommendations.append("Your caloric intake is above your goal. Consider portion control.")
                
            if 'protein' in goals and averages['protein'] < goals['protein']:
                recommendations.append("Consider adding more protein-rich foods to your diet.")
                
            # Add more nutritional analysis as needed
            
        return recommendations

    def set_goals(self, user_id, goals):
        """Set nutritional goals for a user"""
        self.goals[str(user_id)] = goals