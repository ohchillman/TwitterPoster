from flask import Blueprint, jsonify

api_bp = Blueprint('api', __name__)

@api_bp.route('/docs', methods=['GET'])
def api_docs():
    """
    Return API documentation
    """
    docs = {
        "name": "Twitter Poster API",
        "version": "1.0.0",
        "description": "API for posting content to Twitter with proxy support",
        "endpoints": [
            {
                "path": "/health",
                "method": "GET",
                "description": "Health check endpoint",
                "response": {"status": "ok"}
            },
            {
                "path": "/post",
                "method": "POST",
                "description": "Post a tweet with optional image",
                "request_body": {
                    "api_key": "Twitter API key",
                    "api_secret": "Twitter API secret",
                    "access_token": "Twitter access token",
                    "access_secret": "Twitter access token secret",
                    "text": "Tweet text content",
                    "image": "(Optional) Base64 encoded PNG image",
                    "proxy": "(Optional) Proxy configuration object with http/https keys"
                },
                "response": {
                    "status": "success",
                    "tweet_url": "URL to the posted tweet",
                    "tweet_id": "ID of the posted tweet"
                }
            },
            {
                "path": "/docs",
                "method": "GET",
                "description": "API documentation",
                "response": "This documentation"
            }
        ]
    }
    return jsonify(docs)
