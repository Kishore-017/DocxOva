import easyocr
import cv2
import re
import json
import bcrypt
from pymongo import MongoClient
from datetime import datetime


# -----------------------------
# DATABASE CONNECTION
# -----------------------------

from pymongo import MongoClient

client = MongoClient("mongodb+srv://Kishore:Kishore17@cluster3.clomoi7.mongodb.net/?appName=Cluster3")

db = client["DocxOva_App"]

collection = db["Results"]


# -----------------------------
# OCR SETUP
# -----------------------------

reader = easyocr.Reader(['en'])


# -----------------------------
# DOCUMENT FIELD MAP
# -----------------------------

document_fields = {

    "Aadhaar Card": ["Name", "DOB", "Aadhaar Number"],

    "PAN Card": ["Name", "PAN Number", "DOB"],

    "Driving License": ["Name", "DOB", "License Number"],

    "Passport": ["Name", "Passport Number", "DOB"],

    "Invoice": ["Invoice Number", "Date", "Amount"],

    "Bank Statement": ["Account Number", "Date", "Balance"],

    "Medical Report": ["Patient Name", "Age", "Diagnosis"],

    "Marksheet": ["Student Name", "Register Number", "Marks"],

    "Agreement": ["Party Names", "Date"],

    "ID Card": ["Name", "ID Number", "DOB"]
}


# -----------------------------
# REGEX PATTERNS
# -----------------------------

patterns = {

    "DOB": r"\d{2}[./-]\d{2}[./-]\d{4}",

    "Aadhaar Number": r"\d{4}\s\d{4}\s\d{4}",

    "PAN Number": r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",

    "License Number": r"[A-Z0-9]{6,}",

    "Passport Number": r"[A-Z][0-9]{7}",

    "Invoice Number": r"INV[- ]?\d+",

    "Account Number": r"\d{9,18}",

    "Amount": r"\d+\.\d{2}",

    "Balance": r"\d+\.\d{2}",

    "Date": r"\d{2}[/-]\d{2}[/-]\d{4}",

    "Age": r"\d{1,3}",

    "Register Number": r"[A-Z0-9]{6,}",

    "ID Number": r"[A-Z0-9]{6,}"
}


# -----------------------------
# HASH FUNCTION
# -----------------------------

def hash_data(data):

    salt = bcrypt.gensalt(rounds=10)

    return bcrypt.hashpw(data.encode(), salt).decode()


# -----------------------------
# DOCUMENT TYPE DETECTION
# -----------------------------

def detect_document_type(text):

    t = text.upper()

    if "AADHAAR" in t:
        return "Aadhaar Card"

    if "PAN" in t or "INCOME TAX" in t:
        return "PAN Card"

    if "DRIVING" in t:
        return "Driving License"

    if "PASSPORT" in t:
        return "Passport"

    if "INVOICE" in t:
        return "Invoice"

    return "ID Card"


# -----------------------------
# NAME DETECTION
# -----------------------------

def detect_name(text_list):

    for t in text_list:

        if re.match(r'^[A-Z]{3,}\s[A-Z]{3,}$', t.upper()):

            return t.title()

    return None


# -----------------------------
# MAIN PIPELINE
# -----------------------------

def process_document(image_path):

    image = cv2.imread(image_path)

    if image is None:

        print("❌ Image not found")

        return


    print("⏳ Running OCR...")

    results = reader.readtext(image)

    text_list = [r[1] for r in results]

    full_text = " ".join(text_list)


    # Detect document type
    doc_type = detect_document_type(full_text)

    print("📄 Document Type:", doc_type)


    fields = document_fields.get(doc_type, [])

    extracted = []


    for field in fields:

        value = None


        if "Name" in field:

            value = detect_name(text_list)


        else:

            match = re.search(patterns.get(field, ""), full_text)

            if match:

                value = match.group()


        if value:

            secure = hash_data(value)

            extracted.append({

                "field": field,

                "original": value,

                "bcrypt_hash": secure

            })


            print("FIELD:", field)

            print("ORIGINAL:", value)

            print("HASH:", secure)

            print("-" * 50)


    # -----------------------------
    # CREATE JSON OUTPUT
    # -----------------------------

    from datetime import datetime

    json_output = {
        "document_info": {
            "type": doc_type,
            "filename": image_path,
            "processed_at": str(datetime.now())
        },
        "extracted_data": extracted
    }


    # Save JSON file

    with open("pipeline_output.json", "w") as f:

        json.dump(json_output, f, indent=4)


    # Store in MongoDB

    existing = collection.find_one({"document_info.filename": image_path})

    if existing:
        print("⚠ Document already processed")
    else:
        collection.insert_one(json_output)
        print("✅ Stored in MongoDB Atlas")

        print("✅ JSON file saved as pipeline_output.json")


# -----------------------------
# RUN PROGRAM
# -----------------------------

if __name__ == "__main__":

    image_path = input("Enter image path: ")

    process_document(image_path)