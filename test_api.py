import requests
import base64
import os

def test_api_with_image(image_path):
    print(f"\nTesting API with image: {image_path}")
    try:
        # Read and encode the image
        with open(image_path, 'rb') as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
        # Make the request
        response = requests.post(
            'https://invoice-api.onrender.com/api/invoice',
            json={
                'image': f'data:image/jpeg;base64,{base64_image}'
            },
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Invoice extracted successfully!")
            print("Invoice data:", response.json())
        else:
            print("Error:", response.text)
            
    except Exception as e:
        print(f"Error: {str(e)}")

# Test with an image
image_path = 'test.JPG'  # Replace with your image path
if os.path.exists(image_path):
    test_api_with_image(image_path)
else:
    print(f"Please provide a valid image path. Current path '{image_path}' not found.") 