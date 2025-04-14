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
        
        # Проверка прокси перед созданием клиента
        if self.proxy:
            proxy_working, proxy_error = self._test_proxy_connection(self.proxy)
            if not proxy_working:
                self.init_error = f"Proxy connection test failed: {proxy_error}"
                return
        
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
                self._test_proxy_connection(self.proxy)
                
                # Patch the socket module
                socket.socket = socks.socksocket
                
                # Create API without proxy parameter (SOCKS is applied at socket level)
                api = tweepy.API(auth)
            else:
                # Use HTTP/HTTPS proxy
                api = tweepy.API(auth, proxy=self.proxy.get('https') or self.proxy.get('http'))
                
            client._api = api
            
        return client
    
    def _test_proxy_connection(self, proxy_settings):
        """
        Выполняет прямую проверку работоспособности прокси
        Возвращает (success, error_message)
        """
        if not proxy_settings:
            return True, None
        
        # Извлекаем настройки прокси
        proxy_host = None
        proxy_port = None
        proxy_user = None
        proxy_pass = None
        protocol = "http"
        
        if 'socks5' in proxy_settings:
            proxy_url = proxy_settings.get('socks5')
            try:
                proxy_host, proxy_port, proxy_user, proxy_pass = self._parse_proxy_url(proxy_url)
                protocol = "socks5"
            except Exception as e:
                return False, f"Failed to parse SOCKS5 proxy URL: {str(e)}"
        elif 'http' in proxy_settings or 'https' in proxy_settings:
            proxy_url = proxy_settings.get('https') or proxy_settings.get('http')
            try:
                parsed = urlparse(proxy_url)
                proxy_host = parsed.hostname
                proxy_port = parsed.port
                proxy_user = parsed.username
                proxy_pass = parsed.password
                protocol = "http" if proxy_url.startswith("http://") else "https"
            except Exception as e:
                return False, f"Failed to parse HTTP proxy URL: {str(e)}"
        else:
            return False, "No valid proxy configuration found"
        
        if not proxy_host or not proxy_port:
            return False, "Proxy specified incorrectly, check host and port settings"
        
        # Формируем URL прокси для тестирования
        proxy_url_for_test = f"{protocol}://"
        
        # Добавляем учетные данные, если они предоставлены
        if proxy_user and proxy_pass:
            proxy_url_for_test += f"{proxy_user}:{proxy_pass}@"
        
        proxy_url_for_test += f"{proxy_host}:{proxy_port}"
        
        proxies = {
            "http": proxy_url_for_test,
            "https": proxy_url_for_test
        }
        
        try:
            print(f"Testing proxy connection: {protocol}://{proxy_host}:{proxy_port}")
            # Используем Twitter API для проверки
            test_url = "https://api.twitter.com/2/users/me"
            
            # Делаем запрос с таймаутом
            response = requests.get(
                test_url,
                proxies=proxies,
                timeout=5,
                # Не проверяем статус ответа, только соединение
                allow_redirects=False
            )
            
            print(f"Proxy is working, received response with code: {response.status_code}")
            return True, None
            
        except requests.exceptions.ProxyError as e:
            error_msg = str(e)
            if "SOCKS5" in error_msg.upper():
                error_msg = "Socket error: SOCKS5 authentication failed"
            elif "SOCKS4" in error_msg.upper():
                error_msg = "Socket error: SOCKS4 connection failed"
            elif "authentication" in error_msg.lower():
                error_msg = f"Socket error: {protocol.upper()} authentication failed"
            else:
                error_msg = f"Socket error: {protocol.upper()} connection failed"
            
            print(f"Proxy error during direct test: {error_msg}")
            return False, error_msg
            
        except requests.exceptions.Timeout as e:
            error_msg = f"Socket error: {protocol.upper()} connection timeout"
            print(f"Proxy connection timeout during direct test: {error_msg}")
            return False, error_msg
            
        except requests.RequestException as e:
            error_msg = str(e)
            if "connection" in error_msg.lower():
                error_msg = f"Socket error: Could not connect to {protocol.upper()} proxy"
            else:
                error_msg = f"Socket error: {protocol.upper()} proxy error - {error_msg}"
            
            print(f"Request error through proxy during direct test: {error_msg}")
            return False, error_msg
    
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
        
        # Повторная проверка прокси перед публикацией, если необходимо
        if self.proxy:
            proxy_working, proxy_error = self._test_proxy_connection(self.proxy)
            if not proxy_working:
                error_message = f"Proxy connection test failed: {proxy_error}"
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
                    # Проверяем прокси перед загрузкой изображения
                    proxy_working, proxy_error = self._test_proxy_connection(self.proxy)
                    if not proxy_working:
                        raise Exception(f"Proxy connection test failed before image upload: {proxy_error}")
                        
                    if 'socks5' in self.proxy:
                        # SOCKS5 proxy is already configured at socket level
                        api = tweepy.API(auth)
                    else:
                        # Use HTTP/HTTPS proxy
                        api = tweepy.API(auth, proxy=self.proxy.get('https') or self.proxy.get('http'))
                else:
                    api = tweepy.API(auth)
                
                # Decode base64 image
                try:
                    image_binary = base64.b64decode(image_data)
                    media = api.media_upload(filename='image.png', file=io.BytesIO(image_binary))
                    media_id = media.media_id
                    response_details["media_id"] = media_id
                except Exception as e:
                    raise Exception(f"Failed to upload image: {str(e)}")
                
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
            
            # Проверяем, не связана ли ошибка с прокси
            if self.proxy and ("proxy" in error_message.lower() or "socket" in error_message.lower() or "connect" in error_message.lower()):
                proxy_working, proxy_error = self._test_proxy_connection(self.proxy)
                if not proxy_working:
                    error_message = f"Proxy connection test failed: {proxy_error}"
                    response_details["error"] = error_message
            
            return {
                "status": "error",
                "error": error_message,
                "request": request_details,
                "response": response_details
            }