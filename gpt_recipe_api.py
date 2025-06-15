import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI, APIError, RateLimitError, AuthenticationError, APIStatusError, APITimeoutError
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
if os.environ.get("ENVIRONMENT") != "production":
    from dotenv import load_dotenv
    load_dotenv()
app = Flask(__name__)

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

CORS(app, resources={
    r"/*": {
        "origins": os.environ.get("CORS_ORIGINS", "*").split(","),
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

def validate_recipe_data(data):
    """Validate the structure of the recipe data."""
    required_fields = ['title', 'ingredients', 'instructions']
    if not all(field in data for field in required_fields):
        return False, "Missing required fields in recipe data"
    
    if not isinstance(data['ingredients'], list):
        return False, "Ingredients must be a list"
    
    if not isinstance(data['instructions'], list):
        return False, "Instructions must be a list"
    
    return True, None

def handle_error(error):
    if isinstance(error, APIError):
        logger.error(f"API Error: {error.code} - {error.message}")
        return jsonify({'error': f"API Error: {error.code} - {error.message}"}), error.code
    elif isinstance(error, RateLimitError):
        logger.error(f"Rate Limit Error: {error.message}")
        return jsonify({'error': f"Rate Limit Error: {error.message}"}), 429
    elif isinstance(error, AuthenticationError):
        logger.error(f"Authentication Error: {error.message}")
        return jsonify({'error': f"Authentication Error: {error.message}"}), 401
    elif isinstance(error, APIStatusError):
        logger.error(f"API Status Error: {error.code} - {error.message}")
        return jsonify({'error': f"API Status Error: {error.code} - {error.message}"}), error.code
    else:
        logger.error(f"Unexpected error: {str(error)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/recipe', methods=['POST', 'OPTIONS'])
def analyze_recipe():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        # Get the image data from the request
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400

        # Decode the base64 image
        try:
            image_data = base64.b64decode(data['image'].split(',')[1])
            image = Image.open(io.BytesIO(image_data))
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return jsonify({'error': 'Invalid image data'}), 400

        # Convert image to text using GPT-4o
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
                                    "url": f"data:image/jpeg;base64,{base64.b64encode(image_data).decode('utf-8')}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                timeout=60
            )
           
            # Parse and validate the response
            try:
                recipe_data = json.loads(response.choices[0].message.content)
                is_valid, error_message = validate_recipe_data(recipe_data)
                if not is_valid:
                    logger.error(f"Invalid recipe data structure: {error_message}")
                    return jsonify({'error': f'Invalid recipe data: {error_message}'}), 500
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GPT response as JSON: {str(e)}")
                return jsonify({'error': 'Failed to parse recipe data'}), 500

        except AuthenticationError as e:
            logger.error(f"OpenAI API authentication error: {str(e)}")
            return jsonify({'error': 'API authentication failed. Please check API key.'}), 500
        except RateLimitError as e:
            logger.error(f"OpenAI API rate limit exceeded: {str(e)}")
            return jsonify({'error': 'API rate limit exceeded. Please try again later.'}), 429
        except APITimeoutError as e:
            logger.error(f"OpenAI API request timed out: {str(e)}")
            return jsonify({'error': 'Request timed out. Please try again.'}), 504
        except APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return jsonify({'error': 'Error communicating with OpenAI API'}), 500
        except Exception as e:
            logger.error(f"Unexpected error in GPT API call: {str(e)}")
            return jsonify({'error': 'An unexpected error occurred while processing the recipe'}), 500

        return jsonify(recipe_data)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Starting server on port {port}")
    debug = os.environ.get("ENVIRONMENT") != "production"
    app.run(host='0.0.0.0', port=port, debug=debug) 