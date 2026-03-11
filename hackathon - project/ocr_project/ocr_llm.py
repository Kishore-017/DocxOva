from unittest import result

import easyocr
import cv2
import re
import requests
import json

# -----------------------------
# GROQ API KEY (PASTE YOUR KEY)
# -----------------------------
GROQ_API_KEY = "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"

# -------- OCR SETUP --------
reader = easyocr.Reader(['en'])

# -------- DOCUMENT FIELD MAP --------
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

# -------- REGEX PATTERNS --------
patterns = {
    "DOB": r"\d{2}[./-]\d{2}[./-]\d{4}",
    "Aadhaar Number": r"\d{4}\s\d{4}\s\d{4}",
    "PAN Number": r"[A-Z]{5}[0-9]{4}[A-Z]",
    "License Number": r"[A-Z0-9]{6,}",
    "Passport Number": r"[A-Z][0-9]{7}",
    "Invoice Number": r"INV[- ]?\d+",
    "Account Number": r"\d{9,18}",
    "Amount": r"\d+\.\d{2}",
    "Date": r"\d{2}[/-]\d{2}[/-]\d{4}",
    "Age": r"\d+\s?(years|yrs)?",
    "Register Number": r"[A-Z0-9]{6,}",
    "ID Number": r"[A-Z0-9]{6,}"
}

# -------- DOCUMENT TYPE DETECTION --------
def detect_document_type(text):

    text = text.upper()

    if "AADHAAR" in text:
        return "Aadhaar Card"
    elif "INCOME TAX" in text or "PAN" in text:
        return "PAN Card"
    elif "DRIVING" in text:
        return "Driving License"
    elif "PASSPORT" in text:
        return "Passport"
    elif "INVOICE" in text:
        return "Invoice"
    elif "ACCOUNT" in text and "STATEMENT" in text:
        return "Bank Statement"
    elif "MARKSHEET" in text:
        return "Marksheet"
    elif "AGREEMENT" in text:
        return "Agreement"
    elif "REPORT" in text or "PATIENT" in text:
        return "Medical Report"
    else:
        return "ID Card"

# -------- NAME DETECTION --------
def detect_name(text_list):

    ignore_words = [
        "INCOME TAX", "DEPARTMENT", "GOVT", "INDIA",
        "ACCOUNT", "NUMBER", "SIGNATURE"
    ]

    for text in text_list:

        t = text.upper()

        # skip header words
        if any(word in t for word in ignore_words):
            continue

        # detect person name (two words)
        if re.match(r'^[A-Z]{3,}\s[A-Z]{3,}$', t):
            return text.title()

    return None

# -------- FIELD EXTRACTION --------
def extract_fields(text, text_list, doc_type):

    extracted = {}

    fields = document_fields[doc_type]

    for field in fields:

        if field in ["Name","Student Name","Patient Name","Party Names"]:
            extracted[field] = detect_name(text_list)

        else:
            pattern = patterns.get(field)

            if pattern:
                match = re.search(pattern, text)

                if match:
                    extracted[field] = match.group()
                else:
                    extracted[field] = None

    return extracted

# -------- AI FALLBACK USING GROQ --------
def llm_extract(text):

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
Extract document details from this OCR text.

Supported documents:
Aadhaar Card: Name, DOB, Aadhaar Number
PAN Card: Name, PAN Number, DOB
Driving License: Name, DOB, License Number
Passport: Name, Passport Number, DOB
Invoice: Invoice Number, Date, Amount
Bank Statement: Account Number, Date, Balance
Medical Report: Patient Name, Age, Diagnosis
Marksheet: Student Name, Register Number, Marks
Agreement: Party Names, Date
ID Card: Name, ID Number, DOB

Return JSON only.

TEXT:
{text}
"""

    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    result = response.json()

    print("\nDEBUG API RESPONSE:\n")
    print(result)

    if "choices" in result:
        return result["choices"][0]["message"]["content"]
    else:
        return "LLM API failed"

# -------- MAIN PROGRAM --------

image_path = input("Enter image path: ")

image = cv2.imread(image_path)

results = reader.readtext(image)

text_list = [res[1] for res in results]

text = " ".join(text_list)

# detect document
doc_type = detect_document_type(text)

# extract fields
data = extract_fields(text, text_list, doc_type)

print("\nDetected Document Type:", doc_type)

# Create JSON structure
output = {
    "Document Type": doc_type,
    "Extracted Data": data
}

# Print JSON nicely
print("\nJSON Output:\n")
print(json.dumps(output, indent=4))

# Save JSON to file
with open("output.json", "w") as f:
    json.dump(output, f, indent=4)

print("\nSaved to output.json")

# check missing values
missing = [k for k,v in data.items() if v is None]

if missing:
    print("\n⚡ OCR uncertain → Using AI fallback...\n")

    ai_result = llm_extract(text)

    print("AI Corrected Output:\n")
    print(ai_result)