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
import langdetect
from langdetect import detect

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

# Supported languages and their codes
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'nl': 'Dutch',
    'pl': 'Polish',
    'ru': 'Russian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh': 'Chinese'
}

def detect_language(text):
    try:
        lang = detect(text)
        return lang if lang in SUPPORTED_LANGUAGES else 'en'
    except:
        return 'en'

def get_recipe_prompt(image_text, language='en'):
    language_name = SUPPORTED_LANGUAGES.get(language, 'English')
    
    return f"""You are a professional chef and recipe analyzer. Analyze this recipe text and provide a detailed breakdown in {language_name}. 
    The text might be in any language, but provide the response in {language_name}.
    
    Recipe Text:
    {image_text}
    
    Please provide the following in {language_name}:
    1. Recipe Name
    2. Servings
    3. Prep Time
    4. Cook Time
    5. Total Time
    6. Ingredients (with measurements)
    7. Instructions (step by step)
    8. Notes/Tips (if any)
    9. Nutritional Information (if available)
    
    Format the response as a JSON object with these exact keys:
    {{
        "name": "Recipe Name",
        "servings": "Number of servings",
        "prep_time": "Prep time in minutes",
        "cook_time": "Cook time in minutes",
        "total_time": "Total time in minutes",
        "ingredients": ["ingredient 1", "ingredient 2", ...],
        "instructions": ["step 1", "step 2", ...],
        "notes": ["note 1", "note 2", ...],
        "nutrition": {{
            "calories": "number",
            "protein": "number",
            "carbs": "number",
            "fat": "number"
        }}
    }}
    
    If any information is not available, use null for that field. Ensure all text is in {language_name}."""

@app.route('/api/recipe', methods=['POST'])
def analyze_recipe():
    try:
        # Get the image data from the request
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400

        # Get language preference (default to detected language)
        language = data.get('language', 'en')
        if language not in SUPPORTED_LANGUAGES:
            language = 'en'

        # Decode the base64 image
        try:
            image_data = base64.b64decode(data['image'].split(',')[1])
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return jsonify({'error': 'Invalid image data'}), 400

        # Convert image to text using GPT-4 Vision
        try:
            response = client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract all text from this recipe image. Include all ingredients, measurements, instructions, and any other relevant information. Preserve the original formatting and language."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64.b64encode(image_data).decode('utf-8')}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            image_text = response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in GPT-4 Vision API call: {str(e)}")
            return jsonify({'error': 'Error processing image with GPT-4 Vision'}), 500

        # If no language specified, detect it from the text
        if language == 'auto':
            language = detect_language(image_text)

        # Get recipe analysis using GPT-4
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional chef and recipe analyzer."},
                    {"role": "user", "content": get_recipe_prompt(image_text, language)}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            recipe_data = json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Error in GPT-4 API call: {str(e)}")
            return jsonify({'error': 'Error analyzing recipe with GPT-4'}), 500

        return jsonify(recipe_data)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True) 