"""
Run the Flask application with Waitress on Windows - for production use
Includes proper .env file loading
"""
from waitress import serve
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Print loaded environment variables on startup (without revealing full key)
key = os.environ.get("CONTENT_SAFETY_KEY", "Not found")
endpoint = os.environ.get("CONTENT_SAFETY_ENDPOINT", "Not found")

print(f"Loaded environment variables:")
print(f"CONTENT_SAFETY_KEY: {key[:5]}... (truncated)")
print(f"CONTENT_SAFETY_ENDPOINT: {endpoint}")

# Import the app after loading environment variables
from main import app

if __name__ == "__main__":
    print("Starting server on http://0.0.0.0:8000")
    print("Use Ctrl+C to stop")
    # Waitress is a production WSGI server that works well on Windows
    serve(app, host="0.0.0.0", port=8000, threads=4)