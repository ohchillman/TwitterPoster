import tweepy
import base64
import requests
import io
from urllib.parse import urlparse

class TwitterService:
    def __init__(self, api_key, api_secret, access_token, access_secret, proxy=None):
        """
        Initialize Twitter service with credentials and optional proxy
        
        Args:
            api_key (str): Twitter API key
            api_secret (str): Twitter API secret
            access_token (str): Twitter access token
            access_secret (str): Twitter access token secret
            proxy (dict, optional): Proxy configuration with format {"http": "http://user:pass@host:port", "https": "https://user:pass@host:port"}
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_secret = access_secret
        self.proxy = proxy
        self.client = self._create_client()
        
    def _create_client(self):
        """
        Create and configure Tweepy client with credentials and proxy if provided
        
        Returns:
            tweepy.Client: Configured Twitter API client
        """
        # Create client with authentication
        client = tweepy.Client(
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.access_token,
            access_token_secret=self.access_secret
        )
        
        # Configure proxy if provided
        if self.proxy:
            auth = tweepy.OAuth1UserHandler(
                self.api_key, self.api_secret,
                self.access_token, self.access_secret
            )
            api = tweepy.API(auth, proxy=self.proxy.get('https') or self.proxy.get('http'))
            client._api = api
            
        return client
    
    def post_tweet(self, text, image_data=None):
        """
        Post a tweet with optional image
        
        Args:
            text (str): Tweet text content
            image_data (str, optional): Base64 encoded image data
            
        Returns:
            dict: Dictionary containing tweet_id and tweet_url
        """
        if not image_data:
            # Post text-only tweet
            response = self.client.create_tweet(text=text)
            tweet_id = response.data['id']
        else:
            # Post tweet with media
            # First, we need to upload the media using the API v1.1
            auth = tweepy.OAuth1UserHandler(
                self.api_key, self.api_secret,
                self.access_token, self.access_secret
            )
            
            # Configure API with proxy if provided
            if self.proxy:
                api = tweepy.API(auth, proxy=self.proxy.get('https') or self.proxy.get('http'))
            else:
                api = tweepy.API(auth)
            
            # Decode base64 image
            try:
                image_binary = base64.b64decode(image_data)
                media = api.media_upload(filename='image.png', file=io.BytesIO(image_binary))
                media_id = media.media_id
                
                # Post tweet with media
                response = self.client.create_tweet(text=text, media_ids=[media_id])
                tweet_id = response.data['id']
            except Exception as e:
                raise Exception(f"Failed to upload image: {str(e)}")
        
        # Construct tweet URL
        tweet_url = f"https://twitter.com/user/status/{tweet_id}"
        
        return {
            "tweet_id": tweet_id,
            "tweet_url": tweet_url
        }
