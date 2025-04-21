from datetime import datetime, timedelta
from firestore import FirestoreDB
from utils.response_wrapper import response_wrapper
import bcrypt

db = FirestoreDB()
COMPANY_COLLECTION = "companies"

# ---------- Helpers ----------
def get_ist_time():
    return (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")

def get_next_company_id():
    try:
        companies = db.get_all_documents(COMPANY_COLLECTION)

        if not companies:
            return "PEPRE-1000"
        
        company_numbers = []
        for company in companies:
            if "id" in company and company["id"].startswith("PEPRE-"):
                try:
                    num = int(company["id"][6:])
                    company_numbers.append(num)
                except ValueError:
                    continue
        
        if not company_numbers:
            return "PEPRE-1000"
        
        next_number = max(company_numbers) + 1
        return f"PEPRE-{next_number}"
    except Exception as e:
        print(f"Error generating company ID: {str(e)}")
        return "PEPRE-1000"

# ---------- Add Company ----------
def add_company(data):
    try:
        required_fields = ["companyName", "companySize", "adminEmail", "password"]
        if not data:
            return response_wrapper(400, "No data provided", None)

        missing_fields = [f for f in required_fields if f not in data or not data[f]]
        if missing_fields:
            return response_wrapper(400, f"Missing required fields: {', '.join(missing_fields)}", None)

        existing_companies = db.get_documents_by_field(COMPANY_COLLECTION, "adminEmail", data["adminEmail"])
        if existing_companies:
            return response_wrapper(400, "Company with this adminEmail already exists", None)

        company_id = get_next_company_id()

        hashed_password = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        company_data = {
            "id": company_id,
            "companyName": data["companyName"],
            "companySize": data["companySize"],
            "adminEmail": data["adminEmail"],
            "password": hashed_password,
            "created_at": get_ist_time(),
            "updated_at": get_ist_time()
        }

        optional_fields = ["adminName", "address", "phone_number", "industry", "website"]
        for field in optional_fields:
            if field in data:
                company_data[field] = data[field]

        db.add_document(COMPANY_COLLECTION, company_id, company_data)

        # Remove password from response
        company_data.pop("password", None)

        return response_wrapper(201, "Company registered successfully", company_data)

    except Exception as e:
        return response_wrapper(500, f"Error creating company: {str(e)}", None)

# ---------- Login ----------
def login_company(email, password):
    try:
        if not email or not password:
            return response_wrapper(400, "Email and password required", None)

        matching = db.get_documents_by_field(COMPANY_COLLECTION, "adminEmail", email)
        if not matching:
            return response_wrapper(404, "Company not found", None)

        company = matching[0]

        if not bcrypt.checkpw(password.encode("utf-8"), company["password"].encode("utf-8")):
            return response_wrapper(401, "Invalid password", None)

        # Return company details without password
        company.pop("password", None)
        return response_wrapper(200, "Login successful", company)

    except Exception as e:
        return response_wrapper(500, f"Error during login: {str(e)}", None)

# ---------- Fetch / Update / Delete ----------
def get_company(company_id):
    try:
        if not company_id:
            return response_wrapper(400, "Company ID is required", None)
        company = db.get_document(COMPANY_COLLECTION, company_id)
        if not company:
            return response_wrapper(404, "Company not found", None)
        company.pop("password", None)
        return response_wrapper(200, "Company details fetched", company)
    except Exception as e:
        return response_wrapper(500, f"Error fetching company: {str(e)}", None)

def get_all_companies():
    try:
        companies = db.get_all_documents(COMPANY_COLLECTION)
        for c in companies:
            c.pop("password", None)
        return response_wrapper(200, "All companies fetched", companies)
    except Exception as e:
        return response_wrapper(500, f"Error fetching all companies: {str(e)}", None)

def update_company(company_id, data):
    try:
        if not company_id:
            return response_wrapper(400, "Company ID is required", None)

        existing = db.get_document(COMPANY_COLLECTION, company_id)
        if not existing:
            return response_wrapper(404, "Company not found", None)

        if "adminEmail" in data and data["adminEmail"] != existing["adminEmail"]:
            duplicates = db.get_documents_by_field(COMPANY_COLLECTION, "adminEmail", data["adminEmail"])
            if any(d["id"] != company_id for d in duplicates):
                return response_wrapper(400, "Email already in use by another company", None)

        data["updated_at"] = get_ist_time()

        db.update_document(COMPANY_COLLECTION, company_id, data)
        updated = db.get_document(COMPANY_COLLECTION, company_id)
        updated.pop("password", None)

        return response_wrapper(200, "Company updated successfully", updated)
    except Exception as e:
        return response_wrapper(500, f"Error updating company: {str(e)}", None)

def delete_company(company_id):
    try:
        if not company_id:
            return response_wrapper(400, "Company ID is required", None)

        if not db.get_document(COMPANY_COLLECTION, company_id):
            return response_wrapper(404, "Company not found", None)

        db.delete_document(COMPANY_COLLECTION, company_id)
        return response_wrapper(200, "Company deleted successfully", {"id": company_id})
    except Exception as e:
        return response_wrapper(500, f"Error deleting company: {str(e)}", None)

# ---------- Filter / Search ----------
def search_companies(query, field="companyName"):
    try:
        if not query:
            return response_wrapper(400, "Search query is required", None)
        companies = db.get_all_documents(COMPANY_COLLECTION)
        filtered = [c for c in companies if field in c and query.lower() in str(c[field]).lower()]
        for c in filtered:
            c.pop("password", None)
        return response_wrapper(200, f"Found {len(filtered)} matching companies", filtered)
    except Exception as e:
        return response_wrapper(500, f"Error searching companies: {str(e)}", None)

def get_companies_by_size(size):
    try:
        if not size:
            return response_wrapper(400, "Company size is required", None)
        companies = db.get_all_documents(COMPANY_COLLECTION)
        filtered = [c for c in companies if c.get("companySize", "").lower() == size.lower()]
        for c in filtered:
            c.pop("password", None)
        return response_wrapper(200, f"Found {len(filtered)} companies of size '{size}'", filtered)
    except Exception as e:
        return response_wrapper(500, f"Error filtering companies: {str(e)}", None)

def verify_company_exists(company_id):
    try:
        company = db.get_document(COMPANY_COLLECTION, company_id)
        return response_wrapper(200, "Company exists" if company else "Company does not exist", {"exists": bool(company)})
    except Exception as e:
        return response_wrapper(500, f"Error verifying company: {str(e)}", None)
