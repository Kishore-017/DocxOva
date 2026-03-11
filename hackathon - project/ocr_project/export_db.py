from pymongo import MongoClient
import pandas as pd
import os

client = MongoClient("mongodb+srv://Kishore:Kishore17@cluster3.clomoi7.mongodb.net/?appName=Cluster3")

db = client["DocxOva_App"]
collection = db["Results"]

data = list(collection.find())

rows = []

for doc in data:

    doc_info = doc.get("document_info", {})

    row = {
        "Document Type": doc_info.get("type", ""),
        "File Name": doc_info.get("filename", ""),
        "Processed Time": doc_info.get("processed_at", "")
    }

    extracted = doc.get("extracted_data", [])

    for field in extracted:
        field_name = field.get("field", "")
        field_value = field.get("original", "")
        row[field_name] = field_value

    rows.append(row)

df = pd.DataFrame(rows)

print("Documents exported:", len(df))

# remove old file if exists
if os.path.exists("ocr_database.xlsx"):
    os.remove("ocr_database.xlsx")

df.to_excel("ocr_database.xlsx", index=False)

print("✅ Excel export completed")