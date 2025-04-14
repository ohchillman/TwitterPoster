from flask import Flask, request, jsonify, render_template
import os
import json
from app.twitter_service import TwitterService
from app.api import api_bp

def create_app():
    app = Flask(__name__)
    
    # Register API blueprint
    app.register_blueprint(api_bp, url_prefix='/api')
    
    @app.route('/', methods=['GET'])
    def index():
        return render_template('index.html')
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "ok"}), 200
    
    @app.route('/post', methods=['POST'])
    def post_tweet():
        data = request.json
        
        # Validate required fields
        required_fields = ['api_key', 'api_secret', 'access_token', 'access_secret', 'text']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            error_response = {
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}",
                "request": {
                    "credentials": {
                        "api_key": data.get('api_key', ''),
                        "api_secret": "***" + data.get('api_secret', '')[-4:] if data.get('api_secret') and len(data.get('api_secret')) > 4 else "***",
                        "access_token": data.get('access_token', ''),
                        "access_secret": "***" + data.get('access_secret', '')[-4:] if data.get('access_secret') and len(data.get('access_secret')) > 4 else "***"
                    },
                    "text": data.get('text', ''),
                    "has_image": 'image' in data and data['image'] is not None,
                    "proxy_settings": data.get('proxy')
                }
            }
            return jsonify(error_response), 400
        
        # Initialize Twitter service with credentials
        twitter_service = TwitterService(
            api_key=data['api_key'],
            api_secret=data['api_secret'],
            access_token=data['access_token'],
            access_secret=data['access_secret'],
            proxy=data.get('proxy')
        )
        
        # Post tweet
        try:
            image_data = None
            if 'image' in data and data['image']:
                image_data = data['image']
                
            result = twitter_service.post_tweet(data['text'], image_data)
            
            # Check if the result indicates an error
            if result.get('status') == 'error':
                error_response = {
                    "status": "error",
                    "error": result.get('error', 'Unknown error occurred'),
                    "request": result.get('request', {}),
                    "response": result.get('response', {})
                }
                return jsonify(error_response), 500
            
            # Return complete result including request and response details
            response = {
                "status": "success",
                "tweet_url": result.get('tweet_url'),
                "tweet_id": result.get('tweet_id'),
                "request": result.get('request', {}),
                "response": result.get('response', {})
            }
            
            return jsonify(response), 201
            
        except Exception as e:
            error_message = str(e)
            
            # Проверяем, не связана ли ошибка с прокси
            proxy_error = None
            if data.get('proxy') and ("proxy" in error_message.lower() or "socket" in error_message.lower() or "connect" in error_message.lower()):
                try:
                    # Attempt to directly test proxy connection
                    proxy_working, proxy_error = twitter_service._test_proxy_connection(data.get('proxy'))
                    if not proxy_working:
                        error_message = f"Proxy connection test failed: {proxy_error}"
                except Exception as proxy_test_error:
                    proxy_error = str(proxy_test_error)
            
            error_response = {
                "status": "error",
                "message": error_message,
                "request": {
                    "credentials": {
                        "api_key": data['api_key'],
                        "api_secret": "***" + data['api_secret'][-4:] if len(data['api_secret']) > 4 else "***",
                        "access_token": data['access_token'],
                        "access_secret": "***" + data['access_secret'][-4:] if len(data['access_secret']) > 4 else "***"
                    },
                    "text": data['text'],
                    "has_image": 'image' in data and data['image'] is not None,
                    "proxy_settings": data.get('proxy')
                }
            }
            
            if proxy_error:
                error_response["proxy_error"] = proxy_error
                
            return jsonify(error_response), 500
    
    return app
