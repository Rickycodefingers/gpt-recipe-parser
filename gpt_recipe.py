import os
from openai import OpenAI
import base64
from typing import Dict, List
import json
import re
import sys

class GPTRecipeProcessor:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def process_recipe_image(self, image_path: str) -> Dict:
        """Process recipe image using GPT-4o Vision."""
        # Encode the image
        base64_image = self.encode_image(image_path)
        
        # Create the API request
        response = self.client.chat.completions.create(
            model="gpt-4o",  # Use the latest vision model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract the recipe from this image. Return a JSON object with the following structure: {'title': 'Recipe Title', 'ingredients': ['ingredient1', 'ingredient2', ...], 'instructions': ['step1', 'step2', ...]}. Respond only with valid JSON."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        # Print the raw response for debugging
        raw_content = response.choices[0].message.content
        print("\nRaw GPT response:\n", raw_content)
        
        # Strip code block markers if present
        cleaned_content = re.sub(r'^```[a-zA-Z]*\n|```$', '', raw_content.strip(), flags=re.MULTILINE)
        
        # Parse the response
        try:
            recipe_data = json.loads(cleaned_content)
            return recipe_data
        except json.JSONDecodeError:
            print("Error: Could not parse GPT response as JSON")
            return None

def main():
    # Get the API key from environment variable
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        return
    processor = GPTRecipeProcessor(api_key)
    
    # Get image path from command-line argument
    if len(sys.argv) < 2:
        print("Error: Please provide an image path as a command-line argument.")
        return
    image_path = sys.argv[1]
    
    # Process the image
    recipe_data = processor.process_recipe_image(image_path)
    
    if recipe_data:
        print("\nRecipe Title:", recipe_data.get('title', 'No title found'))
        print("\nIngredients:")
        for ingredient in recipe_data.get('ingredients', []):
            print(f"- {ingredient}")
        print("\nInstructions:")
        for i, instruction in enumerate(recipe_data.get('instructions', []), 1):
            print(f"{i}. {instruction}")
    else:
        print("Failed to process recipe image")

if __name__ == "__main__":
    main() 