import base64
import sys
import os
import json
import requests

# Test data
test_data = {
    "api_key": "6H7PkbJywxciTJwCfWJIypowj",
    "api_secret": "hJbObSkbPvIXF29BWbMqOnDeoDTnOo8CEeq60wnS20oJDr9xhj",
    "access_token": "1900101690990174208-RGYPJT5P1WkXu2PGBGoDFr2sYah8g2",
    "access_secret": "T7BSURYSiwlwFjgwK8Oof82fj25byobtCYWlnLb4BiNLE",
    "text": "Test tweet from TwitterPoster API service! #test #api"
}

def test_health_endpoint():
    """Test the health check endpoint"""
    response = requests.get('http://localhost:5000/health')
    print(f"Health check status code: {response.status_code}")
    print(f"Health check response: {response.json()}")
    return response.status_code == 200

def test_post_endpoint(with_image=False):
    """Test the post endpoint"""
    payload = test_data.copy()
    
    if with_image:
        # Create a simple test image (1x1 pixel PNG)
        try:
            # Check if we have a test image, if not create one
            if not os.path.exists('test_image.png'):
                from PIL import Image
                img = Image.new('RGB', (100, 100), color = (73, 109, 137))
                img.save('test_image.png')
            
            # Read and encode the image
            with open('test_image.png', 'rb') as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
                payload['image'] = encoded_image
                print("Added image to payload")
        except Exception as e:
            print(f"Error preparing image: {e}")
            return False
    
    print(f"Sending POST request to /post endpoint with {'image' if with_image else 'text only'}")
    response = requests.post('http://localhost:5000/post', json=payload)
    print(f"Post endpoint status code: {response.status_code}")
    print(f"Post endpoint response: {response.json()}")
    
    if response.status_code == 201:
        print(f"Success! Tweet URL: {response.json().get('tweet_url')}")
        return True
    else:
        print(f"Failed to post tweet: {response.json().get('message')}")
        return False

if __name__ == "__main__":
    print("Testing TwitterPoster API...")
    
    # Test health endpoint
    if not test_health_endpoint():
        print("Health check failed!")
        sys.exit(1)
    
    # Test post endpoint with text only
    if not test_post_endpoint(with_image=False):
        print("Text-only post test failed!")
        sys.exit(1)
    
    # Uncomment to test with image
    # if not test_post_endpoint(with_image=True):
    #     print("Post with image test failed!")
    #     sys.exit(1)
    
    print("All tests passed successfully!")
