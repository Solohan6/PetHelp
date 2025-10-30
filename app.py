import os
import json
from flask import Flask, render_template, jsonify, request
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- Configuration ---
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DATA_FILE = 'data.json'

# --- DATA FOR SYMPTOM CHECKER ---

DOG_SYMPTOM_DATA = {
    "vomiting": {
        "severity": "Moderate to Severe",
        "probable_diagnoses": ["Dietary Indiscretion (eating something they shouldn't have)", "Gastroenteritis (viral or bacterial)", "Pancreatitis", "Foreign Body Obstruction (a blockage)", "Kidney or Liver Issues", "Toxin Ingestion"],
        "course_of_action": "Withhold food for 12 hours (water is okay). If vomiting stops, offer a small meal of bland food (boiled chicken and rice).  GO TO A VET IMMEDIATELY if the dog is trying to vomit but can't, has a bloated abdomen, is very lethargic, or if there is blood in the vomit. For persistent vomiting (>24 hours), see a vet."
    },
    "diarrhea": {
        "severity": "Mild to Severe",
        "probable_diagnoses": ["Dietary Indiscretion or sudden food change", "Stress or excitement", "Intestinal Parasites (worms)", "Viral Infections (e.g., Parvovirus - very serious in puppies)", "Inflammatory Bowel Disease (IBD)"],
        "course_of_action": "Ensure constant access to fresh water to prevent dehydration. A bland diet (boiled chicken/rice) can help.  GO TO A VET IMMEDIATELY if the diarrhea is black, tarry, contains a lot of blood, or is accompanied by vomiting and extreme weakness. If diarrhea persists for more than 48 hours, a vet visit is needed."
    },
    "lethargy": {
        "severity": "Varies - A Sign of Many Issues",
        "probable_diagnoses": ["Infection (bacterial or viral)", "Pain (from injury, arthritis, etc.)", "Metabolic Disease (diabetes, thyroid issues)", "Heart or Organ problems", "Poisoning"],
        "course_of_action": "Lethargy is a non-specific but important sign. Monitor for other symptoms. Ensure the dog is eating and drinking. If lethargy is sudden, extreme, or lasts more than 24 hours, it warrants a vet visit. If it's paired with collapse or difficulty breathing, it's an emergency."
    },
    "coughing": {
        "severity": "Mild to Severe",
        "probable_diagnoses": ["Kennel Cough (infectious tracheobronchitis)", "Something stuck in the throat", "Heart Disease (especially in older, small-breed dogs)", "Pneumonia or other respiratory infections", "Collapsing Trachea"],
        "course_of_action": "A mild cough can be monitored at home for a day or two. Isolate from other dogs.  GO TO A VET IMMEDIATELY if the dog has blue-tinged gums, is struggling to breathe, or collapses. A persistent, harsh, or wet-sounding cough requires a vet visit to rule out serious conditions."
    },
    "itching_scratching": {
        "severity": "Mild to Moderate",
        "probable_diagnoses": ["Fleas or Ticks", "Environmental Allergies (pollen, dust)", "Food Allergies", "Mange (mites)", "Skin infection (bacterial or yeast)"],
        "course_of_action": "Check thoroughly for fleas using a flea comb. You can give a soothing oatmeal bath. Do not use medicated shampoos without vet advice. If itching is severe, causing open sores, hair loss, or is accompanied by a bad smell, a vet visit is needed to diagnose the underlying cause. Antihistamines like Cetirizine (Rigix) can sometimes be used, but ONLY after consulting your vet for the correct dosage."
    }
}

CAT_SYMPTOM_DATA = {
    "vomiting": {
        "severity": "Moderate to Severe",
        "probable_diagnoses": ["Hairballs", "Eating too fast", "Dietary Indiscretion", "Foreign Body Obstruction", "Inflammatory Bowel Disease (IBD)", "Kidney Disease (very common in older cats)", "Hyperthyroidism"],
        "course_of_action": "Occasional vomiting of hairballs can be normal. If vomiting is frequent (more than once a day), contains blood, or is paired with lethargy and lack of appetite, a vet visit is crucial.  Do NOT give any human medications. Withhold food for a few hours and ensure water is available."
    },
    "urinating_outside_litter_box": {
        "severity": "Potentially Severe",
        "probable_diagnoses": ["Feline Lower Urinary Tract Disease (FLUTD)", "Urinary Tract Infection (UTI)", "Bladder Stones or Crystals (can cause a blockage)", "Stress or anxiety", "Dirty litter box or dislike of the litter type"],
        "course_of_action": "This can be a medical emergency, ESPECIALLY for male cats. A urinary blockage is fatal if not treated. If your cat is straining to urinate with little or no output, crying in the litter box, or seems in pain, GO TO AN EMERGENCY VET IMMEDIATELY.  For other cases, ensure the litter box is clean and accessible and schedule a vet appointment to rule out medical issues."
    },
    "hiding_lethargy": {
        "severity": "Significant - Cats Hide Pain",
        "probable_diagnoses": ["Pain (from injury, dental disease, arthritis)", "Fever or Infection (e.g., Feline Immunodeficiency Virus - FIV)", "Organ disease (kidney, liver)", "Stress or fear"],
        "course_of_action": "Cats are masters at hiding illness. A sudden change in behaviour like hiding or extreme lethargy is a major red flag. Try to entice them with a favourite treat. If the cat hasn't eaten in 24 hours or the hiding persists, a vet check-up is essential. Do not force them out of their hiding spot."
    },
    "sneezing_discharge": {
        "severity": "Mild to Moderate",
        "probable_diagnoses": ["Feline Upper Respiratory Infection (URI) - 'Cat Flu'", "Allergies", "Dental problems", "Foreign object in the nose"],
        "course_of_action": "For mild sneezing with clear discharge, ensure the cat is eating and drinking. You can gently wipe their nose and eyes with a warm, damp cloth. Use a humidifier to ease congestion. If the discharge is green/yellow, the cat stops eating, or seems to have difficulty breathing, a vet visit is necessary for potential antibiotics."
    },
     "changes_in_appetite": {
        "severity": "Significant",
        "probable_diagnoses": ["Dental Disease (painful mouth)", "Kidney Disease", "Hyperthyroidism (increased appetite)", "Diabetes (increased appetite/thirst)", "Stress or changes in environment"],
        "course_of_action": "Any change, whether increased or decreased appetite, is important. A cat that stops eating for more than 24-48 hours is at risk for a serious liver condition (hepatic lipidosis). An unquenchable thirst or ravenous appetite also requires a vet visit to check for underlying diseases."
    }
}

# NEW: Checklist data
DOG_CHECKLIST = [
    "Behavior: Is your dog acting unusually quiet, agitated, or aggressive?",
    "Appetite & Water Intake: Are they eating/drinking more or less than usual?",
    "Gums: Are their gums a healthy pink, or are they pale, white, or blue?",
    "Energy Level: Is their energy significantly lower than normal?",
    "Mobility: Are they walking stiffly, limping, or reluctant to move?",
    "Bathroom Habits: Any change in the frequency, color, or consistency of urine or feces?"
]

CAT_CHECKLIST = [
    "Behavior: Is your cat hiding more, less interactive, or vocalizing differently?",
    "Litter Box: Are they using the box normally? Any straining, or going outside the box?",
    "Grooming: Have they stopped grooming (messy coat) or are they over-grooming one spot?",
    "Appetite & Water Intake: Any increase or decrease in hunger or thirst?",
    "Mobility: Are they reluctant to jump on furniture they normally use?",
    "Physical Signs: Any squinting, head tilting, or obvious signs of pain when touched?"
]

# --- Helper Functions for Pet Data Persistence ---
def load_data():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE, 'r') as f:
        try: return json.load(f)
        except json.JSONDecodeError: return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- Page Routes ---
@app.route('/')
def home(): return render_template('index.html')

@app.route('/symptom-checker')
def symptom_checker():
    # NEW: Pass checklist data to the template
    return render_template('symptom_checker.html', dog_checklist=DOG_CHECKLIST, cat_checklist=CAT_CHECKLIST)

@app.route('/lost-pet-map')
def lost_pet_map():
    central_locations = [
        {"name": "DHA Phase 5", "coords": [31.478, 74.375]},
        {"name": "Gulberg (Liberty Mkt)", "coords": [31.509, 74.333]},
        {"name": "Cantt (Fortress Stadium)", "coords": [31.536, 74.366]},
        {"name": "Model Town", "coords": [31.474, 74.332]},
        {"name": "Johar Town", "coords": [31.464, 74.282]},
        {"name": "Lake City", "coords": [31.363, 74.244]},
        {"name": "Bahria Town", "coords": [31.365, 74.185]},
        {"name": "Garden Town", "coords": [31.500, 74.312]},
        {"name": "Mall Road (Charing Cross)", "coords": [31.558, 74.333]},
        {"name": "MM Alam Road", "coords": [31.516, 74.343]},
        {"name": "Wapda Town", "coords": [31.442, 74.269]},
    ]
    return render_template('lost_pet_map.html', locations=central_locations)

@app.route('/wip')
def wip(): return render_template('wip.html')

# --- API Endpoints ---
@app.route('/api/symptom-check', methods=['POST'])
def get_symptom_advice():
    data = request.get_json()
    animal_type = data.get('animal_type')
    symptoms = data.get('symptoms', [])
    if not symptoms: return jsonify({"error": "No symptoms provided"}), 400
    source_data = DOG_SYMPTOM_DATA if animal_type == 'dog' else CAT_SYMPTOM_DATA
    
    all_diagnoses, all_actions = set(), set()
    highest_severity, severity_map = "Mild", {"Mild": 1, "Moderate": 2, "Severe": 3, "Potentially Severe": 3, "Significant": 3}

    for symptom in symptoms:
        symptom_info = source_data.get(symptom)
        if symptom_info:
            all_diagnoses.update(symptom_info["probable_diagnoses"])
            all_actions.add(symptom_info["course_of_action"])
            current_severity = symptom_info.get("severity", "Mild").split(' ')[0]
            if severity_map.get(current_severity, 1) > severity_map.get(highest_severity, 1):
                highest_severity = current_severity
    
    combined_actions = " ".join(all_actions)
    if len(symptoms) > 1:
        combined_actions += " Given the combination of symptoms, a veterinary consultation is strongly recommended to get an accurate diagnosis."

    return jsonify({"severity": highest_severity, "probable_diagnoses": list(all_diagnoses), "course_of_action": combined_actions})

# (The rest of the Pet API endpoints are unchanged)
@app.route('/api/pets', methods=['GET'])
def get_pets(): return jsonify(load_data())

@app.route('/api/pets', methods=['POST'])
def add_pet():
    pets = load_data()
    file = request.files.get('pet_image')
    if not file or file.filename == '': return jsonify({"error": "No image file provided"}), 400
    
    filename = secure_filename(file.filename)
    unique_filename = str(int(float(request.form['submissionTime']) / 1000)) + '_' + filename
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(file_path)
    
    pet_id = 'pet_' + request.form['submissionTime']
    new_pet_data = {
        "id": pet_id, "name": request.form['pet_name'], "contact": request.form['contact'],
        "description": request.form['description'], "imageUrl": '/' + file_path,
        "latlng": [float(request.form['latitude']), float(request.form['longitude'])],
        "submissionTime": int(request.form['submissionTime']), "status": 'not-found',
    }
    pets[pet_id] = new_pet_data
    save_data(pets)
    return jsonify(new_pet_data), 201

@app.route('/api/pets/<pet_id>/status', methods=['POST'])
def update_pet_status(pet_id):
    pets = load_data()
    if pet_id in pets:
        pets[pet_id]['status'] = 'found' if pets[pet_id]['status'] == 'not-found' else 'not-found'
        save_data(pets)
        return jsonify(pets[pet_id])
    return jsonify({"error": "Pet not found"}), 404

@app.route('/api/pets/<pet_id>', methods=['DELETE'])
def delete_pet(pet_id):
    pets = load_data()
    if pet_id in pets:
        try:
            image_path = pets[pet_id]['imageUrl'].lstrip('/')
            if os.path.exists(image_path): os.remove(image_path)
        except Exception as e:
            print(f"Error deleting image file: {e}")
        del pets[pet_id]
        save_data(pets)
        return jsonify({"success": True}), 200
    return jsonify({"error": "Pet not found"}), 404