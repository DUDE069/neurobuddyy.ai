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
        {
            "hospital": "Gauhati Medical College Hospital - Neurology Department",
            "email": "gmchassam@gmail.com",
            "phone": "+91-361-2528021",
            "distance": "5 km",
            "coordinates": {
                "lat": 26.144561,
                "lng": 91.736215
            }
        },
        {
            "hospital": "GNRC Hospital Dispur - Neuroscience Department",
            "email": "info@gnrchospitals.com",
            "phone": "+91-1800-345-0022",
            "distance": "7 km",
            "coordinates": {
                "lat": 26.143328,
                "lng": 91.789856
            }
        },
        {
            "hospital": "Down Town Hospital - Neurology Department",
            "email": "dth@downtowngroup.org",
            "phone": "+91-361-2347777",
            "distance": "8 km",
            "coordinates": {
                "lat": 26.142076,
                "lng": 91.790134
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
                "lat": 26.131309,
                "lng": 91.807789
            }
        },
        {
            "hospital": "Marwari Hospitals - Neurology Department",
            "email": "info@marwarihospitals.com",
            "phone": "+91-7099066004",
            "distance": "9 km",
            "coordinates": {
                "lat": 26.173059,
                "lng": 91.751402
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
                "lat": 27.488605,
                "lng": 94.913943
            }
        },
        {
            "hospital": "Srimanta Sankardeva Hospital - Neurology",
            "email": "info@sankardevahospital.com",
            "phone": "+91-9365881431",
            "distance": "8 km",
            "coordinates": {
                "lat": 27.472832,
                "lng": 94.912036
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
                "lat": 24.775876,
                "lng": 92.794703
            }
        },
        {
            "hospital": "Narayana Hospital Silchar - Neurology Unit",
            "email": "info.silchar@narayanahealth.org",
            "phone": "+91-3842-263000",
            "distance": "9 km",
            "coordinates": {
                "lat": 24.820031,
                "lng": 92.805047
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
                "lat": 26.742139,
                "lng": 94.196034
            }
        },
        {
            "hospital": "Apeksha Hospital Jorhat - Neurology Center",
            "email": "info@apekshahospital.com",
            "phone": "+91-376-2371234",
            "distance": "10 km",
            "coordinates": {
                "lat": 26.750028,
                "lng": 94.210047
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
                "lat": 26.680334,
                "lng": 92.653325
            }
        },
        {
            "hospital": "Times Hospital Tezpur - Neuro Care Unit",
            "email": "info@timeshospital.in",
            "phone": "+91-3712-225678",
            "distance": "12 km",
            "coordinates": {
                "lat": 26.633977,
                "lng": 92.800046
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
                "lat": 26.347639,
                "lng": 92.683947
            }
        },
        {
            "hospital": "Nidan Hospital Nagaon - Neuro Clinic",
            "email": "info@nidanhospital.com",
            "phone": "+91-6026026020",
            "distance": "8 km",
            "coordinates": {
                "lat": 26.345028,
                "lng": 92.690042
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
                "lat": 26.483056,
                "lng": 90.557234
            }
        },
        {
            "hospital": "Lower Assam Hospital - Neuro Center",
            "email": "info@lowerassamhospital.com",
            "phone": "+91-3664-222345",
            "distance": "9 km",
            "coordinates": {
                "lat": 26.476527,
                "lng": 90.563045
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
                "lat": 27.490036,
                "lng": 95.359734
            }
        },
        {
            "hospital": "Aditya Hospital Tinsukia - Neuro Care",
            "email": "info@adityahospital.org",
            "phone": "+91-3742-332111",
            "distance": "11 km",
            "coordinates": {
                "lat": 27.485028,
                "lng": 95.365042
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
                "lat": 26.521439,
                "lng": 93.962034
            }
        },
        {
            "hospital": "Golaghat District Hospital - Neuro Unit",
            "email": "districth.golaghat@gov.in",
            "phone": "+91-3774-271234",
            "distance": "8 km",
            "coordinates": {
                "lat": 26.518028,
                "lng": 93.970047
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
                "lat": 26.984539,
                "lng": 94.639434
            }
        },
        {
            "hospital": "Sivasagar District Hospital - Neuro Clinic",
            "email": "districth.sivasagar@gov.in",
            "phone": "+91-3772-221456",
            "distance": "10 km",
            "coordinates": {
                "lat": 26.980028,
                "lng": 94.645047
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
                "lat": 27.472839,
                "lng": 94.579534
            }
        },
        {
            "hospital": "Dhemaji District Hospital - Neuro Care",
            "email": "districth.dhemaji@gov.in",
            "phone": "+91-3753-241234",
            "distance": "9 km",
            "coordinates": {
                "lat": 27.468028,
                "lng": 94.585047
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
                "lat": 27.236039,
                "lng": 94.103834
            }
        },
        {
            "hospital": "Lakhimpur District Hospital - Neuro Department",
            "email": "districth.lakhimpur@gov.in",
            "phone": "+91-3752-263456",
            "distance": "11 km",
            "coordinates": {
                "lat": 27.232028,
                "lng": 94.110047
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
                "lat": 26.442139,
                "lng": 92.029834
            }
        },
        {
            "hospital": "Darrang District Hospital - Neuro Center",
            "email": "districth.darrang@gov.in",
            "phone": "+91-3713-261234",
            "distance": "10 km",
            "coordinates": {
                "lat": 26.438028,
                "lng": 92.035047
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
                "lat": 26.323139,
                "lng": 90.966834
            }
        },
        {
            "hospital": "Barpeta District Hospital - Neuro Care",
            "email": "districth.barpeta@gov.in",
            "phone": "+91-3665-233234",
            "distance": "9 km",
            "coordinates": {
                "lat": 26.320028,
                "lng": 90.972047
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
                "lat": 26.401239,
                "lng": 90.271534
            }
        },
        {
            "hospital": "Kokrajhar District Hospital - Neuro Department",
            "email": "districth.kokrajhar@gov.in",
            "phone": "+91-3661-273234",
            "distance": "8 km",
            "coordinates": {
                "lat": 26.398028,
                "lng": 90.278047
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
                "lat": 26.019639,
                "lng": 89.986434
            }
        },
        {
            "hospital": "Dhubri District Hospital - Neuro Clinic",
            "email": "districth.dhubri@gov.in",
            "phone": "+91-3662-231456",
            "distance": "10 km",
            "coordinates": {
                "lat": 26.015028,
                "lng": 89.992047
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
                "lat": 26.166739,
                "lng": 90.616634
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
                "lat": 24.685839,
                "lng": 92.562534
            }
        },
        {
            "hospital": "Hailakandi District Hospital - Neuro Care",
            "email": "districth.hailakandi@gov.in",
            "phone": "+91-3844-263456",
            "distance": "9 km",
            "coordinates": {
                "lat": 24.682028,
                "lng": 92.568047
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
                "lat": 24.869739,
                "lng": 92.357334
            }
        },
        {
            "hospital": "Karimganj District Hospital - Neuro Department",
            "email": "districth.karimganj@gov.in",
            "phone": "+91-3843-263234",
            "distance": "10 km",
            "coordinates": {
                "lat": 24.865028,
                "lng": 92.363047
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
                "lat": 26.446339,
                "lng": 91.434634
            }
        },
        {
            "hospital": "Nalbari District Hospital - Neuro Clinic",
            "email": "districth.nalbari@gov.in",
            "phone": "+91-3624-221234",
            "distance": "11 km",
            "coordinates": {
                "lat": 26.442028,
                "lng": 91.440047
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
                "lat": 26.252439,
                "lng": 92.342434
            }
        },
        {
            "hospital": "Morigaon District Hospital - Neuro Unit",
            "email": "districth.morigaon@gov.in",
            "phone": "+91-3678-253234",
            "distance": "9 km",
            "coordinates": {
                "lat": 26.248028,
                "lng": 92.348047
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
                "lat": 26.004639,
                "lng": 92.856934
            }
        },
        {
            "hospital": "Hojai District Hospital - Neuro Care",
            "email": "districth.hojai@gov.in",
            "phone": "+91-3674-241234",
            "distance": "8 km",
            "coordinates": {
                "lat": 26.000028,
                "lng": 92.862047
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
                "lat": 26.740039,
                "lng": 93.150034
            }
        },
        {
            "hospital": "Biswanath District Hospital - Neuro Department",
            "email": "districth.biswanath@gov.in",
            "phone": "+91-3712-283234",
            "distance": "10 km",
            "coordinates": {
                "lat": 26.735028,
                "lng": 93.156047
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
                "lat": 26.925039,
                "lng": 94.800034
            }
        },
        {
            "hospital": "Charaideo District Hospital - Neuro Clinic",
            "email": "districth.charaideo@gov.in",
            "phone": "+91-3772-251234",
            "distance": "11 km",
            "coordinates": {
                "lat": 26.920028,
                "lng": 94.806047
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
                "lat": 26.523039,
                "lng": 90.457034
            }
        },
        {
            "hospital": "Chirang District Hospital - Neuro Unit",
            "email": "districth.chirang@gov.in",
            "phone": "+91-3663-283234",
            "distance": "9 km",
            "coordinates": {
                "lat": 26.518028,
                "lng": 90.463047
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
                "lat": 25.450039,
                "lng": 93.020034
            }
        },
        {
            "hospital": "Dima Hasao District Hospital - Neuro Care",
            "email": "districth.dimahasao@gov.in",
            "phone": "+91-3673-233234",
            "distance": "10 km",
            "coordinates": {
                "lat": 25.445028,
                "lng": 93.026047
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
                "lat": 26.010039,
                "lng": 93.440034
            }
        },
        {
            "hospital": "Karbi Anglong District Hospital - Neuro Department",
            "email": "districth.karbianglong@gov.in",
            "phone": "+91-3671-271234",
            "distance": "11 km",
            "coordinates": {
                "lat": 26.005028,
                "lng": 93.446047
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
                "lat": 25.980039,
                "lng": 92.950034
            }
        },
        {
            "hospital": "West Karbi Anglong District Hospital - Neuro Clinic",
            "email": "districth.westkarbi@gov.in",
            "phone": "+91-3671-241234",
            "distance": "9 km",
            "coordinates": {
                "lat": 25.975028,
                "lng": 92.956047
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
                "lat": 26.956039,
                "lng": 94.163834
            }
        },
        {
            "hospital": "Majuli District Hospital - Neuro Unit",
            "email": "districth.majuli@gov.in",
            "phone": "+91-376-2661234",
            "distance": "8 km",
            "coordinates": {
                "lat": 26.952028,
                "lng": 94.170047
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
                "lat": 26.753839,
                "lng": 92.102534
            }
        },
        {
            "hospital": "Udalguri District Hospital - Neuro Care",
            "email": "districth.udalguri@gov.in",
            "phone": "+91-3714-263234",
            "distance": "10 km",
            "coordinates": {
                "lat": 26.749028,
                "lng": 92.108047
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
                "lat": 26.634039,
                "lng": 91.082034
            }
        },
        {
            "hospital": "Baksa District Hospital - Neuro Department",
            "email": "districth.baksa@gov.in",
            "phone": "+91-3624-281234",
            "distance": "11 km",
            "coordinates": {
                "lat": 26.629028,
                "lng": 91.088047
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
                "lat": 26.115839,
                "lng": 91.708634
            }
        },
        {
            "hospital": "Kamrup District Hospital - Neuro Clinic",
            "email": "districth.kamrup@gov.in",
            "phone": "+91-361-2261234",
            "distance": "12 km",
            "coordinates": {
                "lat": 26.111028,
                "lng": 91.715047
            }
        }
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
