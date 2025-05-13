"""
Flask application with Azure Content Safety integration - Updated to match Azure SDK structure
"""
from flask import Flask, request, jsonify
import os
import asyncio
from azure.ai.contentsafety.aio import ContentSafetyClient
from azure.ai.contentsafety.models import TextCategory
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from azure.ai.contentsafety.models import AnalyzeTextOptions
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({"status": "healthy"})

@app.route('/')
def hello_world():
    """Example root endpoint."""
    return jsonify({"message": "Hello, World!"})

# Define the async function separately
async def analyze_content_safety(text):
    """
    Analyze text content for safety issues using Azure Content Safety API.
    """
    try:
        # Get Azure credentials from environment variables
        key = os.environ.get("CONTENT_SAFETY_KEY")
        endpoint = os.environ.get("CONTENT_SAFETY_ENDPOINT")
        
        print(f"API Key (first 5 chars): {key[:5] if key else 'Not found'}")
        print(f"Endpoint: {endpoint}")
        
        if not key or not endpoint:
            return {
                "error": "Azure Content Safety credentials not configured. "
                        "Set CONTENT_SAFETY_KEY and CONTENT_SAFETY_ENDPOINT environment variables."
            }, 500
        
        # Create a Content Safety client
        client = ContentSafetyClient(endpoint, AzureKeyCredential(key))
        
        # Analyze the text
        async with client:
            # Construct a request
            request_options = AnalyzeTextOptions(text=text)
            
            # Analyze text
            response = await client.analyze_text(request_options)
        
        # Extract results using the same structure as the original Azure sample
        # Find the category results
        hate_result = next((item for item in response.categories_analysis if item.category == TextCategory.HATE), None)
        self_harm_result = next((item for item in response.categories_analysis if item.category == TextCategory.SELF_HARM), None)
        sexual_result = next((item for item in response.categories_analysis if item.category == TextCategory.SEXUAL), None)
        violence_result = next((item for item in response.categories_analysis if item.category == TextCategory.VIOLENCE), None)
        
        print(hate_result)


        results = {
            "hate": {"severity": hate_result.severity} if hate_result else None,
            "selfHarm": {"severity": self_harm_result.severity} if self_harm_result else None,
            "sexual": {"severity": sexual_result.severity} if sexual_result else None,
            "violence": {"severity": violence_result.severity} if violence_result else None
        }
        
        # Filter out None values
        results = {k: v for k, v in results.items() if v is not None}
        
        return {
            "text": text,
            "results": results
        }, 200
        
    except Exception as e:
        print(f"Error in analyze_content_safety: {str(e)}")
        return {"error": str(e)}, 500

# Create a synchronous route that runs the async function
@app.route('/contenttextsafety', methods=['POST'])
def content_text_safety():
    """
    Analyze text content for safety issues.
    
    Expects a JSON payload with a 'text' field.
    Returns safety analysis results.
    """
    try:
        # Get text from request body
        request_data = request.get_json()
        if not request_data or 'text' not in request_data:
            return jsonify({"error": "Request must include 'text' field"}), 400
        
        text_to_analyze = request_data['text']
        
        # Use a new event loop to run the async function
        result, status_code = asyncio.run(analyze_content_safety(text_to_analyze))
        
        return jsonify(result), status_code
        
    except HttpResponseError as e:
        error_response = {
            "error": "Azure Content Safety API error",
            "details": {}
        }
        
        if hasattr(e, 'error') and e.error:
            error_response["details"]["code"] = e.error.code
            error_response["details"]["message"] = e.error.message
        
        return jsonify(error_response), 500
    
    except Exception as e:
        error_msg = str(e)
        print(f"Error in content_text_safety: {error_msg}")
        return jsonify({"error": error_msg}), 500

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Print loaded environment variables on startup (without revealing full key)
    key = os.environ.get("CONTENT_SAFETY_KEY", "Not found")
    endpoint = os.environ.get("CONTENT_SAFETY_ENDPOINT", "Not found")
    
    print(f"Loaded environment variables:")
    print(f"CONTENT_SAFETY_KEY: {key[:5]}... (truncated)")
    print(f"CONTENT_SAFETY_ENDPOINT: {endpoint}")
    
    # For development using Flask's built-in server
    app.run(debug=True, host='0.0.0.0', port=8000)