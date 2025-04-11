# Twitter Poster API

A service for posting content to Twitter via API with proxy support. This service accepts POST requests with Twitter credentials, text content, optional images, and proxy settings, then posts to Twitter and returns the tweet URL.

## Features

- Post text content to Twitter
- Support for PNG image uploads (1 image per post)
- Proxy support for Twitter API connections
- Simple REST API with JSON request/response format
- Dockerized deployment for easy setup

## API Endpoints

### Health Check

```
GET /health
```

Response:
```json
{
  "status": "ok"
}
```

### Post Tweet

```
POST /post
```

Request Body:
```json
{
  "api_key": "YOUR_TWITTER_API_KEY",
  "api_secret": "YOUR_TWITTER_API_SECRET",
  "access_token": "YOUR_TWITTER_ACCESS_TOKEN",
  "access_secret": "YOUR_TWITTER_ACCESS_SECRET",
  "text": "Your tweet text",
  "image": "BASE64_ENCODED_PNG_IMAGE", // Optional
  "proxy": { // Optional
    "http": "http://user:pass@host:port",
    "https": "https://user:pass@host:port"
  }
}
```

Successful Response (201 Created):
```json
{
  "status": "success",
  "tweet_url": "https://twitter.com/user/status/1234567890",
  "tweet_id": "1234567890"
}
```

Error Response (400 Bad Request):
```json
{
  "status": "error",
  "message": "Missing required fields: api_key, api_secret"
}
```

Error Response (500 Internal Server Error):
```json
{
  "status": "error",
  "message": "Failed to post tweet: Twitter API error message"
}
```

### API Documentation

```
GET /api/docs
```

Returns detailed API documentation in JSON format.

## Setup and Deployment

### Prerequisites

- Docker and Docker Compose

### Deployment with Docker

1. Clone the repository:
```bash
git clone https://github.com/ohchillman/TwitterPoster.git
cd TwitterPoster
```

2. Build and start the Docker container:
```bash
docker-compose up -d
```

The service will be available at http://localhost:5000

### Example Usage

Using curl to post a tweet:

```bash
curl -X POST http://localhost:5000/post \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "YOUR_TWITTER_API_KEY",
    "api_secret": "YOUR_TWITTER_API_SECRET",
    "access_token": "YOUR_TWITTER_ACCESS_TOKEN",
    "access_secret": "YOUR_TWITTER_ACCESS_SECRET",
    "text": "Hello from Twitter Poster API!"
  }'
```

Posting with an image (base64 encoded PNG):

```bash
curl -X POST http://localhost:5000/post \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "YOUR_TWITTER_API_KEY",
    "api_secret": "YOUR_TWITTER_API_SECRET",
    "access_token": "YOUR_TWITTER_ACCESS_TOKEN",
    "access_secret": "YOUR_TWITTER_ACCESS_SECRET",
    "text": "Hello with image!",
    "image": "BASE64_ENCODED_PNG_IMAGE"
  }'
```

## Development

### Running Tests

```bash
docker-compose run app python -m unittest discover tests
```

### Local Development Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python run.py
```
