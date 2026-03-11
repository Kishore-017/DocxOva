import easyocr
import cv2
import re


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
    "License Number": r"[A-Z0-9]{10,}",
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

    elif "DRIVING" in text or "DL" in text:
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

    for text in text_list:

        if re.match(r'^[A-Z. ]+$', text):

            if not any(word in text for word in ["COLLEGE","GOVERNMENT","INDIA","INVOICE","ACCOUNT","REPORT","MARKSHEET"]):

                if len(text) > 4:

                    name = text.split(".")[0].title()
                    return name

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

    return extracted

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
print("\nExtracted Data:\n")

for key, value in data.items():
    print(f"{key}: {value}")