from datetime import datetime
from firestore import FirestoreDB
from utils.response_wrapper import response_wrapper

db = FirestoreDB()
COMPANY_COLLECTION = "companies"

def get_next_company_id():
    """Fetch the next sequential company ID in PEPRE-XXXX format"""
    try:
        companies = db.get_all_documents(COMPANY_COLLECTION)
        
        if not companies:
            return "PEPRE-1000"  # Start with PEPRE-1000 if no companies exist
        
        # Extract numeric part from PEPRE-XXXX format and find the max
        company_numbers = []
        for company in companies:
            if "id" in company and company["id"].startswith("PEPRE-"):
                try:
                    num = int(company["id"][6:])  # Extract the number after "PEPRE-"
                    company_numbers.append(num)
                except ValueError:
                    # Skip if not in the expected format
                    continue
        
        if not company_numbers:
            return "PEPRE-1000"  # Start with PEPRE-1000 if no valid IDs found
            
        next_number = max(company_numbers) + 1
        return f"PEPRE-{next_number}"  # Format as PEPRE-1001, PEPRE-1002, etc.
    except Exception as e:
        print(f"Error generating company ID: {str(e)}")
        return "PEPRE-1000"  # Fallback to default if error occurs

def add_company(data):
    """Create a new company"""
    try:
        required_fields = ["name", "size", "email"]

        if not data:
            return response_wrapper(400, "No data provided", None)
            
        # Check for missing fields
        missing_fields = [field for field in required_fields if field not in data or data[field] in [None, ""]]
        if missing_fields:
            return response_wrapper(400, f"Missing required fields: {', '.join(missing_fields)}", None)

        email = data["email"]

        # Check if company already exists with this email
        existing_companies = db.get_documents_by_field(COMPANY_COLLECTION, "email", email)
        if existing_companies:
            return response_wrapper(400, "Company with this email already exists", None)

        # Generate a unique company ID
        company_id = get_next_company_id()
        
        # Create company data
        company_data = {
            "id": company_id,
            "name": data["name"],
            "size": data["size"],
            "email": email,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Add optional fields if they exist
        if "admin_name" in data:
            company_data["admin_name"] = data["admin_name"]
        if "address" in data:
            company_data["address"] = data["address"]
        if "phone_number" in data:
            company_data["phone_number"] = data["phone_number"]
        if "industry" in data:
            company_data["industry"] = data["industry"]
        if "website" in data:
            company_data["website"] = data["website"]

        # Add the document with company_id as the document ID
        db.add_document(COMPANY_COLLECTION, company_id, company_data)
        
        return response_wrapper(201, "Company registered successfully", company_data)
    
    except Exception as e:
        error_message = f"Error creating company: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)

def get_company(company_id):
    """Fetch company by ID"""
    try:
        if not company_id:
            return response_wrapper(400, "Company ID is required", None)

        company = db.get_document(COMPANY_COLLECTION, company_id)
        if not company:
            return response_wrapper(404, "Company not found", None)

        return response_wrapper(200, "Company details fetched", company)
    
    except Exception as e:
        error_message = f"Error fetching company: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)

def get_all_companies():
    """Fetch all companies"""
    try:
        companies = db.get_all_documents(COMPANY_COLLECTION)
        return response_wrapper(200, "All companies fetched", companies)
    
    except Exception as e:
        error_message = f"Error fetching all companies: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)

def update_company(company_id, data):
    """Update an existing company"""
    try:
        if not company_id:
            return response_wrapper(400, "Company ID is required", None)
            
        # Check if company exists
        existing_company = db.get_document(COMPANY_COLLECTION, company_id)
        if not existing_company:
            return response_wrapper(404, "Company not found", None)
            
        # Check if email is being updated and is already in use by another company
        if "email" in data and data["email"] != existing_company["email"]:
            existing_emails = db.get_documents_by_field(COMPANY_COLLECTION, "email", data["email"])
            for comp in existing_emails:
                if comp["id"] != company_id:  # If email belongs to a different company
                    return response_wrapper(400, "Email already in use by another company", None)
        
        # Add last updated timestamp
        data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update company data
        db.update_document(COMPANY_COLLECTION, company_id, data)
        
        # Fetch updated company data
        updated_company = db.get_document(COMPANY_COLLECTION, company_id)
        
        return response_wrapper(200, "Company updated successfully", updated_company)
    
    except Exception as e:
        error_message = f"Error updating company: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)

def delete_company(company_id):
    """Delete a company"""
    try:
        if not company_id:
            return response_wrapper(400, "Company ID is required", None)
            
        # Check if company exists
        company = db.get_document(COMPANY_COLLECTION, company_id)
        if not company:
            return response_wrapper(404, "Company not found", None)
            
        # Delete the company
        db.delete_document(COMPANY_COLLECTION, company_id)
        
        return response_wrapper(200, "Company deleted successfully", {"id": company_id})
    
    except Exception as e:
        error_message = f"Error deleting company: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)

def search_companies(query, field="name"):
    """Search for companies by field"""
    try:
        if not query:
            return response_wrapper(400, "Search query is required", None)
            
        companies = db.get_all_documents(COMPANY_COLLECTION)
        
        filtered_companies = []
        for company in companies:
            if field in company and query.lower() in str(company[field]).lower():
                filtered_companies.append(company)
        
        return response_wrapper(200, f"Found {len(filtered_companies)} matching companies", filtered_companies)
    
    except Exception as e:
        error_message = f"Error searching companies: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)

def get_companies_by_size(size):
    """Get companies by size"""
    try:
        if not size:
            return response_wrapper(400, "Company size is required", None)
            
        companies = db.get_all_documents(COMPANY_COLLECTION)
        filtered_companies = [comp for comp in companies if comp.get("size", "").lower() == size.lower()]
        
        return response_wrapper(200, f"Found {len(filtered_companies)} companies of size '{size}'", 
                            filtered_companies)
    
    except Exception as e:
        error_message = f"Error fetching companies by size: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)

def verify_company_exists(company_id):
    """Check if a company exists"""
    try:
        company = db.get_document(COMPANY_COLLECTION, company_id)
        return response_wrapper(200, "Company exists" if company else "Company does not exist",
                              {"exists": bool(company)})
    
    except Exception as e:
        error_message = f"Error verifying company: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)