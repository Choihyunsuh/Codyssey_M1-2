"""Import the included CSV once into Firestore. Run from the repository root."""
import csv
import json
import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore

raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
if not raw:
    raise SystemExit("Set FIREBASE_SERVICE_ACCOUNT_JSON before importing data.")
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(json.loads(raw)))
db = firestore.client()
path = Path(__file__).resolve().parents[1] / "data" / "usd_krw_2025.csv"
batch = db.batch()
count = 0
with path.open(encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        ref = db.collection("data").document(row["date"])
        batch.set(ref, {"date": row["date"], "value": float(row["value"]), "memo": row["memo"]})
        count += 1
        if count % 400 == 0:
            batch.commit()
            batch = db.batch()
if count % 400:
    batch.commit()
print(f"Imported {count} USD/KRW observations.")
