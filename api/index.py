from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return """
    <html>
        <head><title>NEUROBUDDYY.AI</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>🧠 Welcome to NEUROBUDDYY.AI</h1>
            <p>Your AI Health Assistant is Live!</p>
            <p>Developed by 0 Day Coders</p>
            <p>API Status: ✅ Working</p>
        </body>
    </html>
    """

@app.route('/api/health')
def health():
    return jsonify({
        "status": "healthy", 
        "message": "NEUROBUDDYY.AI API is running!",
        "developer": "0 Day Coders"
    })

@app.route('/api/test', methods=['POST'])
def test():
    data = request.get_json()
    return jsonify({"received": data, "status": "success"})

if __name__ == '__main__':
    app.run()
