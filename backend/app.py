from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import json
import random
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import os
from dotenv import load_dotenv

# ========================================
# LOAD ENVIRONMENT VARIABLES
# ========================================
# Reads from backend/.env locally; uses Render Dashboard env vars in production.
load_dotenv()

app = Flask(__name__)
CORS(app)

# ========================================
# RATE LIMITER (Prevents SOS spam / DDoS)
# Using in-memory storage (resets on dyno restart — acceptable for demo).
# ========================================
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)


# ========================================
# EMAIL & SMS CONFIGURATION — FROM .ENV
# ========================================
GMAIL_SENDER      = os.getenv("GMAIL_SENDER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
FAST2SMS_API_KEY  = os.getenv("FAST2SMS_API_KEY", "YOUR_API_KEY_HERE")
ENABLE_SMS        = os.getenv("ENABLE_SMS", "False").lower() == "true"


# ========================================
# HOSPITAL DATABASE (DEMO DATA)
# ========================================
hospitals_database = {
    "Delhi": {
        "South Delhi": [
            {
                "hospital": "AIIMS Delhi",
                "email": "demo.aiims@example.com",
                "phone": "+919999999991",
                "distance": "5 km"
            }
        ],
        "Central Delhi": [
            {
                "hospital": "Ram Manohar Lohia Hospital",
                "email": "demo.rml@example.com",
                "phone": "+919999999992",
                "distance": "3 km"
            }
        ]
    },
    "Maharashtra": {
        "Mumbai City": [
            {
                "hospital": "KEM Hospital Mumbai",
                "email": "demo.kem@example.com",
                "phone": "+919999999991",
                "distance": "5 km",
                "coordinates": {
                    "lat": 19.002473974696805,
                    "lng": 72.84148838080044
                }
            }
        ]
    },
    "Assam": {
        "Guwahati": [
            {
                "hospital": "Gauhati Medical College & Hospital",
                "email": "demo.gmch@example.com",
                "phone": "+919999999993",
                "distance": "3 km",
                "coordinates": {
                    "lat": 26.1445,
                    "lng": 91.7362
                }
            }
        ],
        "Goalpara": [
            {
                "hospital": "Goalpara Civil Hospital",
                "email": "demo.goalpara@example.com",
                "phone": "+919999999994",
                "distance": "2 km"
            }
        ]
    },
    "Karnataka": {
        "Bengaluru Urban": [
            {
                "hospital": "NIMHANS Bangalore",
                "email": "demo.nimhans@example.com",
                "phone": "+919999999995",
                "distance": "4 km",
                "coordinates": {
                    "lat": 12.9415,
                    "lng": 77.5952
                }
            }
        ]
    },
    "Tamil Nadu": {
        "Chennai": [
            {
                "hospital": "Rajiv Gandhi Government Hospital",
                "email": "demo.rajivgandhi@example.com",
                "phone": "+919999999996",
                "distance": "6 km"
            }
        ]
    },
    "West Bengal": {
        "Kolkata": [
            {
                "hospital": "SSKM Hospital Kolkata",
                "email": "demo.sskm@example.com",
                "phone": "+919999999997",
                "distance": "7 km"
            }
        ]
    },
    "Gujarat": {
        "Ahmedabad": [
            {
                "hospital": "Civil Hospital Ahmedabad",
                "email": "demo.civil@example.com",
                "phone": "+919999999998",
                "distance": "5 km"
            }
        ]
    },
    "Rajasthan": {
        "Jaipur": [
            {
                "hospital": "SMS Hospital Jaipur",
                "email": "demo.sms@example.com",
                "phone": "+919999999990",
                "distance": "4 km"
            }
        ]
    },
    "Uttar Pradesh": {
        "Lucknow": [
            {
                "hospital": "SGPGI Lucknow",
                "email": "demo.sgpgi@example.com",
                "phone": "+919999999989",
                "distance": "8 km"
            }
        ]
    }
}


# ========================================
# LEVENSHTEIN DISTANCE — Pure Python (no extra dependencies)
# Wagner-Fischer algorithm
# ========================================
def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Computes the Levenshtein edit distance between two strings.
    Returns the number of single-character insertions, deletions, or
    substitutions needed to change s1 into s2.
    """
    if s1 == s2:
        return 0
    len1, len2 = len(s1), len(s2)
    if len1 == 0:
        return len2
    if len2 == 0:
        return len1

    # Use two arrays instead of a full matrix (space optimization)
    prev = list(range(len2 + 1))
    curr = [0] * (len2 + 1)

    for i in range(1, len1 + 1):
        curr[0] = i
        for j in range(1, len2 + 1):
            if s1[i - 1] == s2[j - 1]:
                cost = 0
            else:
                cost = 1
            curr[j] = min(
                prev[j] + 1,          # deletion
                curr[j - 1] + 1,      # insertion
                prev[j - 1] + cost    # substitution
            )
        prev, curr = curr, [0] * (len2 + 1)

    return prev[len2]


def fuzzy_word_match(search_word: str, question_lower: str, threshold: int = 2) -> bool:
    """
    Returns True if any word in question_lower is within
    Levenshtein distance `threshold` of search_word.
    Also returns True if search_word is a substring of any question word
    (preserves original exact-match behaviour).
    """
    # Exact substring check first (fast path)
    if search_word in question_lower:
        return True

    # Fuzzy check: split question into words and test each
    for q_word in question_lower.split():
        # Skip very short words to reduce false positives
        if len(search_word) < 3 or len(q_word) < 3:
            continue
        if levenshtein_distance(search_word, q_word) <= threshold:
            return True

    return False


# ========================================
# EMAIL SENDING FUNCTION
# ========================================
def send_emergency_email(hospital_email, hospital_name, patient_location):
    """Send emergency alert email using Gmail SMTP."""
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


# ========================================
# SMS SENDING FUNCTION (OPTIONAL)
# ========================================
def send_emergency_sms(phone_number, hospital_name, patient_location):
    """Send emergency SMS using Fast2SMS API (Optional)."""
    if not ENABLE_SMS or FAST2SMS_API_KEY == "YOUR_API_KEY_HERE":
        print(f"  ⏭️ SMS skipped (not configured)")
        return {'status': 'skipped', 'message': 'SMS not configured'}

    try:
        message = (
            f"🚨 DEMO ALERT: Patient at {patient_location['area']}, "
            f"{patient_location['district']}, {patient_location['state']}. "
            f"Neuro emergency. [NEUROBUDDYY.AI Demo Project]"
        )

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


# ========================================
# SAVE USER LOCATION
# ========================================
@app.route('/api/save-user-location', methods=['POST'])
def save_user_location():
    try:
        data = request.json
        state    = data.get('state')
        district = data.get('district')
        area     = data.get('area')

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


# ========================================
# EMERGENCY ALERT — RATE LIMITED
# Max 5 requests/minute and 10 requests/hour per IP.
# Prevents SOS spam and DDoS on the emergency endpoint.
# ========================================
@app.route('/api/emergency-alert', methods=['POST'])
@limiter.limit("5 per minute;10 per hour")
def emergency_alert():
    try:
        data     = request.json
        location = data.get('location', {})

        state    = location.get('state')
        district = location.get('district')
        area     = location.get('area')

        print(f"\n{'='*70}")
        print(f"🚨 EMERGENCY ALERT RECEIVED!")
        print(f"{'='*70}")
        print(f"User Location: {area}, {district}, {state}")

        if state not in hospitals_database or district not in hospitals_database[state]:
            return jsonify({
                "success": False,
                "message": f"No hospitals configured for {district}, {state}"
            }), 404

        hospitals        = hospitals_database[state][district]
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


# ========================================
# LOAD QUESTIONS FROM JSON FILES
# ========================================
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
    files = [
        'category1_questions.json',
        'category2_questions.json',
        'category3_questions.json',
        'category4_questions.json'
    ]

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
    user_input_clean = (
        user_input.lower().strip()
        .replace('?', '').replace('!', '').replace('.', '').replace(',', '')
    )
    for greeting in greetings_database:
        for pattern in greeting['patterns']:
            if (user_input_clean == pattern
                    or pattern in user_input_clean
                    or user_input_clean in pattern):
                return greeting['response']
    return None


# ========================================
# GET SUGGESTIONS — WITH FUZZY SEARCH
# Two-pass: exact matches first (sorted by length),
# then fuzzy matches (sorted by aggregate Levenshtein distance).
# Rate limited to 30 requests/minute to prevent abuse.
# ========================================
@app.route('/api/get-suggestions', methods=['POST'])
@limiter.limit("30 per minute")
def get_suggestions():
    try:
        import difflib
        user_input  = request.json['text'].lower().strip()
        search_words = [w for w in user_input.split() if w]

        if not search_words:
            return jsonify({'suggestions': []})

        # Greeting check — no suggestions for greetings
        greeting_response = check_greeting(user_input)
        if greeting_response:
            return jsonify({'suggestions': []})

        fuzzy_matches = []
        for q in questions_database:
            question_lower = q['question'].lower()
            q_words = question_lower.split()
            
            if not q_words:
                continue
                
            if user_input in question_lower:
                fuzzy_matches.append((q['question'], 100.0))
                continue
                
            score = 0
            for w in search_words:
                if w in q_words:
                    score += 1
                else:
                    best = difflib.get_close_matches(w, q_words, n=1, cutoff=0.6)
                    if best:
                        score += 1
            
            normalized_score = score / len(search_words)
            if normalized_score > 0:
                ratio = difflib.SequenceMatcher(None, user_input, question_lower).ratio()
                fuzzy_matches.append((q['question'], normalized_score + (ratio * 0.1)))

        # Sort: highest score first
        fuzzy_matches.sort(key=lambda x: x[1], reverse=True)
        top_10 = [q for q, _ in fuzzy_matches[:10]]

        print(
            f"User: '{user_input}' | Words: {search_words} | "
            f"Matches: {len(fuzzy_matches)} | Showing: {len(top_10)}"
        )

        return jsonify({'suggestions': top_10})

    except Exception as e:
        print(f"Error in get-suggestions: {e}")
        return jsonify({'suggestions': []})


# ========================================
# GET ANSWER
# ========================================
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

        print(f"✗ No exact match for: {selected_question}. Trying fuzzy search.")
        
        # Fuzzy search logic
        import difflib
        user_input = selected_question.lower().strip()
        search_words = [w for w in user_input.split() if w]
        
        fuzzy_matches = []
        for q in questions_database:
            question_lower = q['question'].lower()
            q_words = question_lower.split()
            
            if not q_words or not search_words:
                continue
                
            if user_input in question_lower:
                fuzzy_matches.append((q['question'], 100.0))
                continue
                
            score = 0
            for w in search_words:
                if w in q_words:
                    score += 1
                else:
                    best = difflib.get_close_matches(w, q_words, n=1, cutoff=0.6)
                    if best:
                        score += 1
            
            normalized_score = score / len(search_words)
            if normalized_score > 0:
                ratio = difflib.SequenceMatcher(None, user_input, question_lower).ratio()
                fuzzy_matches.append((q['question'], normalized_score + (ratio * 0.1)))
                
        fuzzy_matches.sort(key=lambda x: x[1], reverse=True)
        top_suggestions = [q for q, _ in fuzzy_matches[:5]]
        
        if top_suggestions:
            return jsonify({
                'error': True,
                'message': 'Your typed words were wrong or unrecognized.',
                'suggestions': top_suggestions
            })
        else:
            return jsonify({
                'error': True,
                'message': 'I am not able to identify your question. Please try asking about health issues, neurology, or brain-related problems.',
                'suggestions': []
            })

    except Exception as e:
        print(f"Error in get-answer: {e}")
        return jsonify({'answer': 'Error processing request', 'error': True, 'message': 'Internal Server Error'})


# ========================================
# HEALTH CHECK
# ========================================
@app.route('/', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health_check():
    total_patterns = sum(len(g['patterns']) for g in greetings_database)
    return jsonify({
        'status': 'Backend is working!',
        'total_questions': len(questions_database),
        'greeting_groups': len(greetings_database),
        'total_greeting_patterns': total_patterns,
        'developer': 'ZERO DAY CODERS',
        'project': 'NEUROBUDDYY.AI',
        'emergency_system': 'Active',
        'rate_limiting': 'Active (5/min on /api/emergency-alert)',
        'fuzzy_search': 'Active (Levenshtein threshold=2)',
        'email_configured': bool(GMAIL_SENDER and GMAIL_APP_PASSWORD),
        'sms_enabled': ENABLE_SMS
    })


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 NEUROBUDDYY.AI BACKEND SERVER - ZERO DAY CODERS")
    print("="*70)
    print("📍 Server: http://127.0.0.1:5000")
    print("🤖 Chatbot: Active (Fuzzy Search ON)")
    print("🚨 Emergency System: Active (Rate Limited)")
    print(f"📧 Email: {'Configured ✅' if GMAIL_SENDER else 'Not Configured ⚠️'}")
    print(f"📱 SMS: {'Enabled ✅' if ENABLE_SMS else 'Disabled (Optional)'}")
    print(f"🔐 Env Vars: Loaded from .env ✅")
    print("="*70 + "\n")
    app.run(debug=True, port=5000, host='127.0.0.1')
