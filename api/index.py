from flask import Flask, request, jsonify, send_from_directory, Response
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

GMAIL_SENDER = "ariyanabedin00@gmail.com"
GMAIL_APP_PASSWORD = "lfii ikdv hchI frmb"
FAST2SMS_API_KEY = "YOUR_API_KEY_HERE"
ENABLE_SMS = False

@app.route('/')
def home():
    possible_paths = [
        '/var/task/frontend/index.html',
        'frontend/index.html',
        '../frontend/index.html',
        os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html'),
        '/var/task/src/frontend/index.html',
        './frontend/index.html',
    ]
    
    for file_path in possible_paths:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return Response(f.read(), mimetype='text/html')
        except Exception:
            continue
    
    return Response(f"Frontend not found. Tried: {', '.join(possible_paths)}", status=404)

def load_greetings():
    paths = ['api/data/greetings.json', 'data/greetings.json', '../data/greetings.json']
    for path in paths:
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f).get('greetings', [])
        except Exception:
            continue
    print("⚠️ greetings.json not found")
    return []

def load_questions():
    all_questions = []
    files = ['category1_questions.json', 'category2_questions.json', 
             'category3_questions.json', 'category4_questions.json']
    dirs = ['api/data/', 'data/', '../data/']
    
    for file in files:
        for d in dirs:
            try:
                path = os.path.join(d, file)
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        all_questions.extend(json.load(f).get('questions', []))
                    break
            except Exception:
                continue
    return all_questions

greetings_database = load_greetings()
questions_database = load_questions()

print(f"✓ Loaded {len(greetings_database)} greetings, {len(questions_database)} questions")

def check_greeting(user_input):
    if not greetings_database:
        return None
    clean = user_input.lower().strip().replace('?', '').replace('!', '').replace('.', '').replace(',', '')
    for g in greetings_database:
        for p in g.get('patterns', []):
            if clean == p or p in clean or clean in p:
                return g.get('response')
    return None

hospitals_database = {
    "Delhi": {
        "South Delhi": [{"hospital": "AIIMS Delhi", "email": "demo.aiims@example.com", "phone": "+919999999991", "distance": "5 km"}],
        "Central Delhi": [{"hospital": "Ram Manohar Lohia Hospital", "email": "demo.rml@example.com", "phone": "+919999999992", "distance": "3 km"}]
    },
    "Maharashtra": {
        "Mumbai City": [
            {"hospital": "KEM Hospital Mumbai", "email": "demo.kem@example.com", "phone": "+919999999991", "distance": "5 km", "coordinates": {"lat": 19.002473974696805, "lng": 72.84148838080044}},
            {"hospital": "Lilavati Hospital Mumbai", "email": "demo.lilavati@example.com", "phone": "+919999999992", "distance": "7 km", "coordinates": {"lat": 19.0596, "lng": 72.8295}},
            {"hospital": "Hinduja Hospital Mumbai", "email": "demo.hinduja@example.com", "phone": "+919999999993", "distance": "10 km", "coordinates": {"lat": 19.0522, "lng": 72.8346}},
            {"hospital": "Bombay Hospital Mumbai", "email": "demo.bombay@example.com", "phone": "+919999999994", "distance": "12 km"},
            {"hospital": "Jaslok Hospital Mumbai", "email": "demo.jaslok@example.com", "phone": "+919999999995", "distance": "15 km"}
        ],
        "Pune": [
            {"hospital": "Ruby Hall Clinic Pune", "email": "demo.ruby@example.com", "phone": "+919999999996", "distance": "5 km"},
            {"hospital": "Jehangir Hospital Pune", "email": "demo.jehangir@example.com", "phone": "+919999999997", "distance": "6 km"}
        ]
    },
    "Karnataka": {
        "Bangalore": [
            {"hospital": "NIMHANS Bangalore", "email": "demo.nimhans@example.com", "phone": "+919999999998", "distance": "6 km"},
            {"hospital": "Manipal Hospital Bangalore", "email": "demo.manipal@example.com", "phone": "+919999999999", "distance": "8 km"},
            {"hospital": "Apollo Hospital Bangalore", "email": "demo.apollo@example.com", "phone": "+919999999991", "distance": "10 km"}
        ]
    },
    "Assam": {
        "Guwahati": [
            {"hospital": "GNRC Hospital Dispur - Neuroscience Department", "email": "info@gnrchospitals.com", "phone": "+91-1800-345-0022", "distance": "5 km", "coordinates": {"lat": 26.1393220976546, "lng": 91.79459993962551}},
            {"hospital": "Narayana Superspeciality Hospital - Neurology & Neurosurgery", "email": "info.guw@narayanahealth.org", "phone": "+91-361-2680321", "distance": "8 km", "coordinates": {"lat": 26.207774, "lng": 91.677652}},
            {"hospital": "Down Town Hospital - Neurology Department", "email": "dth@downtowngroup.org", "phone": "+91-9854074073", "distance": "7 km", "coordinates": {"lat": 26.13866, "lng": 91.79986}}
        ],
        "Kamrup Metropolitan": [
            {"hospital": "GNRC Sixmile - Neuro-Science Center", "email": "info@gnrchospitals.com", "phone": "+91-1800-345-0011", "distance": "6 km", "coordinates": {"lat": 26.131309412128402, "lng": 91.80778967118864}},
            {"hospital": "Marwari Hospitals - Neurology Department", "email": "info@marwarihospitals.com", "phone": "+91-7099066004", "distance": "9 km", "coordinates": {"lat": 26.1730, "lng": 91.7514}}
        ]
    }
}

def send_emergency_email(hospital_email, hospital_name, patient_location):
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_SENDER
        msg['To'] = hospital_email
        msg['Subject'] = '🚨 [DEMO] NEURO EMERGENCY - NEUROBUDDYY.AI'
        
        html_body = f"""
        <html><body>
            <h2 style="color: red;">🚨 NEUROLOGICAL EMERGENCY ALERT</h2>
            <p><strong>Hospital:</strong> {hospital_name}</p>
            <p><strong>Location:</strong> {patient_location['area']}, {patient_location['district']}, {patient_location['state']}</p>
            <p><strong>Time:</strong> {datetime.now().strftime('%d %B %Y, %I:%M %p')}</p>
            <p><strong>Developed by:</strong> ZERODAYCODERS</p>
        </body></html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        return {'status': 'success'}
    except Exception as e:
        return {'status': 'failed', 'error': str(e)}

def send_emergency_sms(phone_number, hospital_name, patient_location):
    if not ENABLE_SMS:
        return {'status': 'skipped'}
    try:
        message = f"🚨 DEMO: Patient at {patient_location['area']}, {patient_location['district']}, {patient_location['state']}. Neuro emergency."
        url = "https://www.fast2sms.com/dev/bulkV2"
        payload = {'sender_id': 'FSTSMS', 'message': message, 'route': 'q', 'numbers': phone_number.replace('+91', '').replace('+', ''), 'language': 'english'}
        headers = {'authorization': FAST2SMS_API_KEY, 'Content-Type': "application/x-www-form-urlencoded"}
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        return {'status': 'success' if response.json().get('return') else 'failed'}
    except Exception:
        return {'status': 'failed'}

@app.route('/api/get-suggestions', methods=['POST'])
def get_suggestions():
    try:
        user_input = request.json.get('text', '').lower().strip()
        if not questions_database or check_greeting(user_input):
            return jsonify({'suggestions': []})
        
        search_words = user_input.split()
        matching = [q['question'] for q in questions_database if all(w in q.get('question', '').lower() for w in search_words)][:10]
        
        if not matching:
            matching = [q['question'] for q in questions_database if any(w in q.get('question', '').lower() for w in search_words)][:10]
        
        matching.sort(key=len)
        return jsonify({'suggestions': matching[:10]})
    except Exception:
        return jsonify({'suggestions': []})

@app.route('/api/get-answer', methods=['POST'])
def get_answer():
    try:
        question = request.json.get('question', '')
        
        greeting = check_greeting(question)
        if greeting:
            return jsonify({'answer': greeting})
        
        for q in questions_database:
            if q.get('question') == question:
                return jsonify({'answer': q.get('answer', 'Answer not found')})
        
        return jsonify({'answer': 'I am not able to identify your question. Please try selecting from suggested questions.'})
    except Exception:
        return jsonify({'answer': 'Error processing request'})

@app.route('/api/save-user-location', methods=['POST'])
def save_user_location():
    try:
        data = request.json
        state = data.get('state')
        district = data.get('district')
        area = data.get('area')
        
        hospitals = None
        if state in hospitals_database and district in hospitals_database[state]:
            hospitals = hospitals_database[state][district]
            if isinstance(hospitals, dict):
                hospitals = [hospitals]
        
        if not hospitals:
            return jsonify({"success": False, "message": "No hospital found for this location"}), 404
        
        return jsonify({"success": True, "hospital": hospitals, "message": "Location saved successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/emergency-alert', methods=['POST'])
def emergency_alert():
    try:
        data = request.json
        location = data.get('location', {})
        
        state = location.get('state')
        district = location.get('district')
        area = location.get('area')
        
        if state not in hospitals_database or district not in hospitals_database[state]:
            return jsonify({"success": False, "message": "No hospitals configured"}), 404
        
        hospitals = hospitals_database[state][district]
        primary = hospitals[0]
        
        ref_id = f"EMG{random.randint(10000, 99999)}"
        
        email_result = send_emergency_email(primary['email'], primary['hospital'], {'state': state, 'district': district, 'area': area})
        sms_result = send_emergency_sms(primary['phone'], primary['hospital'], {'state': state, 'district': district, 'area': area})
        
        return jsonify({
            "success": True,
            "reference_id": ref_id,
            "hospital_name": primary['hospital'],
            "hospital_phone": primary['phone'],
            "hospital_email": primary['email'],
            "message": "Emergency alert sent successfully",
            "email_status": email_result['status'],
            "sms_status": sms_result['status']
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/test', methods=['GET'])
def test():
    return jsonify({
        'status': 'Backend working!',
        'total_questions': len(questions_database),
        'greetings': len(greetings_database),
        'hospitals': len(hospitals_database),
        'developer': 'ZERODAYCODERS',
        'project': 'NEUROBUDDYY.AI'
    })

if __name__ == '__main__':
    app.run()
