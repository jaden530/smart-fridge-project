# recipe_api.py

import requests
import os
from dotenv import load_dotenv
from openai import OpenAI
import json

# Try to load from .env file, but don't fail if it doesn't exist
load_dotenv(override=True)

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_api_key():
    # Check multiple possible sources for the API key
    return (os.getenv('SPOONACULAR_API_KEY') or 
            os.environ.get('SPOONACULAR_API_KEY') or 
            input("Please enter your Spoonacular API key: "))

BASE_URL = 'https://api.spoonacular.com/recipes'

def get_ai_recipe_suggestion(ingredients):
    prompt = f"Create a recipe using some or all of these ingredients: {', '.join(ingredients)}. Format the response as a JSON object with 'name', 'ingredients', and 'instructions' keys."
    
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

def find_recipes_by_ingredients(ingredients):
    API_KEY = get_api_key()
    endpoint = f"{BASE_URL}/findByIngredients"
    params = {
        'apiKey': API_KEY,
        'ingredients': ','.join(ingredients),
        'number': 5,
        'ranking': 2
    }
    try:
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            recipes = response.json()
            if recipes:
                return recipes
            else:
                # If no recipes found, try AI suggestion
                ai_recipe = get_ai_recipe_suggestion(ingredients)
                if ai_recipe:
                    return [ai_recipe]  # Return as a list to maintain consistency
                else:
                    return []
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return None
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None
        

def get_recipe_details(recipe_id):
    API_KEY = get_api_key()
    endpoint = f"{BASE_URL}/{recipe_id}/information"
    params = {
        'apiKey': API_KEY,
        'includeNutrition': False
    }
    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None