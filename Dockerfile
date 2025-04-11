FROM python:3.9-slim

WORKDIR /app

# Install specific versions of Flask and Werkzeug directly
RUN pip install --no-cache-dir Flask==2.0.1 Werkzeug==2.0.1 tweepy==4.12.1 requests==2.28.2 gunicorn==20.1.0

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]
