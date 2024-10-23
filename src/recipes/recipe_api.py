# recipe_api.py

import requests
import os
from dotenv import load_dotenv
from openai import OpenAI
import json

# Load environment variables from project root
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(base_dir, '.env'))

class SpoonacularAPI:
    def __init__(self):
        self.api_key = os.getenv('SPOONACULAR_API_KEY')
        if not self.api_key:
            print("Warning: Spoonacular API key not found")
        self.base_url = 'https://api.spoonacular.com/recipes'

    def find_recipes_by_ingredients(self, ingredients, dietary_preference=None):
        if not self.api_key:
            print("Warning: Spoonacular API key not configured")
            return []

        endpoint = f"{self.base_url}/findByIngredients"
        params = {
            'apiKey': self.api_key,
            'ingredients': ','.join(ingredients),
            'number': 10,
            'ranking': 2,
            'ignorePantry': True
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            recipes = response.json()
            
            if dietary_preference:
                filtered_recipes = []
                for recipe in recipes:
                    details = self.get_recipe_details(recipe['id'])
                    if details.get('diets', []) and dietary_preference.lower() in [diet.lower() for diet in details['diets']]:
                        filtered_recipes.append(recipe)
                return filtered_recipes
            return recipes
        except requests.RequestException as e:
            print(f"Error finding recipes: {e}")
            return []

    def get_recipe_details(self, recipe_id):
        if not self.api_key:
            print("Warning: Spoonacular API key not configured")
            return {
                "error": "API key not configured",
                "title": "Recipe Unavailable",
                "instructions": ["API key required to fetch recipe details"],
                "extendedIngredients": []
            }

        endpoint = f"{self.base_url}/{recipe_id}/information"
        params = {
            'apiKey': self.api_key,
            'includeNutrition': True
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching recipe details: {e}")
            return {
                "error": "Failed to fetch recipe details",
                "title": "Recipe Temporarily Unavailable",
                "instructions": ["Unable to load recipe details. Please try again later."],
                "extendedIngredients": []
            }

# Create a single instance of SpoonacularAPI
api = SpoonacularAPI()

# Define the functions that use the API instance
def find_recipes_by_ingredients(ingredients, dietary_preference=None):
    return api.find_recipes_by_ingredients(ingredients, dietary_preference)

def get_recipe_details(recipe_id):
    return api.get_recipe_details(recipe_id)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_ai_recipe_suggestion(ingredients, dietary_preference=None):
    prompt = f"Create a recipe using some or all of these ingredients: {', '.join(ingredients)}. "
    if dietary_preference:
        prompt += f"The recipe should be suitable for a {dietary_preference} diet. "
    prompt += "Format the response as a JSON object with 'name', 'ingredients', and 'instructions' keys."
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates recipes."},
                {"role": "user", "content": prompt}
            ]
        )
        recipe_json = response.choices[0].message.content
        print(f"OpenAI API response: {recipe_json}")
        return json.loads(recipe_json)
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None