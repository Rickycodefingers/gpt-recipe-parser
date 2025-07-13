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

# At the top of the file, after loading environment variables
app = Flask(__name__)

# Initialize OpenAI client only if API key is available
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    client = OpenAI(api_key=api_key)
else:
    client = None
    logger.warning("OPENAI_API_KEY not set - API calls will fail")

# Configure CORS
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://harvest-frontend-mocha.vercel.app", 
            "https://harvest-frontend-jxqcp4t10-rickycodefingers-projects.vercel.app",
            "http://localhost:8080"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "expose_headers": ["Content-Type", "Authorization"]
    }
})

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    # Get the origin from the request
    origin = request.headers.get('Origin')
    allowed_origins = [
        'https://harvest-frontend-mocha.vercel.app',
        'https://harvest-frontend-jxqcp4t10-rickycodefingers-projects.vercel.app',
        'http://localhost:8080'
    ]
    
    if origin in allowed_origins:
        response.headers.add('Access-Control-Allow-Origin', origin)
    
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

def validate_invoice_data(data):
    """Validate the structure of the invoice data."""
    required_fields = ['invoice_id', 'vendor', 'date', 'totalAmount', 'confirmedAt', 'items']
    if not all(field in data for field in required_fields):
        return False, "Missing required fields in invoice data"
    
    if not isinstance(data['items'], list):
        return False, "Items must be a list"
    
    # Validate each item in the items list
    for item in data['items']:
        item_fields = ['id', 'name', 'quantity', 'unit', 'price', 'status']
        if not all(field in item for field in item_fields):
            return False, f"Missing required fields in item: {item_fields}"
        
        if item['status'] not in ['normal', 'credited', 'returned']:
            return False, f"Invalid status in item: {item['status']}"
    
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
        return jsonify({'error': 'Authentication Error: {error.message}'}), 401
    elif isinstance(error, APIStatusError):
        logger.error(f"API Status Error: {error.code} - {error.message}")
        return jsonify({'error': f"API Status Error: {error.code} - {error.message}"}), error.code
    else:
        logger.error(f"Unexpected error: {str(error)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

# Register error handlers
@app.errorhandler(APIError)
def handle_api_error(error):
    return handle_error(error)

@app.errorhandler(RateLimitError)
def handle_rate_limit_error(error):
    return handle_error(error)

@app.errorhandler(AuthenticationError)
def handle_auth_error(error):
    return handle_error(error)

@app.errorhandler(APIStatusError)
def handle_status_error(error):
    return handle_error(error)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'environment': os.environ.get('ENVIRONMENT', 'development')})

@app.route('/api/invoice', methods=['POST', 'OPTIONS'])
def analyze_invoice():
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

        # Convert image to text using GPT-4o-mini
        try:
            if not client:
                return jsonify({'error': 'OpenAI API key not configured'}), 500
                
            logger.info("Sending request to OpenAI API...")
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract the invoice data from this image and return it as a valid JSON object. Follow this exact structure: {  invoice_id: number; vendor: string; date: string; totalAmount: number; confirmedAt: string; items: Array<{ id: number; name: string; quantity: number; unit: string; price: number; status: 'normal' | 'credited' | 'returned';}. Do not include any text before or after the JSON object."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64.b64encode(image_data).decode('utf-8')}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                timeout=60
            )
            logger.info("Received response from OpenAI API")
           
            # Parse and validate the response
            try:
                if not response:
                    logger.error("Empty response from OpenAI API")
                    return jsonify({'error': 'Empty response from API'}), 500
                
                if not hasattr(response, 'choices') or not response.choices:
                    logger.error("No choices in API response")
                    return jsonify({'error': 'Invalid response format from API'}), 500
                
                if not hasattr(response.choices[0], 'message'):
                    logger.error("No message in API response choices")
                    return jsonify({'error': 'Invalid response format from API'}), 500
                
                if not response.choices[0].message.content:
                    logger.error("Empty content in API response message")
                    return jsonify({'error': 'Empty content in API response'}), 500

                logger.info(f"Raw GPT response: {response.choices[0].message.content}")
                invoice_data = json.loads(response.choices[0].message.content)
                is_valid, error_message = validate_invoice_data(invoice_data)
                if not is_valid:
                    logger.error(f"Invalid invoice data structure: {error_message}")
                    return jsonify({'error': f'Invalid invoice data: {error_message}'}), 500
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GPT response as JSON: {str(e)}")
                logger.error(f"Raw response content: {response.choices[0].message.content}")
                return jsonify({'error': 'Failed to parse invoice data'}), 500

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
            return jsonify({'error': 'An unexpected error occurred while processing the invoice'}), 500

        return jsonify(invoice_data)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Starting server on port {port}")
    debug = os.environ.get("ENVIRONMENT") != "production"
    app.run(host='0.0.0.0', port=port, debug=debug) 