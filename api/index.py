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
        "Central Delhi": [
            {"hospital": "Ram Manohar Lohia Hospital - Neurology", "email": "demo.rml@example.com", "phone": "+919999991001", "distance": "3 km", "coordinates": {"lat": 28.636251, "lng": 77.214447}},
            {"hospital": "Lady Hardinge Medical College - Neuro Dept", "email": "demo.lhmc@example.com", "phone": "+919999991002", "distance": "4 km", "coordinates": {"lat": 28.634589, "lng": 77.212834}},
            {"hospital": "Dr. Ram Manohar Lohia Hospital ICU", "email": "demo.rmlicu@example.com", "phone": "+919999991003", "distance": "3.5 km", "coordinates": {"lat": 28.636789, "lng": 77.215123}},
            {"hospital": "Lok Nayak Hospital - Neurology Unit", "email": "demo.lnjp@example.com", "phone": "+919999991004", "distance": "5 km", "coordinates": {"lat": 28.647234, "lng": 77.233456}}
        ],
        "South Delhi": [
            {"hospital": "AIIMS Delhi - Neurosciences Centre", "email": "demo.aiims@example.com", "phone": "+919999992001", "distance": "5 km", "coordinates": {"lat": 28.568235, "lng": 77.209657}},
            {"hospital": "Fortis Escorts Hospital - Neurology", "email": "demo.fortisescorts@example.com", "phone": "+919999992002", "distance": "7 km", "coordinates": {"lat": 28.569823, "lng": 77.243156}},
            {"hospital": "Max Super Speciality Hospital Saket", "email": "demo.maxsaket@example.com", "phone": "+919999992003", "distance": "8 km", "coordinates": {"lat": 28.527234, "lng": 77.218945}},
            {"hospital": "Batra Hospital - Neurology Department", "email": "demo.batra@example.com", "phone": "+919999992004", "distance": "6 km", "coordinates": {"lat": 28.538967, "lng": 77.240123}}
        ],
        "North Delhi": [
            {"hospital": "Hindu Rao Hospital - Neurology", "email": "demo.hindurao@example.com", "phone": "+919999993001", "distance": "4 km", "coordinates": {"lat": 28.691234, "lng": 77.215678}},
            {"hospital": "Kasturba Hospital - Neuro Unit", "email": "demo.kasturba@example.com", "phone": "+919999993002", "distance": "5 km", "coordinates": {"lat": 28.694567, "lng": 77.219834}},
            {"hospital": "Civil Hospital - Neurology Dept", "email": "demo.civilhosp@example.com", "phone": "+919999993003", "distance": "6 km", "coordinates": {"lat": 28.698234, "lng": 77.221945}},
            {"hospital": "Aruna Asaf Ali Hospital", "email": "demo.arunasaf@example.com", "phone": "+919999993004", "distance": "5.5 km", "coordinates": {"lat": 28.693456, "lng": 77.218123}}
        ],
        "East Delhi": [
            {"hospital": "Guru Teg Bahadur Hospital - Neurology", "email": "demo.gtb@example.com", "phone": "+919999994001", "distance": "6 km", "coordinates": {"lat": 28.661234, "lng": 77.305678}},
            {"hospital": "Lal Bahadur Shastri Hospital", "email": "demo.lbsh@example.com", "phone": "+919999994002", "distance": "7 km", "coordinates": {"lat": 28.647823, "lng": 77.298456}},
            {"hospital": "Hedgewar Hospital - Neuro Clinic", "email": "demo.hedgewar@example.com", "phone": "+919999994003", "distance": "8 km", "coordinates": {"lat": 28.655234, "lng": 77.301234}},
            {"hospital": "Max Hospital Patparganj", "email": "demo.maxpat@example.com", "phone": "+919999994004", "distance": "9 km", "coordinates": {"lat": 28.635678, "lng": 77.295123}}
        ],
        "West Delhi": [
            {"hospital": "Acharya Shree Bhikshu Hospital", "email": "demo.bhikshu@example.com", "phone": "+919999995001", "distance": "5 km", "coordinates": {"lat": 28.659234, "lng": 77.109567}},
            {"hospital": "Deen Dayal Upadhyay Hospital - Neurology", "email": "demo.ddu@example.com", "phone": "+919999995002", "distance": "6 km", "coordinates": {"lat": 28.651823, "lng": 77.095234}},
            {"hospital": "Jaipur Golden Hospital - Neuro", "email": "demo.jgh@example.com", "phone": "+919999995003", "distance": "7 km", "coordinates": {"lat": 28.667234, "lng": 77.113456}},
            {"hospital": "Sanjay Gandhi Memorial Hospital", "email": "demo.sgmh@example.com", "phone": "+919999995004", "distance": "8 km", "coordinates": {"lat": 28.643567, "lng": 77.089123}}
        ],
        "New Delhi": [
            {"hospital": "Safdarjung Hospital - Neurology", "email": "demo.safdarjung@example.com", "phone": "+919999996001", "distance": "4 km", "coordinates": {"lat": 28.567234, "lng": 77.206789}},
            {"hospital": "Apollo Hospital New Delhi", "email": "demo.apollond@example.com", "phone": "+919999996002", "distance": "5 km", "coordinates": {"lat": 28.573456, "lng": 77.201234}},
            {"hospital": "BLK Super Speciality Hospital", "email": "demo.blk@example.com", "phone": "+919999996003", "distance": "6 km", "coordinates": {"lat": 28.635234, "lng": 77.184567}},
            {"hospital": "Indraprastha Apollo Hospital", "email": "demo.indraprastha@example.com", "phone": "+919999996004", "distance": "7 km", "coordinates": {"lat": 28.545678, "lng": 77.270123}}
        ],
        "North West Delhi": [
            {"hospital": "Babu Jagjivan Ram Hospital", "email": "demo.bjrh@example.com", "phone": "+919999997001", "distance": "5 km", "coordinates": {"lat": 28.723456, "lng": 77.135678}},
            {"hospital": "Sanjay Gandhi Memorial Hospital", "email": "demo.sgmhnw@example.com", "phone": "+919999997002", "distance": "6 km", "coordinates": {"lat": 28.719234, "lng": 77.128945}},
            {"hospital": "Rao Tula Ram Memorial Hospital", "email": "demo.rtrm@example.com", "phone": "+919999997003", "distance": "7 km", "coordinates": {"lat": 28.714567, "lng": 77.142123}},
            {"hospital": "Pitampura Hospital - Neurology", "email": "demo.pitampura@example.com", "phone": "+919999997004", "distance": "8 km", "coordinates": {"lat": 28.726789, "lng": 77.138456}}
        ],
        "South West Delhi": [
            {"hospital": "Fortis Flt. Lt. Rajan Dhall Hospital", "email": "demo.fortissw@example.com", "phone": "+919999998001", "distance": "6 km", "coordinates": {"lat": 28.591234, "lng": 77.067856}},
            {"hospital": "Vivekananda Polyclinic - Neurology", "email": "demo.vivek@example.com", "phone": "+919999998002", "distance": "7 km", "coordinates": {"lat": 28.585678, "lng": 77.074123}},
            {"hospital": "Moolchand Hospital - Neuro Dept", "email": "demo.moolchand@example.com", "phone": "+919999998003", "distance": "8 km", "coordinates": {"lat": 28.578234, "lng": 77.081456}},
            {"hospital": "Manipal Hospital Dwarka", "email": "demo.manipaldwarka@example.com", "phone": "+919999998004", "distance": "9 km", "coordinates": {"lat": 28.570456, "lng": 77.058789}}
        ],
        "South East Delhi": [
            {"hospital": "Moolchand Medcity - Neurology", "email": "demo.moolchandse@example.com", "phone": "+919999999001", "distance": "5 km", "coordinates": {"lat": 28.547234, "lng": 77.248967}},
            {"hospital": "Pushpawati Singhania Hospital", "email": "demo.psri@example.com", "phone": "+919999999002", "distance": "6 km", "coordinates": {"lat": 28.539456, "lng": 77.255123}},
            {"hospital": "Max Smart Hospital Saket", "email": "demo.maxsmart@example.com", "phone": "+919999999003", "distance": "7 km", "coordinates": {"lat": 28.532678, "lng": 77.261456}},
            {"hospital": "Apollo Spectra Hospital Nehru Place", "email": "demo.spectra@example.com", "phone": "+919999999004", "distance": "8 km", "coordinates": {"lat": 28.550234, "lng": 77.246789}}
        ],
        "North East Delhi": [
            {"hospital": "Jag Pravesh Chandra Hospital", "email": "demo.jpc@example.com", "phone": "+919998881001", "distance": "5 km", "coordinates": {"lat": 28.693234, "lng": 77.284567}},
            {"hospital": "Yashoda Super Speciality Hospital", "email": "demo.yashoda@example.com", "phone": "+919998881002", "distance": "6 km", "coordinates": {"lat": 28.686789, "lng": 77.291234}},
            {"hospital": "Shree Hospital - Neurology Unit", "email": "demo.shree@example.com", "phone": "+919998881003", "distance": "7 km", "coordinates": {"lat": 28.679456, "lng": 77.297856}},
            {"hospital": "Metro Hospital Preet Vihar", "email": "demo.metro@example.com", "phone": "+919998881004", "distance": "8 km", "coordinates": {"lat": 28.672123, "lng": 77.303945}}
        ],
        "Shahdara": [
            {"hospital": "Max Super Speciality Hospital Patparganj", "email": "demo.maxshd@example.com", "phone": "+919998882001", "distance": "6 km", "coordinates": {"lat": 28.638234, "lng": 77.307856}},
            {"hospital": "Fortis Hospital Noida Extension", "email": "demo.fortisshd@example.com", "phone": "+919998882002", "distance": "7 km", "coordinates": {"lat": 28.630567, "lng": 77.314123}},
            {"hospital": "Kailash Hospital - Neurology", "email": "demo.kailash@example.com", "phone": "+919998882003", "distance": "8 km", "coordinates": {"lat": 28.623789, "lng": 77.320456}},
            {"hospital": "Shanti Mukand Hospital", "email": "demo.shantimukand@example.com", "phone": "+919998882004", "distance": "9 km", "coordinates": {"lat": 28.616234, "lng": 77.326789}}
        ]
    },

    # ========== MAHARASHTRA (Major Districts) ==========
    "Maharashtra": {
        "Mumbai City": [
            {"hospital": "KEM Hospital - Neurology Department", "email": "demo.kem@example.com", "phone": "+919888881001", "distance": "5 km", "coordinates": {"lat": 19.002474, "lng": 72.841480}},
            {"hospital": "Lilavati Hospital - Neurosciences", "email": "demo.lilavati@example.com", "phone": "+919888881002", "distance": "7 km", "coordinates": {"lat": 19.059600, "lng": 72.829500}},
            {"hospital": "Hinduja Hospital - Neurology", "email": "demo.hinduja@example.com", "phone": "+919888881003", "distance": "10 km", "coordinates": {"lat": 19.052200, "lng": 72.834600}},
            {"hospital": "Bombay Hospital - Neuro Unit", "email": "demo.bombay@example.com", "phone": "+919888881004", "distance": "12 km", "coordinates": {"lat": 18.968234, "lng": 72.826789}}
        ],
        "Mumbai Suburban": [
            {"hospital": "Kokilaben Dhirubhai Ambani Hospital", "email": "demo.kokilaben@example.com", "phone": "+919888882001", "distance": "8 km", "coordinates": {"lat": 19.173456, "lng": 72.836789}},
            {"hospital": "Nanavati Super Speciality Hospital", "email": "demo.nanavati@example.com", "phone": "+919888882002", "distance": "9 km", "coordinates": {"lat": 19.045234, "lng": 72.828967}},
            {"hospital": "Fortis Hospital Mulund", "email": "demo.fortismulund@example.com", "phone": "+919888882003", "distance": "11 km", "coordinates": {"lat": 19.172789, "lng": 72.956123}},
            {"hospital": "Hiranandani Hospital Powai", "email": "demo.hiranandani@example.com", "phone": "+919888882004", "distance": "13 km", "coordinates": {"lat": 19.120456, "lng": 72.907234}}
        ],
        "Pune": [
            {"hospital": "Ruby Hall Clinic - Neurology", "email": "demo.ruby@example.com", "phone": "+919888883001", "distance": "5 km", "coordinates": {"lat": 18.518234, "lng": 73.866789}},
            {"hospital": "Jehangir Hospital - Neuro Department", "email": "demo.jehangir@example.com", "phone": "+919888883002", "distance": "6 km", "coordinates": {"lat": 18.526567, "lng": 73.855123}},
            {"hospital": "Deenanath Mangeshkar Hospital", "email": "demo.deenanath@example.com", "phone": "+919888883003", "distance": "7 km", "coordinates": {"lat": 18.476789, "lng": 73.871456}},
            {"hospital": "Sahyadri Super Speciality Hospital", "email": "demo.sahyadri@example.com", "phone": "+919888883004", "distance": "8 km", "coordinates": {"lat": 18.534234, "lng": 73.844967}}
        ],
        "Thane": [
            {"hospital": "Jupiter Hospital - Neurology", "email": "demo.jupiter@example.com", "phone": "+919888884001", "distance": "6 km", "coordinates": {"lat": 19.184234, "lng": 72.970567}},
            {"hospital": "Bethany Hospital - Neuro Unit", "email": "demo.bethany@example.com", "phone": "+919888884002", "distance": "7 km", "coordinates": {"lat": 19.190789, "lng": 72.963234}},
            {"hospital": "Oscar Hospital Thane", "email": "demo.oscar@example.com", "phone": "+919888884003", "distance": "8 km", "coordinates": {"lat": 19.197456, "lng": 72.956789}},
            {"hospital": "Currae Hospital - Neurology", "email": "demo.currae@example.com", "phone": "+919888884004", "distance": "9 km", "coordinates": {"lat": 19.202123, "lng": 72.978945}}
        ],
        "Nagpur": [
            {"hospital": "AIIMS Nagpur - Neurosciences", "email": "demo.aiimsnagpur@example.com", "phone": "+919888885001", "distance": "5 km", "coordinates": {"lat": 21.145800, "lng": 79.088158}},
            {"hospital": "Wockhardt Hospital Nagpur", "email": "demo.wockhardtnagpur@example.com", "phone": "+919888885002", "distance": "6 km", "coordinates": {"lat": 21.151234, "lng": 79.093456}},
            {"hospital": "Orange City Hospital - Neurology", "email": "demo.orangecity@example.com", "phone": "+919888885003", "distance": "7 km", "coordinates": {"lat": 21.138567, "lng": 79.081234}},
            {"hospital": "Meditrina Hospital - Neuro Dept", "email": "demo.meditrina@example.com", "phone": "+919888885004", "distance": "8 km", "coordinates": {"lat": 21.144789, "lng": 79.076789}}
        ],
        "Nashik": [
            {"hospital": "Wockhardt Hospital Nashik", "email": "demo.wockhardtnashik@example.com", "phone": "+919888886001", "distance": "5 km", "coordinates": {"lat": 19.998234, "lng": 73.791567}},
            {"hospital": "Ashoka Medicover Hospital", "email": "demo.ashoka@example.com", "phone": "+919888886002", "distance": "6 km", "coordinates": {"lat": 20.004789, "lng": 73.784234}},
            {"hospital": "Suyash Hospital - Neurology", "email": "demo.suyash@example.com", "phone": "+919888886003", "distance": "7 km", "coordinates": {"lat": 19.991456, "lng": 73.798789}},
            {"hospital": "Lifeline Hospital Nashik", "email": "demo.lifeline@example.com", "phone": "+919888886004", "distance": "8 km", "coordinates": {"lat": 20.011123, "lng": 73.777945}}
        ]
    },

    # ========== KARNATAKA (Major Districts) ==========
    "Karnataka": {
        "Bangalore Urban": [
            {"hospital": "NIMHANS - Neurosciences Centre", "email": "demo.nimhans@example.com", "phone": "+919777771001", "distance": "6 km", "coordinates": {"lat": 12.943253, "lng": 77.596603}},
            {"hospital": "Manipal Hospital - Neurology", "email": "demo.manipalblr@example.com", "phone": "+919777771002", "distance": "8 km", "coordinates": {"lat": 12.977234, "lng": 77.608456}},
            {"hospital": "Apollo Hospital Bangalore", "email": "demo.apolloblr@example.com", "phone": "+919777771003", "distance": "10 km", "coordinates": {"lat": 12.956789, "lng": 77.638123}},
            {"hospital": "Fortis Hospital Bannerghatta Road", "email": "demo.fortisblr@example.com", "phone": "+919777771004", "distance": "12 km", "coordinates": {"lat": 12.889456, "lng": 77.608967}}
        ],
        "Mysore": [
            {"hospital": "JSS Hospital - Neurology Department", "email": "demo.jss@example.com", "phone": "+919777772001", "distance": "5 km", "coordinates": {"lat": 12.307234, "lng": 76.639567}},
            {"hospital": "Apollo BGS Hospital Mysore", "email": "demo.apollomysore@example.com", "phone": "+919777772002", "distance": "6 km", "coordinates": {"lat": 12.314789, "lng": 76.632234}},
            {"hospital": "Columbia Asia Hospital - Neuro", "email": "demo.columbiamysore@example.com", "phone": "+919777772003", "distance": "7 km", "coordinates": {"lat": 12.299456, "lng": 76.646789}},
            {"hospital": "Vikram Hospital Mysore", "email": "demo.vikrammysore@example.com", "phone": "+919777772004", "distance": "8 km", "coordinates": {"lat": 12.321123, "lng": 76.625945}}
        ],
        "Mangalore": [
            {"hospital": "KMC Hospital Mangalore - Neurology", "email": "demo.kmc@example.com", "phone": "+919777773001", "distance": "5 km", "coordinates": {"lat": 12.917234, "lng": 74.856567}},
            {"hospital": "AJ Hospital - Neuro Department", "email": "demo.ajhosp@example.com", "phone": "+919777773002", "distance": "6 km", "coordinates": {"lat": 12.924789, "lng": 74.849234}},
            {"hospital": "Yenepoya Hospital - Neurology", "email": "demo.yenepoya@example.com", "phone": "+919777773003", "distance": "7 km", "coordinates": {"lat": 12.909456, "lng": 74.863789}},
            {"hospital": "Father Muller Medical College Hospital", "email": "demo.fathermuller@example.com", "phone": "+919777773004", "distance": "8 km", "coordinates": {"lat": 12.931123, "lng": 74.842945}}
        ],
        "Hubli-Dharwad": [
            {"hospital": "SDM Hospital Dharwad - Neurology", "email": "demo.sdm@example.com", "phone": "+919777774001", "distance": "5 km", "coordinates": {"lat": 15.457234, "lng": 75.007567}},
            {"hospital": "KIMS Hubli - Neuro Department", "email": "demo.kimshubli@example.com", "phone": "+919777774002", "distance": "6 km", "coordinates": {"lat": 15.364789, "lng": 75.123234}},
            {"hospital": "Srinivas Hospital - Neurology", "email": "demo.srinivas@example.com", "phone": "+919777774003", "distance": "7 km", "coordinates": {"lat": 15.450456, "lng": 75.014789}},
            {"hospital": "Max Hospital Hubli", "email": "demo.maxhubli@example.com", "phone": "+919777774004", "distance": "8 km", "coordinates": {"lat": 15.371123, "lng": 75.116945}}
        ]
    },

    # ========== WEST BENGAL (Major Districts) ==========
    "West Bengal": {
        "Kolkata": [
            {"hospital": "AMRI Hospital - Neurosciences", "email": "demo.amri@example.com", "phone": "+919666661001", "distance": "5 km", "coordinates": {"lat": 22.533234, "lng": 88.363567}},
            {"hospital": "Apollo Gleneagles Hospital", "email": "demo.apollokol@example.com", "phone": "+919666661002", "distance": "6 km", "coordinates": {"lat": 22.540789, "lng": 88.356234}},
            {"hospital": "Medica Superspecialty Hospital", "email": "demo.medica@example.com", "phone": "+919666661003", "distance": "7 km", "coordinates": {"lat": 22.526456, "lng": 88.370789}},
            {"hospital": "Rabindranath Tagore Hospital", "email": "demo.rthospital@example.com", "phone": "+919666661004", "distance": "8 km", "coordinates": {"lat": 22.547123, "lng": 88.349945}}
        ],
        "Howrah": [
            {"hospital": "Narayana Superspecialty Hospital", "email": "demo.narayanahowrah@example.com", "phone": "+919666662001", "distance": "6 km", "coordinates": {"lat": 22.595234, "lng": 88.266567}},
            {"hospital": "CMRI Hospital Howrah", "email": "demo.cmri@example.com", "phone": "+919666662002", "distance": "7 km", "coordinates": {"lat": 22.602789, "lng": 88.259234}},
            {"hospital": "Horizon Life Line Hospital", "email": "demo.horizon@example.com", "phone": "+919666662003", "distance": "8 km", "coordinates": {"lat": 22.588456, "lng": 88.273789}},
            {"hospital": "Belle Vue Clinic - Neurology", "email": "demo.bellevue@example.com", "phone": "+919666662004", "distance": "9 km", "coordinates": {"lat": 22.609123, "lng": 88.252945}}
        ],
        "Darjeeling": [
            {"hospital": "North Bengal Medical College - Neurology", "email": "demo.nbmc@example.com", "phone": "+919666663001", "distance": "5 km", "coordinates": {"lat": 26.720234, "lng": 88.428567}},
            {"hospital": "Siliguri District Hospital - Neuro", "email": "demo.siliguri@example.com", "phone": "+919666663002", "distance": "6 km", "coordinates": {"lat": 26.727789, "lng": 88.421234}},
            {"hospital": "Neotia Getwel Hospital Siliguri", "email": "demo.neotiasiliguri@example.com", "phone": "+919666663003", "distance": "7 km", "coordinates": {"lat": 26.713456, "lng": 88.435789}},
            {"hospital": "District Hospital Darjeeling", "email": "demo.darjeeling@example.com", "phone": "+919666663004", "distance": "8 km", "coordinates": {"lat": 27.041123, "lng": 88.262945}}
        ],
        "Durgapur": [
            {"hospital": "IQ City Medical College - Neurology", "email": "demo.iqcity@example.com", "phone": "+919666664001", "distance": "5 km", "coordinates": {"lat": 23.548234, "lng": 87.291567}},
            {"hospital": "Durgapur Steel Plant Hospital", "email": "demo.dsph@example.com", "phone": "+919666664002", "distance": "6 km", "coordinates": {"lat": 23.555789, "lng": 87.284234}},
            {"hospital": "AMRI Hospital Durgapur", "email": "demo.amridur@example.com", "phone": "+919666664003", "distance": "7 km", "coordinates": {"lat": 23.541456, "lng": 87.298789}},
            {"hospital": "Mission Hospital Durgapur", "email": "demo.mission@example.com", "phone": "+919666664004", "distance": "8 km", "coordinates": {"lat": 23.562123, "lng": 87.277945}}
        ]
    },

    # ========== TAMIL NADU (Major Districts) ==========
    "Tamil Nadu": {
        "Chennai": [
            {"hospital": "Apollo Hospitals - Neurosciences", "email": "demo.apollochn@example.com", "phone": "+919555551001", "distance": "6 km", "coordinates": {"lat": 13.035234, "lng": 80.248567}},
            {"hospital": "Fortis Malar Hospital - Neurology", "email": "demo.fortischn@example.com", "phone": "+919555551002", "distance": "7 km", "coordinates": {"lat": 13.042789, "lng": 80.241234}},
            {"hospital": "MIOT International - Neuro Dept", "email": "demo.miot@example.com", "phone": "+919555551003", "distance": "8 km", "coordinates": {"lat": 13.028456, "lng": 80.255789}},
            {"hospital": "Kauvery Hospital Chennai", "email": "demo.kauverychn@example.com", "phone": "+919555551004", "distance": "9 km", "coordinates": {"lat": 13.049123, "lng": 80.234945}}
        ],
        "Coimbatore": [
            {"hospital": "PSG Hospitals - Neurology", "email": "demo.psg@example.com", "phone": "+919555552001", "distance": "5 km", "coordinates": {"lat": 11.025234, "lng": 76.965567}},
            {"hospital": "Kovai Medical Center - Neuro", "email": "demo.kmc@example.com", "phone": "+919555552002", "distance": "6 km", "coordinates": {"lat": 11.032789, "lng": 76.958234}},
            {"hospital": "Ganga Hospital - Neurology", "email": "demo.ganga@example.com", "phone": "+919555552003", "distance": "7 km", "coordinates": {"lat": 11.018456, "lng": 76.972789}},
            {"hospital": "Sri Ramakrishna Hospital", "email": "demo.sriramakrishna@example.com", "phone": "+919555552004", "distance": "8 km", "coordinates": {"lat": 11.039123, "lng": 76.951945}}
        ],
        "Madurai": [
            {"hospital": "Meenakshi Mission Hospital - Neurology", "email": "demo.meenakshi@example.com", "phone": "+919555553001", "distance": "5 km", "coordinates": {"lat": 9.925234, "lng": 78.121567}},
            {"hospital": "Apollo Speciality Hospital Madurai", "email": "demo.apollomadurai@example.com", "phone": "+919555553002", "distance": "6 km", "coordinates": {"lat": 9.932789, "lng": 78.114234}},
            {"hospital": "Devadoss Multispecialty Hospital", "email": "demo.devadoss@example.com", "phone": "+919555553003", "distance": "7 km", "coordinates": {"lat": 9.918456, "lng": 78.128789}},
            {"hospital": "Vadamalayan Hospital - Neuro", "email": "demo.vadamalayan@example.com", "phone": "+919555553004", "distance": "8 km", "coordinates": {"lat": 9.939123, "lng": 78.107945}}
        ],
        "Trichy": [
            {"hospital": "Kauvery Hospital Trichy - Neurology", "email": "demo.kauverytrichy@example.com", "phone": "+919555554001", "distance": "5 km", "coordinates": {"lat": 10.805234, "lng": 78.686567}},
            {"hospital": "Apollo Speciality Hospital Trichy", "email": "demo.apollotrichy@example.com", "phone": "+919555554002", "distance": "6 km", "coordinates": {"lat": 10.812789, "lng": 78.679234}},
            {"hospital": "Harshamitra Hospital - Neuro Dept", "email": "demo.harshamitra@example.com", "phone": "+919555554003", "distance": "7 km", "coordinates": {"lat": 10.798456, "lng": 78.693789}},
            {"hospital": "Sri Ramachandra Hospital Trichy", "email": "demo.ramachandratrichy@example.com", "phone": "+919555554004", "distance": "8 km", "coordinates": {"lat": 10.819123, "lng": 78.672945}}
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
