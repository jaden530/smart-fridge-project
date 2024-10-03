# recipes.py

recipes = [
    {
        "name": "Fruit Salad",
        "ingredients": ["banana", "orange", "apple", "grape"],
        "instructions": "Chop all fruits and mix in a bowl."
    },
    {
        "name": "Vegetable Stir Fry",
        "ingredients": ["carrot", "broccoli", "pepper", "onion"],
        "instructions": "Chop vegetables, stir fry in a pan with oil and seasonings."
    },
    {
        "name": "Banana Smoothie",
        "ingredients": ["banana", "milk", "yogurt"],
        "instructions": "Blend all ingredients until smooth."
    },
    # Add more recipes as needed
]

def find_matching_recipes(inventory):
    matching_recipes = []
    for recipe in recipes:
        if all(ingredient in inventory for ingredient in recipe['ingredients']):
            matching_recipes.append(recipe)
    return matching_recipes