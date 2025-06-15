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

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

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

CORS(app, resources={
    r"/*": {
        "origins": os.environ.get("CORS_ORIGINS", "*").split(","),
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

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
                max_tokens=10000
            )
            recipe_data = json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Error in GPT-4o API call: {str(e)}")
            return jsonify({'error': 'Error analyzing recipe with GPT-4o'}), 500

        return jsonify(recipe_data)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True) 