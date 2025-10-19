from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import json

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Serve the frontend HTML
@app.route('/')
def home():
    return send_from_directory('../frontend', 'index.html')

# Health check endpoint
@app.route('/api/health')
def health():
    return jsonify({
        "status": "healthy", 
        "message": "NEUROBUDDYY.AI API is running!",
        "developer": "ZERODAYCODERS"
    })

# Main chat endpoint - this will handle your chatbot queries
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').lower().strip()
        
        # Basic greeting responses
        greetings = ['hi', 'hello', 'hey', 'namaste', 'good morning', 'good evening']
        if any(greet in user_message for greet in greetings):
            return jsonify({
                "response": "Hello! I'm NeuroBuddy, your AI health assistant. How can I help you today?",
                "status": "success"
            })
        
        # Default response for now
        return jsonify({
            "response": f"Thank you for your message: '{data.get('message')}'. Full chatbot logic will be integrated shortly!",
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({
            "response": "Sorry, I encountered an error. Please try again.",
            "status": "error",
            "error": str(e)
        }), 500

# Test endpoint
@app.route('/api/test', methods=['GET', 'POST'])
def test():
    return jsonify({
        "message": "NEUROBUDDYY.AI API is working!",
        "developer": "0DAYCODERS",
        "status": "success"
    })

if __name__ == '__main__':
    app.run()
