# src/recipes/recipe_manager.py

from typing import List, Dict, Optional
from datetime import datetime

class RecipeManager:
    def __init__(self, recipe_api):
        self.recipe_api = recipe_api
        self.cached_recipes = {}
        self.user_ratings = {}
        
    def search_recipes(self, 
                      ingredients: List[str] = None,
                      dietary_restrictions: List[str] = None,
                      max_cooking_time: int = None,
                      min_rating: float = None,
                      nutrition_requirements: Dict = None,
                      difficulty_level: str = None) -> List[Dict]:
        """
        Advanced recipe search with multiple filters
        """
        # Start with basic ingredient search
        recipes = self.recipe_api.find_recipes_by_ingredients(ingredients)
        
        if not recipes:
            return []
            
        filtered_recipes = []
        
        for recipe in recipes:
            matches_criteria = True
            
            # Apply filters
            if dietary_restrictions:
                if not all(diet in recipe.get('diets', []) for diet in dietary_restrictions):
                    matches_criteria = False
                    
            if max_cooking_time and recipe.get('readyInMinutes', 0) > max_cooking_time:
                matches_criteria = False
                
            if nutrition_requirements:
                recipe_nutrition = recipe.get('nutrition', {})
                for nutrient, required_value in nutrition_requirements.items():
                    if recipe_nutrition.get(nutrient, 0) < required_value:
                        matches_criteria = False
                        break
                        
            if difficulty_level:
                recipe_difficulty = self._calculate_difficulty(recipe)
                if recipe_difficulty != difficulty_level:
                    matches_criteria = False
                    
            if matches_criteria:
                filtered_recipes.append(recipe)
                
        return filtered_recipes
    
    def _calculate_difficulty(self, recipe: Dict) -> str:
        """
        Calculate recipe difficulty based on various factors
        """
        score = 0
        
        # Factor in number of ingredients
        ingredients_count = len(recipe.get('extendedIngredients', []))
        if ingredients_count > 10:
            score += 2
        elif ingredients_count > 5:
            score += 1
            
        # Factor in preparation time
        prep_time = recipe.get('readyInMinutes', 0)
        if prep_time > 60:
            score += 2
        elif prep_time > 30:
            score += 1
            
        # Factor in number of steps
        steps_count = len(recipe.get('analyzedInstructions', [{}])[0].get('steps', []))
        if steps_count > 8:
            score += 2
        elif steps_count > 4:
            score += 1
            
        # Convert score to difficulty level
        if score >= 4:
            return 'advanced'
        elif score >= 2:
            return 'intermediate'
        return 'beginner'
    
    def get_recipe_details(self, recipe_id: int) -> Optional[Dict]:
        """
        Get detailed recipe information with caching
        """
        if recipe_id in self.cached_recipes:
            return self.cached_recipes[recipe_id]
            
        recipe_details = self.recipe_api.get_recipe_details(recipe_id)
        if recipe_details:
            self.cached_recipes[recipe_id] = recipe_details
        return recipe_details
    
    def filter_by_health_goals(self, 
                             recipes: List[Dict],
                             calorie_target: int = None,
                             protein_target: int = None,
                             carb_target: int = None,
                             fat_target: int = None) -> List[Dict]:
        """
        Filter recipes based on nutritional goals
        """
        filtered_recipes = []
        
        for recipe in recipes:
            nutrition = recipe.get('nutrition', {}).get('nutrients', {})
            
            matches_goals = True
            
            if calorie_target and nutrition.get('calories', 0) > calorie_target:
                matches_goals = False
            if protein_target and nutrition.get('protein', 0) < protein_target:
                matches_goals = False
            if carb_target and nutrition.get('carbohydrates', 0) > carb_target:
                matches_goals = False
            if fat_target and nutrition.get('fat', 0) > fat_target:
                matches_goals = False
                
            if matches_goals:
                filtered_recipes.append(recipe)
                
        return filtered_recipes