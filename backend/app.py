from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import random
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests


app = Flask(__name__)
CORS(app)


# ========================================
# EMAIL & SMS CONFIGURATION (SETUP REQUIRED)
# ========================================

# Gmail Configuration - YOUR EMAIL (Developer's Gmail)
# This is YOUR system email that will send alerts to hospitals
GMAIL_SENDER = "ariyanabedin00@gmail.com"  # ← Replace with YOUR Gmail
GMAIL_APP_PASSWORD = "lfii ikdv hchl frmb"  # ← Replace with 16-digit App Password

# Fast2SMS Configuration (OPTIONAL - For SMS)
# Get FREE ₹50 credit at [https://www.fast2sms.com](https://www.fast2sms.com)
FAST2SMS_API_KEY = "YOUR_API_KEY_HERE"  # ← Replace if you want SMS feature
ENABLE_SMS = False  # Set to True if you configured Fast2SMS

# ========== HOSPITAL DATABASE (DEMO DATA) ==========
hospitals_database = {
    "Delhi": {
        "South Delhi": {
            "hospital": "AIIMS Delhi",
            "email": "demo.aiims@example.com",  # DEMO EMAIL
            "phone": "+919999999991",  # DEMO PHONE
            "distance": "5 km"
        },
        "Central Delhi": {
            "hospital": "Ram Manohar Lohia Hospital",
            "email": "demo.rml@example.com",  # DEMO EMAIL
            "phone": "+919999999992",  # DEMO PHONE
            "distance": "3 km"
        }
    },
    # ... [ALL YOUR HOSPITAL DATA - KEEPING EXACTLY AS IS]
    "Maharashtra": {
        "Mumbai City": [
            {
                "hospital": "KEM Hospital Mumbai",
                "email": "demo.kem@example.com",
                "phone": "+919999999991",
                "distance": "5 km",
                "coordinates":{
                    "lat":19.002473974696805, 
                    "lng":72.84148838080044
                }
            },
            # ... rest of your hospitals
        ]
    },
    # ... [KEEPING ALL YOUR ASSAM HOSPITAL DATA EXACTLY AS IS]
}

# ========== EMAIL SENDING FUNCTION ==========
def send_emergency_email(hospital_email, hospital_name, patient_location):
    """Send emergency alert email using Gmail SMTP"""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_SENDER
        msg['To'] = hospital_email
        msg['Subject'] = '🚨 [DEMO] NEURO EMERGENCY ALERT - NEUROBUDDYY.AI'
        
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .warning {{ background: #fff3cd; padding: 15px; border-left: 5px solid #ffc107; margin-bottom: 20px; }}
                .alert {{ background: #fee; padding: 20px; border-left: 5px solid #dc2626; }}
                .info {{ background: #f0f4f8; padding: 15px; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <div class="warning">
                <h3>⚠️ DEMO PROJECT ALERT</h3>
                <p>This is an educational/college project by <strong>ZERO DAY CODERS</strong>.</p>
                <p>All hospital data and alerts are simulated for demonstration purposes.</p>
            </div>
            
            <div class="alert">
                <h2 style="color: #dc2626; margin-top: 0;">🚨 NEUROLOGICAL EMERGENCY ALERT</h2>
                
                <h3>Hospital:</h3>
                <p style="font-size: 1.1rem; color: #2563eb;"><strong>{hospital_name}</strong></p>
                
                <h3>📍 Patient Location:</h3>
                <div class="info">
                    <p><strong>State:</strong> {patient_location['state']}</p>
                    <p><strong>District:</strong> {patient_location['district']}</p>
                    <p><strong>Area:</strong> {patient_location['area']}</p>
                </div>
                
                <h3>🕒 Alert Time:</h3>
                <p>{datetime.now().strftime('%d %B %Y, %I:%M:%S %p')}</p>
                
                <h3>⚡ Action Required:</h3>
                <p style="color: #dc2626; font-weight: bold; font-size: 1.1rem;">
                    IMMEDIATE NEUROLOGICAL ASSISTANCE NEEDED
                </p>
            </div>
            
            <hr style="margin: 30px 0;">
            
            <p style="color: #666; font-size: 0.9rem;">
                <em>This is an automated alert from <strong>NEUROBUDDYY.AI Emergency System</strong></em><br>
                <em>Developed by: ZERO DAY CODERS</em><br>
                <em>Project Type: Educational/College Demo</em>
            </p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print(f"  ✅ Email sent successfully to {hospital_email}")
        return {'status': 'success', 'message': 'Email sent successfully'}
    
    except Exception as e:
        print(f"  ❌ Email error: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


# ========== SMS SENDING FUNCTION (OPTIONAL) ==========
def send_emergency_sms(phone_number, hospital_name, patient_location):
    """Send emergency SMS using Fast2SMS API (Optional)"""
    if not ENABLE_SMS or FAST2SMS_API_KEY == "YOUR_API_KEY_HERE":
        print(f"  ⏭️ SMS skipped (not configured)")
        return {'status': 'skipped', 'message': 'SMS not configured'}
    
    try:
        message = f"🚨 DEMO ALERT: Patient at {patient_location['area']}, {patient_location['district']}, {patient_location['state']}. Neuro emergency. [NEUROBUDDYY.AI Demo Project]"
        
        url = "https://www.fast2sms.com/dev/bulkV2"
        
        payload = {
            'sender_id': 'FSTSMS',
            'message': message,
            'route': 'q',
            'numbers': phone_number.replace('+91', '').replace('+', ''),
            'language': 'english'
        }
        
        headers = {
            'authorization': FAST2SMS_API_KEY,
            'Content-Type': "application/x-www-form-urlencoded",
            'Cache-Control': "no-cache"
        }
        
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        result = response.json()
        
        if result.get('return'):
            print(f"  ✅ SMS sent successfully to {phone_number}")
            return {'status': 'success', 'response': result}
        else:
            print(f"  ❌ SMS failed: {result}")
            return {'status': 'failed', 'error': result}
    
    except Exception as e:
        print(f"  ❌ SMS error: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


# ========== SAVE USER LOCATION (WITH /api/ PREFIX) ==========
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
        
        if not hospitals:
            return jsonify({
                "success": False,
                "message": "No hospital found for this location"
            }), 404
        
        print(f"\n✅ Location Saved:")
        print(f"   State: {state}")
        print(f"   District: {district}")
        print(f"   Area: {area}")
        print(f"   Total Hospitals: {len(hospitals)}")
        print(f"   Primary Hospital: {hospitals[0]['hospital']}")
        
        return jsonify({
            "success": True,
            "hospital": hospitals,
            "message": "Location saved successfully"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ========== EMERGENCY ALERT (WITH /api/ PREFIX) ==========
@app.route('/api/emergency-alert', methods=['POST'])
def emergency_alert():
    try:
        data = request.json
        location = data.get('location')
        
        state = location.get('state')
        district = location.get('district')
        area = location.get('area')
        
        print(f"\n{'='*70}")
        print(f"🚨 EMERGENCY ALERT RECEIVED!")
        print(f"{'='*70}")
        print(f"User Location: {area}, {district}, {state}")
        
        if state not in hospitals_database or district not in hospitals_database[state]:
            return jsonify({
                "success": False,
                "message": f"No hospitals configured for {district}, {state}"
            }), 404
        
        hospitals = hospitals_database[state][district]
        primary_hospital = hospitals[0]
        
        print(f"\n✅ SENDING ALERT TO PRIMARY HOSPITAL:")
        print(f"   Name: {primary_hospital['hospital']}")
        print(f"   Email: {primary_hospital['email']}")
        print(f"   Phone: {primary_hospital['phone']}")
        print(f"{'='*70}\n")
        
        reference_id = f"EMG{random.randint(10000, 99999)}"
        
        email_result = send_emergency_email(
            hospital_email=primary_hospital['email'],
            hospital_name=primary_hospital['hospital'],
            patient_location={'state': state, 'district': district, 'area': area}
        )
        
        sms_result = send_emergency_sms(
            phone_number=primary_hospital['phone'],
            hospital_name=primary_hospital['hospital'],
            patient_location={'state': state, 'district': district, 'area': area}
        )
        
        print(f"✅ ALERT SENT TO: {primary_hospital['hospital']}")
        
        return jsonify({
            "success": True,
            "reference_id": reference_id,
            "hospital_name": primary_hospital['hospital'],
            "hospital_phone": primary_hospital['phone'],
            "hospital_email": primary_hospital['email'],
            "message": "Emergency alert sent successfully",
            "email_status": email_result['status'],
            "sms_status": sms_result['status']
        })
        
    except Exception as e:
        print(f"❌ Emergency Alert Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ========== LOAD QUESTIONS ==========
def load_greetings():
    try:
        with open('data/greetings.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data['greetings']
    except Exception as e:
        print(f"✗ Error loading greetings.json: {e}")
        return []


def load_questions():
    all_questions = []
    files = ['category1_questions.json', 'category2_questions.json',
             'category3_questions.json', 'category4_questions.json']
    
    for file in files:
        try:
            with open(f'data/{file}', 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_questions.extend(data['questions'])
            print(f"✓ Loaded {file}")
        except Exception as e:
            print(f"✗ Error loading {file}: {e}")
    
    return all_questions


greetings_database = load_greetings()
questions_database = load_questions()

print(f"\n🎉 Total {len(questions_database)} questions loaded successfully!")
print(f"💬 Total {len(greetings_database)} greeting groups loaded!\n")


def check_greeting(user_input):
    user_input_clean = user_input.lower().strip().replace('?', '').replace('!', '').replace('.', '').replace(',', '')
    for greeting in greetings_database:
        for pattern in greeting['patterns']:
            if user_input_clean == pattern or pattern in user_input_clean or user_input_clean in pattern:
                return greeting['response']
    return None


# ========== GET SUGGESTIONS (WITH /api/ PREFIX) ✅ NEW ==========
@app.route('/api/get-suggestions', methods=['POST'])
def get_suggestions():
    try:
        user_input = request.json['text'].lower().strip()

        # Check greeting
        greeting_response = check_greeting(user_input)
        if greeting_response:
            return jsonify({'suggestions': []})

        # Split into words for matching
        search_words = user_input.split()
        
        # Find questions containing ALL search words
        matching = []
        
        for q in questions_database:
            question_lower = q['question'].lower()
            
            # Check if ALL words are in the question
            if all(word in question_lower for word in search_words):
                matching.append(q['question'])
            
            # Stop at 5 suggestions
            if len(matching) >= 5:
                break
        
        # Sort by length (shorter questions usually more direct)
        matching.sort(key=len)
        
        # Return top 10
        top_10 = matching[:10]
        
        print(f"User: '{user_input}' | Words: {search_words} | Found: {len(matching)} | Showing: {len(top_10)}")
        
        return jsonify({'suggestions': top_10})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'suggestions': []})


# ========== GET ANSWER (WITH /api/ PREFIX) ✅ UPDATED ==========
@app.route('/api/get-answer', methods=['POST'])
def get_answer():
    try:
        selected_question = request.json['question']
        
        greeting_response = check_greeting(selected_question)
        if greeting_response:
            print(f"✓ Greeting detected: {selected_question}")
            return jsonify({'answer': greeting_response})
        
        for q in questions_database:
            if q['question'] == selected_question:
                print(f"✓ Found answer for: {selected_question}")
                return jsonify({'answer': q['answer']})
        
        print(f"✗ No answer found for: {selected_question}")
        return jsonify({'answer': 'I am not able to identify your question. Please try selecting from the suggested questions or ask about health issues, neurology, or brain-related problems.'})
    
    except Exception as e:
        print(f"Error in get-answer: {e}")
        return jsonify({'answer': 'Error processing request'})


# ========== TEST/HEALTH CHECK ==========
@app.route('/', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def test():
    total_patterns = sum(len(g['patterns']) for g in greetings_database)
    return jsonify({
        'status': 'Backend is working!',
        'total_questions': len(questions_database),
        'greeting_groups': len(greetings_database),
        'total_greeting_patterns': total_patterns,
        'developer': 'ZERO DAY CODERS',
        'project': 'NEUROBUDDYY.AI',
        'emergency_system': 'Active',
        'email_configured': GMAIL_SENDER != "your_email@gmail.com",
        'sms_enabled': ENABLE_SMS
    })


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 NEUROBUDDYY.AI BACKEND SERVER - ZERO DAY CODERS")
    print("="*70)
    print("📍 Server: http://127.0.0.1:5000")
    print("🤖 Chatbot: Active")
    print("🚨 Emergency System: Active")
    print(f"📧 Email: {'Configured ✅' if GMAIL_SENDER != 'your_email@gmail.com' else 'Not Configured ⚠️'}")
    print(f"📱 SMS: {'Enabled ✅' if ENABLE_SMS else 'Disabled (Optional)'}")
    print("="*70 + "\n")
    app.run(debug=True, port=5000, host='127.0.0.1')
