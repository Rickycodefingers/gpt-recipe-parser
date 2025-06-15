import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image
import io
import base64
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configure OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def extract_recipe_from_text(text):
    try:
        # Try to parse the text as JSON directly
        recipe = json.loads(text)
        
        # Validate the structure
        required_fields = ['title', 'ingredients', 'instructions']
        if not all(field in recipe for field in required_fields):
            raise ValueError("Missing required fields in recipe")
            
        # Validate ingredients structure
        if not isinstance(recipe['ingredients'], list):
            raise ValueError("Ingredients must be a list")
            
        for ingredient in recipe['ingredients']:
            if not isinstance(ingredient, dict):
                raise ValueError("Each ingredient must be a dictionary")
            if 'item' not in ingredient:
                raise ValueError("Each ingredient must have an 'item' field")
                
        # Validate instructions structure
        if not isinstance(recipe['instructions'], list):
            raise ValueError("Instructions must be a list")
            
        return recipe
        
    except json.JSONDecodeError:
        raise ValueError("Could not parse recipe text as JSON")

@app.route('/api/recipe', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    try:
        image_file = request.files['image']
        image = Image.open(image_file)
        
        # Convert image to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract the recipe from this image. Return ONLY a JSON object with the following structure: {\"title\": \"Recipe Title\", \"ingredients\": [{\"item\": \"ingredient name\", \"amount\": \"amount with unit\", \"notes\": \"any additional notes\"}], \"instructions\": [\"step 1\", \"step 2\", ...]}. Do not include any other text or explanation."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_str}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        # Parse the response
        recipe_text = response.choices[0].message.content
        recipe = extract_recipe_from_text(recipe_text)
        
        return jsonify(recipe)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 