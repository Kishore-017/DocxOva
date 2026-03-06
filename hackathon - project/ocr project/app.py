from flask import Flask, request, jsonify
import easyocr
import cv2
import os
import re
import json
import bcrypt

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize OCR
reader = easyocr.Reader(['en'])

# ---------------- REGEX ----------------
pan_pattern = r'[A-Z]{5}[0-9]{4}[A-Z]'
aadhaar_pattern = r'\d{4}\s\d{4}\s\d{4}'
dob_pattern = r'\d{2}[/-]\d{2}[/-]\d{4}'


# ---------------- HASH FUNCTION ----------------
def hash_data(data):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(data.encode(), salt).decode()


# ---------------- REDACTION ----------------
def redact_text(text):

    entities = []

    # PAN detection
    pans = re.findall(pan_pattern, text)
    for p in pans:
        entities.append({
            "type": "PAN",
            "original_value": p,
            "hashed_value": hash_data(p)
        })
        text = text.replace(p, "XXXXXXXXXX")

    # Aadhaar detection
    aads = re.findall(aadhaar_pattern, text)
    for a in aads:
        entities.append({
            "type": "AADHAAR",
            "original_value": a,
            "hashed_value": hash_data(a)
        })
        text = text.replace(a, "XXXX XXXX XXXX")

    return text, entities


# ---------------- OCR FUNCTION ----------------
def run_ocr(image_path):

    image = cv2.imread(image_path)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

    results = reader.readtext(image)

    text_list = []

    for r in results:
        text = r[1].strip()

        if len(text) < 3:
            continue

        text_list.append(text)

    return text_list


# ---------------- NAME DETECTION ----------------
def detect_name(text_list):

    for text in text_list:

        if re.match(r'^[A-Z][a-z]+\s[A-Z][a-z]+$', text):
            return text

    return None


# ---------------- FIELD EXTRACTION ----------------
def extract_fields(text, text_list):

    data = {}

    name = detect_name(text_list)
    dob = re.search(dob_pattern, text)
    pan = re.search(pan_pattern, text)
    aadhaar = re.search(aadhaar_pattern, text)

    if name:
        data["Name"] = name

    if dob:
        data["DOB"] = dob.group()

    if pan:
        data["PAN"] = pan.group()

    if aadhaar:
        data["Aadhaar"] = aadhaar.group()

    return data


# ---------------- MAIN API ----------------
@app.route("/")
def home():
    return "OCR Document API Running"


@app.route("/process-document", methods=["POST"])
def process_document():

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # OCR
    text_list = run_ocr(filepath)

    full_text = " ".join(text_list)

    # Extraction
    extracted = extract_fields(full_text, text_list)

    # Redaction
    redacted_text, entities = redact_text(full_text)

    result = {
        "extracted_fields": extracted,
        "redacted_text": redacted_text,
        "detected_entities": entities
    }

    # Save JSON
    with open("redacted_output.json", "w") as f:
        json.dump(result, f, indent=4)

    return jsonify(result)


# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(debug=True)