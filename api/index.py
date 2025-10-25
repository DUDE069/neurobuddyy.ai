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
@app.route('/')
def home():
    from flask import Response
    import os
    
    # Try ALL possible paths where Vercel might store the file
    possible_paths = [
        '/var/task/frontend/index.html',  # Vercel Lambda path
        'frontend/index.html',  # Relative path
        '../frontend/index.html',  # Parent directory
        os.path.join(os.path.dirname(__file__), '..', 'frontend', 'index.html'),  # Calculated path
        '/var/task/src/frontend/index.html',  # Another possible Vercel path
        './frontend/index.html',  # Current directory
    ]
    
    html_content = None
    found_path = None
    
    for file_path in possible_paths:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                    found_path = file_path
                    break
        except Exception:
            continue
    
    if html_content:
        return Response(html_content, mimetype='text/html')
    else:
        # Debug message showing what paths were tried
        return Response(f"Frontend file not found. Tried paths: {', '.join(possible_paths)}", status=404)




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


# ========== HOSPITAL DATABASE ==========
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
            },
            {
                "hospital": "Lilavati Hospital Mumbai",
                "email": "demo.lilavati@example.com",
                "phone": "+919999999992",
                "distance": "7 km",
                "coordinates": {
                    "lat": 19.0596,
                    "lng": 72.8295
                }
            },
            {
                "hospital": "Hinduja Hospital Mumbai",
                "email": "demo.hinduja@example.com",
                "phone": "+919999999993",
                "distance": "10 km",
                "coordinates": {
                    "lat": 19.0522,
                    "lng": 72.8346
                }
            },
            {
                "hospital": "Bombay Hospital Mumbai",
                "email": "demo.bombay@example.com",
                "phone": "+919999999994",
                "distance": "12 km"
            },
            {
                "hospital": "Jaslok Hospital Mumbai",
                "email": "demo.jaslok@example.com",
                "phone": "+919999999995",
                "distance": "15 km"
            }
        ],
        "Pune": [
            {
                "hospital": "Ruby Hall Clinic Pune",
                "email": "demo.ruby@example.com",
                "phone": "+919999999996",
                "distance": "5 km"
            },
            {
                "hospital": "Jehangir Hospital Pune",
                "email": "demo.jehangir@example.com",
                "phone": "+919999999997",
                "distance": "6 km"
            }
        ]
    },
    "Karnataka": {
        "Bangalore": [
            {
                "hospital": "NIMHANS Bangalore",
                "email": "demo.nimhans@example.com",
                "phone": "+919999999998",
                "distance": "6 km"
            },
            {
                "hospital": "Manipal Hospital Bangalore",
                "email": "demo.manipal@example.com",
                "phone": "+919999999999",
                "distance": "8 km"
            },
            {
                "hospital": "Apollo Hospital Bangalore",
                "email": "demo.apollo@example.com",
                "phone": "+919999999991",
                "distance": "10 km"
            }
        ]
    },
    "Assam": {
        "Guwahati": [
            {
                "hospital": "GNRC Hospital Dispur - Neuroscience Department",
                "email": "info@gnrchospitals.com",
                "phone": "+91-1800-345-0022",
                "distance": "5 km",
                "coordinates": {
                    "lat": 26.1393220976546,
                    "lng": 91.79459993962551
                }
            },
            {
                "hospital": "Narayana Superspeciality Hospital - Neurology & Neurosurgery",
                "email": "info.guw@narayanahealth.org",
                "phone": "+91-361-2680321",
                "distance": "8 km",
                "coordinates": {
                    "lat": 26.207774,
                    "lng": 91.677652
                }
            },
            {
                "hospital": "Down Town Hospital - Neurology Department",
                "email": "dth@downtowngroup.org",
                "phone": "+91-9854074073",
                "distance": "7 km",
                "coordinates": {
                    "lat": 26.13866,
                    "lng": 91.79986
                }
            }
        ],
        "Kamrup Metropolitan": [
            {
                "hospital": "GNRC Sixmile - Neuro-Science Center",
                "email": "info@gnrchospitals.com",
                "phone": "+91-1800-345-0011",
                "distance": "6 km",
                "coordinates": {
                    "lat": 26.131309412128402,
                    "lng": 91.80778967118864
                }
            },
            {
                "hospital": "Marwari Hospitals - Neurology Department",
                "email": "info@marwarihospitals.com",
                "phone": "+91-7099066004",
                "distance": "9 km",
                "coordinates": {
                    "lat": 26.1730,
                    "lng": 91.7514
                }
            }
        ],
        "Dibrugarh": [
            {
                "hospital": "Assam Medical College - Neurology Department",
                "email": "viceprincipalamch@gmail.com",
                "phone": "+91-373-2300080",
                "distance": "4 km",
                "coordinates": {
                    "lat": 27.4886,
                    "lng": 94.9139
                }
            },
            {
                "hospital": "Srimanta Sankardeva Hospital - Neurology & Neurosurgery",
                "email": "info@sankardevahospital.com",
                "phone": "+91-9365881431",
                "distance": "8 km",
                "coordinates": {
                    "lat": 27.4728,
                    "lng": 94.9120
                }
            }
        ],
        "Cachar": [
            {
                "hospital": "Silchar Medical College - Neurology Department",
                "email": "smch.cachar@gov.in",
                "phone": "+91-3842-231469",
                "distance": "5 km",
                "coordinates": {
                    "lat": 24.7758,
                    "lng": 92.7947
                }
            },
            {
                "hospital": "Narayana Hospital Silchar - Neurology Unit",
                "email": "info.silchar@narayanahealth.org",
                "phone": "+91-3842-263000",
                "distance": "9 km",
                "coordinates": {
                    "lat": 24.8200,
                    "lng": 92.8050
                }
            }
        ],
        "Jorhat": [
            {
                "hospital": "Jorhat Medical College - Neurology Department",
                "email": "jmc-asm@nic.in",
                "phone": "+91-376-2935370",
                "distance": "6 km",
                "coordinates": {
                    "lat": 26.7421,
                    "lng": 94.1960
                }
            },
            {
                "hospital": "Apeksha Hospital Jorhat - Neurology Center",
                "email": "info@apekshahospital.com",
                "phone": "+91-376-2371234",
                "distance": "10 km",
                "coordinates": {
                    "lat": 26.7500,
                    "lng": 94.2100
                }
            }
        ],
        "Sonitpur": [
            {
                "hospital": "Tezpur Medical College - Neurology Department",
                "email": "tmctezpur@gmail.com",
                "phone": "+91-3712-241305",
                "distance": "7 km",
                "coordinates": {
                    "lat": 26.6803,
                    "lng": 92.6533
                }
            },
            {
                "hospital": "Times Hospital Tezpur - Neuro Care Unit",
                "email": "info@timeshospital.in",
                "phone": "+91-3712-225678",
                "distance": "12 km",
                "coordinates": {
                    "lat": 26.6339,
                    "lng": 92.8000
                }
            }
        ],
        "Nagaon": [
            {
                "hospital": "Bhogeswari Phukanani Civil Hospital - Neurology",
                "email": "bpch.nagaon@gov.in",
                "phone": "+91-3672-232000",
                "distance": "5 km",
                "coordinates": {
                    "lat": 26.3476,
                    "lng": 92.6839
                }
            },
            {
                "hospital": "Nidan Hospital Nagaon - Neuro Clinic",
                "email": "info@nidanhospital.com",
                "phone": "+91-6026026020",
                "distance": "8 km",
                "coordinates": {
                    "lat": 26.3450,
                    "lng": 92.6900
                }
            }
        ],
        "Bongaigaon": [
            {
                "hospital": "Bongaigaon Civil Hospital - Neurology Unit",
                "email": "civilhosp.bongaigaon@gov.in",
                "phone": "+91-3664-221234",
                "distance": "6 km",
                "coordinates": {
                    "lat": 26.4830,
                    "lng": 90.5572
                }
            },
            {
                "hospital": "Lower Assam Hospital - Neuro Center",
                "email": "info@lowerassamhospital.com",
                "phone": "+91-3664-222345",
                "distance": "9 km",
                "coordinates": {
                    "lat": 26.4765,
                    "lng": 90.5630
                }
            }
        ],
        "Tinsukia": [
            {
                "hospital": "Tinsukia Civil Hospital - Neurology Department",
                "email": "civilhosp.tinsukia@gov.in",
                "phone": "+91-3742-331000",
                "distance": "7 km",
                "coordinates": {
                    "lat": 27.4900,
                    "lng": 95.3597
                }
            },
            {
                "hospital": "Aditya Hospital Tinsukia - Neuro Care",
                "email": "info@adityahospital.org",
                "phone": "+91-3742-332111",
                "distance": "11 km",
                "coordinates": {
                    "lat": 27.4850,
                    "lng": 95.3650
                }
            }
        ],
        "Golaghat": [
            {
                "hospital": "Golaghat Civil Hospital - Neurology",
                "email": "civilhosp.golaghat@gov.in",
                "phone": "+91-3774-270123",
                "distance": "5 km",
                "coordinates": {
                    "lat": 26.5214,
                    "lng": 93.9620
                }
            },
            {
                "hospital": "Golaghat District Hospital - Neuro Unit",
                "email": "districth.golaghat@gov.in",
                "phone": "+91-3774-271234",
                "distance": "8 km",
                "coordinates": {
                    "lat": 26.5180,
                    "lng": 93.9700
                }
            }
        ],
        "Sivasagar": [
            {
                "hospital": "Sivasagar Civil Hospital - Neurology Department",
                "email": "civilhosp.sivasagar@gov.in",
                "phone": "+91-3772-220345",
                "distance": "6 km",
                "coordinates": {
                    "lat": 26.9845,
                    "lng": 94.6394
                }
            },
            {
                "hospital": "Sivasagar District Hospital - Neuro Clinic",
                "email": "districth.sivasagar@gov.in",
                "phone": "+91-3772-221456",
                "distance": "10 km",
                "coordinates": {
                    "lat": 26.9800,
                    "lng": 94.6450
                }
            }
        ],
        "Dhemaji": [
            {
                "hospital": "Dhemaji Civil Hospital - Neurology Unit",
                "email": "civilhosp.dhemaji@gov.in",
                "phone": "+91-3753-240123",
                "distance": "5 km",
                "coordinates": {
                    "lat": 27.4728,
                    "lng": 94.5795
                }
            },
            {
                "hospital": "Dhemaji District Hospital - Neuro Care",
                "email": "districth.dhemaji@gov.in",
                "phone": "+91-3753-241234",
                "distance": "9 km",
                "coordinates": {
                    "lat": 27.4680,
                    "lng": 94.5850
                }
            }
        ],
        "Lakhimpur": [
            {
                "hospital": "North Lakhimpur Civil Hospital - Neurology",
                "email": "civilhosp.lakhimpur@gov.in",
                "phone": "+91-3752-262345",
                "distance": "6 km",
                "coordinates": {
                    "lat": 27.2360,
                    "lng": 94.1038
                }
            },
            {
                "hospital": "Lakhimpur District Hospital - Neuro Department",
                "email": "districth.lakhimpur@gov.in",
                "phone": "+91-3752-263456",
                "distance": "11 km",
                "coordinates": {
                    "lat": 27.2320,
                    "lng": 94.1100
                }
            }
        ],
        "Darrang": [
            {
                "hospital": "Mangaldai Civil Hospital - Neurology Unit",
                "email": "civilhosp.mangaldai@gov.in",
                "phone": "+91-3713-260123",
                "distance": "7 km",
                "coordinates": {
                    "lat": 26.4421,
                    "lng": 92.0298
                }
            },
            {
                "hospital": "Darrang District Hospital - Neuro Center",
                "email": "districth.darrang@gov.in",
                "phone": "+91-3713-261234",
                "distance": "10 km",
                "coordinates": {
                    "lat": 26.4380,
                    "lng": 92.0350
                }
            }
        ],
        "Barpeta": [
            {
                "hospital": "Barpeta Civil Hospital - Neurology Department",
                "email": "civilhosp.barpeta@gov.in",
                "phone": "+91-3665-232123",
                "distance": "6 km",
                "coordinates": {
                    "lat": 26.3231,
                    "lng": 90.9668
                }
            },
            {
                "hospital": "Barpeta District Hospital - Neuro Care",
                "email": "districth.barpeta@gov.in",
                "phone": "+91-3665-233234",
                "distance": "9 km",
                "coordinates": {
                    "lat": 26.3200,
                    "lng": 90.9720
                }
            }
        ],
        "Kokrajhar": [
            {
                "hospital": "Kokrajhar Civil Hospital - Neurology Unit",
                "email": "civilhosp.kokrajhar@gov.in",
                "phone": "+91-3661-272123",
                "distance": "5 km",
                "coordinates": {
                    "lat": 26.4012,
                    "lng": 90.2715
                }
            },
            {
                "hospital": "Kokrajhar District Hospital - Neuro Department",
                "email": "districth.kokrajhar@gov.in",
                "phone": "+91-3661-273234",
                "distance": "8 km",
                "coordinates": {
                    "lat": 26.3980,
                    "lng": 90.2780
                }
            }
        ],
        "Dhubri": [
            {
                "hospital": "Dhubri Civil Hospital - Neurology",
                "email": "civilhosp.dhubri@gov.in",
                "phone": "+91-3662-230345",
                "distance": "6 km",
                "coordinates": {
                    "lat": 26.0196,
                    "lng": 89.9864
                }
            },
            {
                "hospital": "Dhubri District Hospital - Neuro Clinic",
                "email": "districth.dhubri@gov.in",
                "phone": "+91-3662-231456",
                "distance": "10 km",
                "coordinates": {
                    "lat": 26.0150,
                    "lng": 89.9920
                }
            }
        ],
        "Goalpara": [
            {
                "hospital": "Goalpara Civil Hospital - Neurology Department",
                "email": "civilhosp.goalpara@gov.in",
                "phone": "+91-3663-262123",
                "distance": "7 km",
                "coordinates": {
                    "lat": 26.14247,
                    "lng": 90.61006
                }
            }
        ],
        "Hailakandi": [
            {
                "hospital": "Hailakandi Civil Hospital - Neurology",
                "email": "civilhosp.hailakandi@gov.in",
                "phone": "+91-3844-262345",
                "distance": "5 km",
                "coordinates": {
                    "lat": 24.6858,
                    "lng": 92.5625
                }
            },
            {
                "hospital": "Hailakandi District Hospital - Neuro Care",
                "email": "districth.hailakandi@gov.in",
                "phone": "+91-3844-263456",
                "distance": "9 km",
                "coordinates": {
                    "lat": 24.6820,
                    "lng": 92.5680
                }
            }
        ],
        "Karimganj": [
            {
                "hospital": "Karimganj Civil Hospital - Neurology Unit",
                "email": "civilhosp.karimganj@gov.in",
                "phone": "+91-3843-262123",
                "distance": "6 km",
                "coordinates": {
                    "lat": 24.8697,
                    "lng": 92.3573
                }
            },
            {
                "hospital": "Karimganj District Hospital - Neuro Department",
                "email": "districth.karimganj@gov.in",
                "phone": "+91-3843-263234",
                "distance": "10 km",
                "coordinates": {
                    "lat": 24.8650,
                    "lng": 92.3630
                }
            }
        ],
        "Nalbari": [
            {
                "hospital": "Nalbari Civil Hospital - Neurology",
                "email": "civilhosp.nalbari@gov.in",
                "phone": "+91-3624-220123",
                "distance": "7 km",
                "coordinates": {
                    "lat": 26.4463,
                    "lng": 91.4346
                }
            },
            {
                "hospital": "Nalbari District Hospital - Neuro Clinic",
                "email": "districth.nalbari@gov.in",
                "phone": "+91-3624-221234",
                "distance": "11 km",
                "coordinates": {
                    "lat": 26.4420,
                    "lng": 91.4400
                }
            }
        ],
        "Morigaon": [
            {
                "hospital": "Morigaon Civil Hospital - Neurology Department",
                "email": "civilhosp.morigaon@gov.in",
                "phone": "+91-3678-252123",
                "distance": "6 km",
                "coordinates": {
                    "lat": 26.2524,
                    "lng": 92.3424
                }
            },
            {
                "hospital": "Morigaon District Hospital - Neuro Unit",
                "email": "districth.morigaon@gov.in",
                "phone": "+91-3678-253234",
                "distance": "9 km",
                "coordinates": {
                    "lat": 26.2480,
                    "lng": 92.3480
                }
            }
        ],
        "Hojai": [
            {
                "hospital": "Hojai Civil Hospital - Neurology",
                "email": "civilhosp.hojai@gov.in",
                "phone": "+91-3674-240123",
                "distance": "5 km",
                "coordinates": {
                    "lat": 26.0046,
                    "lng": 92.8569
                }
            },
            {
                "hospital": "Hojai District Hospital - Neuro Care",
                "email": "districth.hojai@gov.in",
                "phone": "+91-3674-241234",
                "distance": "8 km",
                "coordinates": {
                    "lat": 26.0000,
                    "lng": 92.8620
                }
            }
        ],
        "Biswanath": [
            {
                "hospital": "Biswanath Civil Hospital - Neurology Unit",
                "email": "civilhosp.biswanath@gov.in",
                "phone": "+91-3712-282123",
                "distance": "6 km",
                "coordinates": {
                    "lat": 26.7400,
                    "lng": 93.1500
                }
            },
            {
                "hospital": "Biswanath District Hospital - Neuro Department",
                "email": "districth.biswanath@gov.in",
                "phone": "+91-3712-283234",
                "distance": "10 km",
                "coordinates": {
                    "lat": 26.7350,
                    "lng": 93.1560
                }
            }
        ],
        "Charaideo": [
            {
                "hospital": "Charaideo Civil Hospital - Neurology",
                "email": "civilhosp.charaideo@gov.in",
                "phone": "+91-3772-250123",
                "distance": "7 km",
                "coordinates": {
                    "lat": 26.9250,
                    "lng": 94.8000
                }
            },
            {
                "hospital": "Charaideo District Hospital - Neuro Clinic",
                "email": "districth.charaideo@gov.in",
                "phone": "+91-3772-251234",
                "distance": "11 km",
                "coordinates": {
                    "lat": 26.9200,
                    "lng": 94.8060
                }
            }
        ],
        "Chirang": [
            {
                "hospital": "Chirang Civil Hospital - Neurology Department",
                "email": "civilhosp.chirang@gov.in",
                "phone": "+91-3663-282123",
                "distance": "5 km",
                "coordinates": {
                    "lat": 26.5230,
                    "lng": 90.4570
                }
            },
            {
                "hospital": "Chirang District Hospital - Neuro Unit",
                "email": "districth.chirang@gov.in",
                "phone": "+91-3663-283234",
                "distance": "9 km",
                "coordinates": {
                    "lat": 26.5180,
                    "lng": 90.4630
                }
            }
        ],
        "Dima Hasao": [
            {
                "hospital": "Dima Hasao Civil Hospital - Neurology",
                "email": "civilhosp.dimahasao@gov.in",
                "phone": "+91-3673-232123",
                "distance": "6 km",
                "coordinates": {
                    "lat": 25.4500,
                    "lng": 93.0200
                }
            },
            {
                "hospital": "Dima Hasao District Hospital - Neuro Care",
                "email": "districth.dimahasao@gov.in",
                "phone": "+91-3673-233234",
                "distance": "10 km",
                "coordinates": {
                    "lat": 25.4450,
                    "lng": 93.0260
                }
            }
        ],
        "Karbi Anglong": [
            {
                "hospital": "Karbi Anglong Civil Hospital - Neurology Unit",
                "email": "civilhosp.karbianglong@gov.in",
                "phone": "+91-3671-270123",
                "distance": "7 km",
                "coordinates": {
                    "lat": 26.0100,
                    "lng": 93.4400
                }
            },
            {
                "hospital": "Karbi Anglong District Hospital - Neuro Department",
                "email": "districth.karbianglong@gov.in",
                "phone": "+91-3671-271234",
                "distance": "11 km",
                "coordinates": {
                    "lat": 26.0050,
                    "lng": 93.4460
                }
            }
        ],
        "West Karbi Anglong": [
            {
                "hospital": "West Karbi Anglong Civil Hospital - Neurology",
                "email": "civilhosp.westkarbi@gov.in",
                "phone": "+91-3671-240123",
                "distance": "6 km",
                "coordinates": {
                    "lat": 25.9800,
                    "lng": 92.9500
                }
            },
            {
                "hospital": "West Karbi Anglong District Hospital - Neuro Clinic",
                "email": "districth.westkarbi@gov.in",
                "phone": "+91-3671-241234",
                "distance": "9 km",
                "coordinates": {
                    "lat": 25.9750,
                    "lng": 92.9560
                }
            }
        ],
        "Majuli": [
            {
                "hospital": "Majuli Civil Hospital - Neurology Department",
                "email": "civilhosp.majuli@gov.in",
                "phone": "+91-376-2660123",
                "distance": "5 km",
                "coordinates": {
                    "lat": 26.9560,
                    "lng": 94.1638
                }
            },
            {
                "hospital": "Majuli District Hospital - Neuro Unit",
                "email": "districth.majuli@gov.in",
                "phone": "+91-376-2661234",
                "distance": "8 km",
                "coordinates": {
                    "lat": 26.9520,
                    "lng": 94.1700
                }
            }
        ],
        "Udalguri": [
            {
                "hospital": "Udalguri Civil Hospital - Neurology",
                "email": "civilhosp.udalguri@gov.in",
                "phone": "+91-3714-262123",
                "distance": "6 km",
                "coordinates": {
                    "lat": 26.7538,
                    "lng": 92.1025
                }
            },
            {
                "hospital": "Udalguri District Hospital - Neuro Care",
                "email": "districth.udalguri@gov.in",
                "phone": "+91-3714-263234",
                "distance": "10 km",
                "coordinates": {
                    "lat": 26.7490,
                    "lng": 92.1080
                }
            }
        ],
        "Baksa": [
            {
                "hospital": "Baksa Civil Hospital - Neurology Unit",
                "email": "civilhosp.baksa@gov.in",
                "phone": "+91-3624-280123",
                "distance": "7 km",
                "coordinates": {
                    "lat": 26.6340,
                    "lng": 91.0820
                }
            },
            {
                "hospital": "Baksa District Hospital - Neuro Department",
                "email": "districth.baksa@gov.in",
                "phone": "+91-3624-281234",
                "distance": "11 km",
                "coordinates": {
                    "lat": 26.6290,
                    "lng": 91.0880
                }
            }
        ],
        "Kamrup": [
            {
                "hospital": "Kamrup Civil Hospital - Neurology",
                "email": "civilhosp.kamrup@gov.in",
                "phone": "+91-361-2260123",
                "distance": "8 km",
                "coordinates": {
                    "lat": 26.1158,
                    "lng": 91.7086
                }
            },
            {
                "hospital": "Kamrup District Hospital - Neuro Clinic",
                "email": "districth.kamrup@gov.in",
                "phone": "+91-361-2261234",
                "distance": "12 km",
                "coordinates": {
                    "lat": 26.1110,
                    "lng": 91.7150
                }
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
@app.route('/api/get-suggestions', methods=['POST'])
def get_suggestions():
    try:
        user_input = request.json['text'].lower().strip()

        # Check greeting - don't suggest for greetings
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
                
                # Stop once we have 10 suggestions
                if len(matching) >= 10:
                    break
        
        # If no matches found, try partial matching (any word)
        if not matching:
            for q in questions_database:
                question_lower = q['question'].lower()
                
                # Check if ANY word is in the question
                if any(word in question_lower for word in search_words):
                    matching.append(q['question'])
                    
                    if len(matching) >= 10:
                        break
        
        # Sort by length (shorter questions first)
        matching.sort(key=len)
        
        # Return top 10
        top_10 = matching[:10]
        
        return jsonify({'suggestions': top_10})

    except Exception as e:
        print(f"❌ Error in suggestions: {e}")
        return jsonify({'suggestions': []})


@app.route('/api/get-answer', methods=['POST'])
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
            
            # Convert dict to list if needed
            if isinstance(hospitals, dict):
                hospitals = [hospitals]
        
        if not hospitals:
            return jsonify({
                "success": False,
                "message": "No hospital found for this location"
            }), 404
        
        return jsonify({
            "success": True,
            "hospital": hospitals,
            "message": "Location saved successfully"
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/emergency-alert', methods=['POST'])
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
