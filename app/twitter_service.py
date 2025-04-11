import tweepy
import base64
import requests
import io
import socks
import socket
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
            proxy (dict, optional): Proxy configuration with format:
                - HTTP/HTTPS: {"http": "http://user:pass@host:port", "https": "https://user:pass@host:port"}
                - SOCKS5: {"socks5": "socks5://user:pass@host:port"}
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
            
            # Handle different proxy types
            if 'socks5' in self.proxy:
                # Parse SOCKS5 proxy URL
                proxy_url = self.proxy.get('socks5')
                parsed = urlparse(proxy_url)
                
                # Extract proxy components
                proxy_host = parsed.hostname
                proxy_port = parsed.port
                proxy_user = parsed.username
                proxy_pass = parsed.password
                
                # Set up SOCKS5 proxy
                if proxy_user and proxy_pass:
                    socks.set_default_proxy(socks.SOCKS5, proxy_host, proxy_port, username=proxy_user, password=proxy_pass)
                else:
                    socks.set_default_proxy(socks.SOCKS5, proxy_host, proxy_port)
                
                # Patch the socket module
                socket.socket = socks.socksocket
                
                # Create API without proxy parameter (SOCKS is applied at socket level)
                api = tweepy.API(auth)
            else:
                # Use HTTP/HTTPS proxy
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
            dict: Dictionary containing tweet_id, tweet_url and request details
        """
        request_details = {
            "credentials": {
                "api_key": self.api_key,
                "api_secret": "***" + self.api_secret[-4:],
                "access_token": self.access_token,
                "access_secret": "***" + self.access_secret[-4:]
            },
            "text": text,
            "has_image": image_data is not None,
            "proxy_settings": self.proxy
        }
        
        response_details = {}
        
        try:
            if not image_data:
                # Post text-only tweet
                response = self.client.create_tweet(text=text)
                tweet_id = response.data['id']
                response_details["tweet_type"] = "text_only"
            else:
                # Post tweet with media
                # First, we need to upload the media using the API v1.1
                auth = tweepy.OAuth1UserHandler(
                    self.api_key, self.api_secret,
                    self.access_token, self.access_secret
                )
                
                # Configure API with proxy if provided
                if self.proxy:
                    if 'socks5' in self.proxy:
                        # SOCKS5 proxy is already configured at socket level
                        api = tweepy.API(auth)
                    else:
                        # Use HTTP/HTTPS proxy
                        api = tweepy.API(auth, proxy=self.proxy.get('https') or self.proxy.get('http'))
                else:
                    api = tweepy.API(auth)
                
                # Decode base64 image
                image_binary = base64.b64decode(image_data)
                media = api.media_upload(filename='image.png', file=io.BytesIO(image_binary))
                media_id = media.media_id
                response_details["media_id"] = media_id
                
                # Post tweet with media
                response = self.client.create_tweet(text=text, media_ids=[media_id])
                tweet_id = response.data['id']
                response_details["tweet_type"] = "with_image"
            
            # Construct tweet URL
            tweet_url = f"https://twitter.com/user/status/{tweet_id}"
            
            response_details["status"] = "success"
            response_details["tweet_id"] = tweet_id
            response_details["tweet_url"] = tweet_url
            
            return {
                "tweet_id": tweet_id,
                "tweet_url": tweet_url,
                "request": request_details,
                "response": response_details
            }
            
        except Exception as e:
            error_message = str(e)
            response_details["status"] = "error"
            response_details["error"] = error_message
            
            raise Exception(error_message)
