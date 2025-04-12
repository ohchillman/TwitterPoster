import tweepy
import base64
import requests
import io
import socks
import socket
import re
from urllib.parse import urlparse, unquote

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
        self.client = None
        
        # Initialize client with proper error handling for proxy issues
        try:
            self.client = self._create_client()
        except Exception as e:
            # Store the initialization error to report it later
            self.init_error = str(e)
        
    def _parse_proxy_url(self, proxy_url):
        """
        Parse proxy URL with custom method to handle complex usernames and passwords
        
        Args:
            proxy_url (str): Proxy URL in format socks5://username:password@host:port
            
        Returns:
            tuple: (host, port, username, password)
        """
        try:
            # First try standard urlparse
            parsed = urlparse(proxy_url)
            
            # Extract basic components
            proxy_host = parsed.hostname
            proxy_port = parsed.port
            
            # Handle authentication with custom parsing for complex usernames/passwords
            if '@' in proxy_url:
                # Extract auth part (everything between protocol and @)
                auth_part = re.search(r'://(.+)@', proxy_url)
                if auth_part:
                    auth_str = auth_part.group(1)
                    # Find the last colon before the @ to split username and password
                    # This handles usernames that may contain colons
                    last_colon_index = auth_str.rfind(':')
                    if last_colon_index != -1:
                        proxy_user = auth_str[:last_colon_index]
                        proxy_pass = auth_str[last_colon_index+1:]
                        # URL decode to handle special characters
                        proxy_user = unquote(proxy_user)
                        proxy_pass = unquote(proxy_pass)
                    else:
                        proxy_user = auth_str
                        proxy_pass = None
                else:
                    proxy_user = None
                    proxy_pass = None
            else:
                proxy_user = None
                proxy_pass = None
                
            return proxy_host, proxy_port, proxy_user, proxy_pass
            
        except Exception as e:
            raise Exception(f"Failed to parse proxy URL: {str(e)}")
    
    def _create_client(self):
        """
        Create and configure Tweepy client with credentials and proxy if provided
        
        Returns:
            tweepy.Client: Configured Twitter API client
        
        Raises:
            Exception: If proxy configuration fails
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
                # Parse SOCKS5 proxy URL with custom method
                proxy_url = self.proxy.get('socks5')
                proxy_host, proxy_port, proxy_user, proxy_pass = self._parse_proxy_url(proxy_url)
                
                if not proxy_host or not proxy_port:
                    raise Exception(f"Invalid proxy URL format: {proxy_url}")
                
                # Debug information
                auth_info = f"Using proxy authentication: User={proxy_user is not None}, Pass={proxy_pass is not None}"
                print(auth_info)
                
                # Set up SOCKS5 proxy
                if proxy_user and proxy_pass:
                    socks.set_default_proxy(socks.SOCKS5, proxy_host, proxy_port, username=proxy_user, password=proxy_pass)
                else:
                    socks.set_default_proxy(socks.SOCKS5, proxy_host, proxy_port)
                
                # Test proxy connection before patching socket
                self._test_proxy_connection(proxy_host, proxy_port, proxy_user, proxy_pass)
                
                # Patch the socket module
                socket.socket = socks.socksocket
                
                # Create API without proxy parameter (SOCKS is applied at socket level)
                api = tweepy.API(auth)
            else:
                # Use HTTP/HTTPS proxy
                api = tweepy.API(auth, proxy=self.proxy.get('https') or self.proxy.get('http'))
                
            client._api = api
            
        return client
    
    def _test_proxy_connection(self, host, port, username=None, password=None):
        """
        Test proxy connection before using it
        
        Args:
            host (str): Proxy host
            port (int): Proxy port
            username (str, optional): Proxy username
            password (str, optional): Proxy password
            
        Raises:
            Exception: If proxy connection fails
        """
        try:
            # Create a test socket
            test_socket = socks.socksocket()
            
            # Configure proxy with authentication if provided
            if username and password:
                test_socket.set_proxy(socks.SOCKS5, host, port, username=username, password=password)
            else:
                test_socket.set_proxy(socks.SOCKS5, host, port)
            
            # Try to connect to Twitter API (timeout after 5 seconds)
            test_socket.settimeout(5)
            test_socket.connect(('api.twitter.com', 443))
            test_socket.close()
        except Exception as e:
            raise Exception(f"Proxy connection test failed: {str(e)}")
    
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
        
        # Check if client initialization failed
        if self.client is None:
            error_message = getattr(self, 'init_error', 'Client initialization failed')
            response_details["status"] = "error"
            response_details["error"] = error_message
            
            return {
                "status": "error",
                "error": error_message,
                "request": request_details,
                "response": response_details
            }
        
        try:
            if not image_data:
                # Post text-only tweet
                response = self.client.create_tweet(text=text)
                
                # Verify that we got a valid response
                if not response or not hasattr(response, 'data') or 'id' not in response.data:
                    raise Exception("Invalid response from Twitter API")
                    
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
                
                # Verify that we got a valid response
                if not response or not hasattr(response, 'data') or 'id' not in response.data:
                    raise Exception("Invalid response from Twitter API")
                    
                tweet_id = response.data['id']
                response_details["tweet_type"] = "with_image"
            
            # Construct tweet URL
            tweet_url = f"https://twitter.com/user/status/{tweet_id}"
            
            response_details["status"] = "success"
            response_details["tweet_id"] = tweet_id
            response_details["tweet_url"] = tweet_url
            
            return {
                "status": "success",
                "tweet_id": tweet_id,
                "tweet_url": tweet_url,
                "request": request_details,
                "response": response_details
            }
            
        except Exception as e:
            error_message = str(e)
            response_details["status"] = "error"
            response_details["error"] = error_message
            
            return {
                "status": "error",
                "error": error_message,
                "request": request_details,
                "response": response_details
            }
