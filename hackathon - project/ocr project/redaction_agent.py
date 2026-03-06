import re
import json
import os
import bcrypt

# -------- REGEX PATTERNS --------
phone_pattern = r'\b\d{10}\b'
email_pattern = r'\b[\w\.-]+@[\w\.-]+\.\w+\b'
aadhaar_pattern = r'\b\d{4}\s\d{4}\s\d{4}\b'
pan_pattern = r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'
date_pattern = r'\b\d{2}[/-]\d{2}[/-]\d{4}\b'

# -------- HASH FUNCTION --------
def hash_sensitive_data(data):
    salt = bcrypt.gensalt(rounds=10)
    hashed = bcrypt.hashpw(data.encode(), salt)
    return hashed.decode()

# -------- REDACTION FUNCTION --------
def redact_text(text):

    detected_entities = []

    patterns = [
        ("PHONE", phone_pattern, "XXXXXXXXXX"),
        ("EMAIL", email_pattern, "XXXX@XXXX.com"),
        ("AADHAAR", aadhaar_pattern, "XXXX XXXX XXXX"),
        ("PAN", pan_pattern, "XXXXXXXXXX"),
        ("DATE", date_pattern, "XX/XX/XXXX")
    ]

    for label, pattern, mask in patterns:

        matches = re.findall(pattern, text)

        for match in matches:

            hashed_value = hash_sensitive_data(match)

            detected_entities.append({
                "type": label,
                "original_value": match,
                "hashed_value": hashed_value
            })

            text = text.replace(match, mask)

    return text, detected_entities


# -------- DOCUMENT PROCESSING --------
def redact_document(ocr_output):

    final_output = []

    for block in ocr_output:

        original_text = block["text"]

        redacted_text, entities = redact_text(original_text)

        final_output.append({
            "original_text": original_text,
            "redacted_text": redacted_text,
            "detected_entities": entities
        })

    return final_output


# -------- MAIN PROGRAM --------
if __name__ == "__main__":

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    input_path = os.path.join(BASE_DIR, "output.json")

    with open(input_path, "r", encoding="utf-8") as f:
        ocr_data = json.load(f)

    # Convert OCR format
    ocr_output = []

for key, value in ocr_data["Extracted Data"].items():
    ocr_output.append({"text": str(value)})

    # Run redaction
    final_result = redact_document(ocr_output)

    # Save output
    output_path = os.path.join(BASE_DIR, "redacted_output.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_result, f, indent=2)

print("\n✅ Redaction Completed Successfully!\n")

for item in final_result:

    print("Original :", item["original_text"])
    print("Redacted :", item["redacted_text"])

    print("Detected Entities:")

    for ent in item["detected_entities"]:

        print("  Type :", ent["type"])
        print("  Original :", ent["original_value"])

        if "hashed_value" in ent:
            print("  Hashed :", ent["hashed_value"])

        print()

    print("-" * 50)