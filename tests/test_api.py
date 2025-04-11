import unittest
import json
import base64
from unittest.mock import patch, MagicMock
from app.main import create_app
from app.twitter_service import TwitterService

class TestTwitterPoster(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True
        
        # Test data
        self.test_credentials = {
            'api_key': 'test_api_key',
            'api_secret': 'test_api_secret',
            'access_token': 'test_access_token',
            'access_secret': 'test_access_secret',
            'text': 'Test tweet'
        }
        
        # Mock image data (base64 encoded small PNG)
        self.test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')
    
    def test_api_docs_endpoint(self):
        """Test the API documentation endpoint"""
        response = self.client.get('/api/docs')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('endpoints', data)
        self.assertIn('version', data)
    
    @patch('app.twitter_service.TwitterService.post_tweet')
    def test_post_tweet_text_only(self, mock_post_tweet):
        """Test posting a text-only tweet"""
        # Mock the post_tweet method
        mock_post_tweet.return_value = {
            'tweet_id': '1234567890',
            'tweet_url': 'https://twitter.com/user/status/1234567890'
        }
        
        # Send request
        response = self.client.post(
            '/post',
            data=json.dumps(self.test_credentials),
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['tweet_url'], 'https://twitter.com/user/status/1234567890')
        self.assertEqual(data['tweet_id'], '1234567890')
        
        # Verify mock was called with correct parameters
        mock_post_tweet.assert_called_once_with('Test tweet', None)
    
    @patch('app.twitter_service.TwitterService.post_tweet')
    def test_post_tweet_with_image(self, mock_post_tweet):
        """Test posting a tweet with an image"""
        # Mock the post_tweet method
        mock_post_tweet.return_value = {
            'tweet_id': '1234567890',
            'tweet_url': 'https://twitter.com/user/status/1234567890'
        }
        
        # Add image to test data
        test_data = self.test_credentials.copy()
        test_data['image'] = self.test_image
        
        # Send request
        response = self.client.post(
            '/post',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        
        # Verify mock was called with correct parameters
        mock_post_tweet.assert_called_once_with('Test tweet', self.test_image)
    
    def test_missing_required_fields(self):
        """Test error handling for missing required fields"""
        # Remove required field
        incomplete_data = self.test_credentials.copy()
        del incomplete_data['api_key']
        
        # Send request
        response = self.client.post(
            '/post',
            data=json.dumps(incomplete_data),
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertIn('Missing required fields', data['message'])
    
    @patch('app.twitter_service.TwitterService.post_tweet')
    def test_error_handling(self, mock_post_tweet):
        """Test error handling when Twitter API fails"""
        # Mock the post_tweet method to raise an exception
        mock_post_tweet.side_effect = Exception("Twitter API error")
        
        # Send request
        response = self.client.post(
            '/post',
            data=json.dumps(self.test_credentials),
            content_type='application/json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Twitter API error')

if __name__ == '__main__':
    unittest.main()
