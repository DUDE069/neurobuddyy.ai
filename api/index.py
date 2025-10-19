from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import random
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import os

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# ========== CONFIGURATION ==========
GMAIL_SENDER = "ariyanabedin00@gmail.com"
GMAIL_APP_PASSWORD = "lfii ikdv hchI frmb"
FAST2SMS_API_KEY = "YOUR_API_KEY_HERE"
ENABLE_SMS = False

# ========== SERVE FRONTEND ==========
# ========== SERVE FRONTEND ==========
@app.route('/')
def home():
    from flask import Response
    try:
        # For Vercel, the working directory is /var/task
        html_path = '/var/task/frontend/index.html'
        
        # Fallback paths
        if not os.path.exists(html_path):
            html_path = 'frontend/index.html'
        
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return Response(content, mimetype='text/html')
    except FileNotFoundError:
        return Response("Frontend not found. Deployment may still be processing.", status=404)
    except Exception as e:
        return Response(f"Error: {str(e)}", status=500)


# ========== LOAD DATA FILES ==========
def load_greetings():
    try:
        with open('api/data/greetings.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data['greetings']
    except Exception as e:
        print(f"Error loading greetings: {e}")
        return []

def load_questions():
    all_questions = []
    files = ['category1_questions.json', 'category2_questions.json',
             'category3_questions.json', 'category4_questions.json']
    
    for file in files:
        try:
            with open(f'api/data/{file}', 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_questions.extend(data['questions'])
        except Exception as e:
            print(f"Error loading {file}: {e}")
    
    return all_questions

greetings_database = load_greetings()
questions_database = load_questions()

def check_greeting(user_input):
    user_input_clean = user_input.lower().strip().replace('?', '').replace('!', '').replace('.', '').replace(',', '')
    for greeting in greetings_database:
        for pattern in greeting['patterns']:
            if user_input_clean == pattern or pattern in user_input_clean or user_input_clean in pattern:
                return greeting['response']
    return None

# ========== HOSPITAL DATABASE (MINI VERSION - WE'LL ADD FULL ONE LATER) ==========
hospitals_database = {
    "Assam": {
        "Guwahati": [
            {
                "hospital": "GNRC Hospital Dispur",
                "email": "info@gnrchospitals.com",
                "phone": "+91-1800-345-0022",
                "distance": "5 km",
                "coordinates": {"lat": 26.1393, "lng": 91.7946}
            },
            {
                "hospital": "Down Town Hospital",
                "email": "dth@downtowngroup.org",
                "phone": "+91-9854074073",
                "distance": "7 km",
                "coordinates": {"lat": 26.1387, "lng": 91.7999}
            }
        ],
        "Kamrup Metropolitan": [
            {
                "hospital": "GNRC Sixmile",
                "email": "info@gnrchospitals.com",
                "phone": "+91-1800-345-0011",
                "distance": "6 km",
                "coordinates": {"lat": 26.1313, "lng": 91.8078}
            }
        ]
    }
}

# ========== EMAIL FUNCTION ==========
def send_emergency_email(hospital_email, hospital_name, patient_location):
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_SENDER
        msg['To'] = hospital_email
        msg['Subject'] = '🚨 [DEMO] NEURO EMERGENCY - NEUROBUDDYY.AI'
        
        html_body = f"""
        <html>
        <body>
            <h2 style="color: red;">🚨 NEUROLOGICAL EMERGENCY ALERT</h2>
            <p><strong>Hospital:</strong> {hospital_name}</p>
            <p><strong>Location:</strong> {patient_location['area']}, {patient_location['district']}, {patient_location['state']}</p>
            <p><strong>Time:</strong> {datetime.now().strftime('%d %B %Y, %I:%M %p')}</p>
            <p><strong>Developed by:</strong> ZERODAYCODERS</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        return {'status': 'success'}
    except Exception as e:
        return {'status': 'failed', 'error': str(e)}

# ========== API ENDPOINTS ==========

@app.route('/get-suggestions', methods=['POST'])
def get_suggestions():
    try:
        user_input = request.json['text'].lower().strip()
        
        if check_greeting(user_input):
            return jsonify({'suggestions': []})
        
        search_words = user_input.split()
        matching = []
        
        for q in questions_database:
            question_lower = q['question'].lower()
            if all(word in question_lower for word in search_words):
                matching.append(q['question'])
        
        matching.sort(key=len)
        return jsonify({'suggestions': matching[:10]})
    
    except Exception as e:
        return jsonify({'suggestions': []})

@app.route('/get-answer', methods=['POST'])
def get_answer():
    try:
        selected_question = request.json['question']
        
        greeting_response = check_greeting(selected_question)
        if greeting_response:
            return jsonify({'answer': greeting_response})
        
        for q in questions_database:
            if q['question'] == selected_question:
                return jsonify({'answer': q['answer']})
        
        return jsonify({'answer': 'I am not able to identify your question. Please try selecting from suggested questions.'})
    
    except Exception as e:
        return jsonify({'answer': 'Error processing request'})

@app.route('/save-user-location', methods=['POST'])
def save_user_location():
    try:
        data = request.json
        state = data.get('state')
        district = data.get('district')
        area = data.get('area')
        
        hospitals = None
        if state in hospitals_database and district in hospitals_database[state]:
            hospitals = hospitals_database[state][district]
        
        if not hospitals:
            return jsonify({"success": False, "message": "No hospital found"}), 404
        
        return jsonify({
            "success": True,
            "hospital": hospitals,
            "message": "Location saved successfully"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/emergency-alert', methods=['POST'])
def emergency_alert():
    try:
        data = request.json
        location = data.get('location')
        
        state = location.get('state')
        district = location.get('district')
        area = location.get('area')
        
        if state not in hospitals_database or district not in hospitals_database[state]:
            return jsonify({"success": False, "message": "No hospitals configured"}), 404
        
        hospitals = hospitals_database[state][district]
        primary_hospital = hospitals[0]
        
        reference_id = f"EMG{random.randint(10000, 99999)}"
        
        email_result = send_emergency_email(
            hospital_email=primary_hospital['email'],
            hospital_name=primary_hospital['hospital'],
            patient_location={'state': state, 'district': district, 'area': area}
        )
        
        return jsonify({
            "success": True,
            "reference_id": reference_id,
            "hospital_name": primary_hospital['hospital'],
            "hospital_phone": primary_hospital['phone'],
            "hospital_email": primary_hospital['email'],
            "message": "Emergency alert sent successfully",
            "email_status": email_result['status']
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/test', methods=['GET'])
def test():
    return jsonify({
        'status': 'Backend working!',
        'total_questions': len(questions_database),
        'greetings': len(greetings_database),
        'developer': 'ZERODAYCODERS',
        'project': 'NEUROBUDDYY.AI'
    })

# Vercel needs this
if __name__ == '__main__':
    app.run()
