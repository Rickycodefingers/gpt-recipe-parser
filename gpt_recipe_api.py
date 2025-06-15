import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image
import io
import base64
import json
import logging
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# Initialize Sentry
sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),  # Add this to your environment variables
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0,
    environment=os.getenv('ENVIRONMENT', 'production')
)

# Configure logging
logging.basicConfig(level=logging.INFO)  # Change to INFO for production
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure CORS for production
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:3000",  # Local development
            "https://your-production-domain.com"  # Replace with your actual domain
        ],
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Configure OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def extract_recipe_from_text(text):
    try:
        logger.debug(f"Attempting to parse recipe text: {text[:100]}...")  # Log first 100 chars
        # Try to parse the text as JSON directly
        recipe = json.loads(text)
        
        # Validate the structure
        required_fields = ['title', 'ingredients', 'instructions']
        if not all(field in recipe for field in required_fields):
            logger.error(f"Missing required fields. Found: {list(recipe.keys())}")
            raise ValueError("Missing required fields in recipe")
            
        # Validate ingredients structure
        if not isinstance(recipe['ingredients'], list):
            logger.error(f"Ingredients is not a list: {type(recipe['ingredients'])}")
            raise ValueError("Ingredients must be a list")
            
        for ingredient in recipe['ingredients']:
            if not isinstance(ingredient, dict):
                logger.error(f"Ingredient is not a dict: {type(ingredient)}")
                raise ValueError("Each ingredient must be a dictionary")
            if 'item' not in ingredient:
                logger.error(f"Ingredient missing 'item' field: {ingredient}")
                raise ValueError("Each ingredient must have an 'item' field")
                
        # Validate instructions structure
        if not isinstance(recipe['instructions'], list):
            logger.error(f"Instructions is not a list: {type(recipe['instructions'])}")
            raise ValueError("Instructions must be a list")
            
        logger.info(f"Successfully parsed recipe: {recipe['title']}")
        return recipe
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        raise ValueError("Could not parse recipe text as JSON")

@app.route('/api/recipe', methods=['POST'])
def process_image():
    logger.info("Received recipe request")
    if 'image' not in request.files:
        logger.error("No image provided in request")
        return jsonify({'error': 'No image provided'}), 400
    
    try:
        image_file = request.files['image']
        logger.debug(f"Received image: {image_file.filename}")
        image = Image.open(image_file)
        
        # Convert image to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        logger.debug("Image converted to base64")
        
        # Call OpenAI API
        logger.info("Calling OpenAI API")
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract the recipe from this image and return it as a valid JSON object. The response must be ONLY the JSON object, with no additional text or explanation. The JSON must follow this exact structure: {\"title\": \"Recipe Title\", \"ingredients\": [{\"item\": \"ingredient name\", \"amount\": \"amount with unit\", \"notes\": \"any additional notes\"}], \"instructions\": [\"step 1\", \"step 2\", ...]}. Make sure the JSON is properly formatted with double quotes and no trailing commas."},
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
            logger.debug(f"Raw OpenAI response: {recipe_text}")
            
            # Try to clean the response if it's not valid JSON
            try:
                # Remove any markdown code block markers
                recipe_text = recipe_text.replace('```json', '').replace('```', '').strip()
                recipe = extract_recipe_from_text(recipe_text)
                logger.info("Successfully processed recipe")
                return jsonify(recipe)
            except ValueError as e:
                logger.error(f"Failed to parse recipe: {str(e)}")
                logger.error(f"Raw text was: {recipe_text}")
                return jsonify({'error': f"Could not parse recipe: {str(e)}"}), 400
                
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}", exc_info=True)
            return jsonify({'error': f"OpenAI API error: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Error processing recipe: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True) 