import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Get the absolute path to the project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  

# Update the path to the service account key
FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, "serviceAccountKey.json")

# Check if credentials are provided as an environment variable
FIREBASE_CREDENTIALS_JSON = os.environ.get("FIREBASE_CREDENTIALS_JSON")

try:
    if FIREBASE_CREDENTIALS_JSON:
        cred_dict = json.loads(FIREBASE_CREDENTIALS_JSON)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    elif os.path.exists(FIREBASE_CREDENTIALS_PATH):
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
    else:
        raise FileNotFoundError(f"Firebase credentials file not found: {FIREBASE_CREDENTIALS_PATH}")

    db = firestore.client()
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    raise
