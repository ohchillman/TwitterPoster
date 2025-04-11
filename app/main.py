from flask import Flask, request, jsonify, render_template
import os
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
            return jsonify({
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
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
            
            return jsonify({
                "status": "success",
                "tweet_url": result['tweet_url'],
                "tweet_id": result['tweet_id']
            }), 201
            
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500
    
    return app
