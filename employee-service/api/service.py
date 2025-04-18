import bcrypt
import string
import random
from datetime import datetime
from firestore import FirestoreDB
from utils.response_wrapper import response_wrapper

db = FirestoreDB()
EMPLOYEE_COLLECTION = "employees"


def generate_unique_password(length=8):
    """
    Generate a unique, secure password with exactly:
    - 1 number
    - 1 capital letter
    - 1 special character (only @, $, *, or -)
    - Total length of 8 characters
    """
    # Define character sets for password
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special_chars = "@$*-"  # Only these special characters are allowed
    
    # Ensure password has at least one character from each required set
    password = [
        random.choice(uppercase),    # 1 capital letter
        random.choice(digits),       # 1 number
        random.choice(special_chars) # 1 special character
    ]
    
    # Fill the rest of the password with lowercase letters
    password.extend(random.choice(lowercase) for _ in range(length - 3))
    
    # Shuffle the password characters to randomize positions
    random.shuffle(password)
    
    # Convert list to string
    return ''.join(password)

def get_next_employee_id():
    """Fetch the next sequential employee ID"""
    try:
        employees = db.get_all_documents(EMPLOYEE_COLLECTION)
        
        if not employees:
            return "EMP001"  # Start with EMP001 if no employees exist
        
        # Extract numeric part from EMP*** format and find the max
        emp_numbers = []
        for emp in employees:
            if "id" in emp and emp["id"].startswith("EMP"):
                try:
                    num = int(emp["id"][3:])  # Extract the number after "EMP"
                    emp_numbers.append(num)
                except ValueError:
                    # Skip if not in the expected format
                    continue
        
        if not emp_numbers:
            return "EMP001"  # Start with EMP001 if no valid IDs found
            
        next_number = max(emp_numbers) + 1
        return f"EMP{next_number:03d}"  # Format as EMP001, EMP002, etc.
    except Exception as e:
        # Better error handling - return error details
        print(f"Error generating employee ID: {str(e)}")
        return "EMP001"  # Fallback to default if error occurs

def add_employee(data):
    """Register a new employee with fixed 'admin' password"""
    try:
        # Update the required fields list to match your current needs
        required_fields = ["name", "date_of_birth", "email", "address", 
                           "phone_number", "designation", "employee_shift_hours"]

        if not data:
            return response_wrapper(400, "No data provided", None)
            
        # Check for missing fields more safely
        missing_fields = [field for field in required_fields if field not in data or data[field] in [None, ""]]
        if missing_fields:
            return response_wrapper(400, f"Missing required fields: {', '.join(missing_fields)}", None)

        email = data["email"]

        # Check if employee already exists with this email
        existing_employees = db.get_documents_by_field(EMPLOYEE_COLLECTION, "email", email)
        if existing_employees:
            return response_wrapper(400, "Employee with this email already exists", None)

        # Generate a unique employee ID
        employee_id = get_next_employee_id()
        
        # Use fixed password 'admin' instead of generating
        raw_password = "admin"
        
        # Hash the password before storing - with proper salt
        hashed_password = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # Create employee data with only the fields you need
        employee_data = {
            "id": employee_id,
            "name": data["name"],
            "date_of_birth": data["date_of_birth"],
            "email": email,
            "address": data["address"],
            "phone_number": data["phone_number"],
            "designation": data["designation"],
            "password": hashed_password,  # Store hashed password
            "employee_shift_hours": data["employee_shift_hours"],
            "created_at": datetime.utcnow().isoformat(),
            "last_login": None
        }

        # Optionally add these fields if they exist in the data
        if "age" in data:
            employee_data["age"] = data["age"]
        if "blood_type" in data:
            employee_data["blood_type"] = data["blood_type"]
        if "ctc" in data:
            employee_data["ctc"] = data["ctc"]

        # Add the document with employee_id as the document ID
        db.add_document(EMPLOYEE_COLLECTION, employee_id, employee_data)
        
        # Return the employee data with the standard password
        response_data = employee_data.copy()
        # Remove hashed password from response and add standard password
        del response_data["password"]
        response_data["password"] = "admin"
        return response_wrapper(201, "Employee registered successfully with standard password 'admin'", response_data)
    
    except Exception as e:
        # Better error handling with more detailed error message
        error_message = f"Error creating employee: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)
    
    
def update_employee(employee_id, data):
    """Update an existing employee"""
    try:
        if not employee_id:
            return response_wrapper(400, "Employee ID is required", None)
            
        # Check if employee exists
        existing_employee = db.get_document(EMPLOYEE_COLLECTION, employee_id)
        if not existing_employee:
            return response_wrapper(404, "Employee not found", None)
            
        # Check if email is being updated and is already in use by another employee
        if "email" in data and data["email"] != existing_employee["email"]:
            existing_emails = db.get_documents_by_field(EMPLOYEE_COLLECTION, "email", data["email"])
            for emp in existing_emails:
                if emp["id"] != employee_id:  # If email belongs to a different employee
                    return response_wrapper(400, "Email already in use by another employee", None)
        
        # Create a copy of the data for the response
        response_data = {}
                
        # Handle password update
        if "update_password" in data and data["update_password"] is True:
            # Set to standard 'admin' password instead of generating
            raw_password = "admin"
            hashed_password = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            data["password"] = hashed_password
            # Remove update_password flag as it's not needed in the database
            del data["update_password"]
            # Add the standard password to the response
            response_data["password"] = "admin"
        elif "password" in data:
            # If a specific password is provided, hash it
            if data["password"]:
                data["password"] = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            else:
                # If empty password is provided, remove it from the update
                del data["password"]
            
        # Add last updated timestamp
        data["updated_at"] = datetime.utcnow().isoformat()
        
        # Update employee data
        db.update_document(EMPLOYEE_COLLECTION, employee_id, data)
        
        # Fetch updated employee data
        updated_employee = db.get_document(EMPLOYEE_COLLECTION, employee_id)
        
        # Merge the updated employee with any response data (like password)
        response_data.update(updated_employee)
        
        return response_wrapper(200, "Employee updated successfully", response_data)
    
    except Exception as e:
        error_message = f"Error updating employee: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)

def login_employee(data):
    """Authenticate employee (Login)"""
    try:
        required_fields = ["email", "password"]

        if not data or not all(k in data for k in required_fields):
            return response_wrapper(400, "Email and password are required", None)

        email = data["email"]
        password = data["password"]

        # Fetch employee from Firestore by email
        employees = db.get_documents_by_field(EMPLOYEE_COLLECTION, "email", email)
        if not employees:
            return response_wrapper(401, "Invalid email or password", None)
        
        employee = employees[0]  # Use the first match (should be only one)
        stored_password = employee.get("password")
        
        # Check if stored_password exists
        if not stored_password:
            return response_wrapper(401, "Invalid password format", None)

        # Verify password with improved error handling
        try:
            # Make sure the stored hash is properly formatted for bcrypt
            if not stored_password.startswith('$2'):  # Check if it's a valid bcrypt hash format
                print("Invalid bcrypt hash format")
                return response_wrapper(401, "Invalid stored password format", None)
                
            is_valid = bcrypt.checkpw(password.encode("utf-8"), stored_password.encode("utf-8"))
            if not is_valid:
                return response_wrapper(401, "Invalid email or password", None)
        except ValueError as e:
            # This happens when the stored password is not in valid bcrypt format
            print(f"Password verification error: {str(e)}")
            return response_wrapper(401, "Password verification failed", None)
        except Exception as e:
            # Catch any other bcrypt-related errors
            print(f"Unexpected password verification error: {str(e)}")
            return response_wrapper(500, f"Password verification system error: {str(e)}", None)

        # Update last login time
        db.update_document(EMPLOYEE_COLLECTION, employee["id"], {"last_login": datetime.utcnow().isoformat()})

        return response_wrapper(200, "Login successful", employee)
    
    except Exception as e:
        error_message = f"Error during login: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)
        
def get_employee(employee_id):
    """Fetch employee by ID"""
    try:
        if not employee_id:
            return response_wrapper(400, "Employee ID is required", None)

        employee = db.get_document(EMPLOYEE_COLLECTION, employee_id)
        if not employee:
            return response_wrapper(404, "Employee not found", None)

        return response_wrapper(200, "Employee details fetched", employee)
    
    except Exception as e:
        error_message = f"Error fetching employee: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)


def get_all_employees():
    """Fetch all employees"""
    try:
        employees = db.get_all_documents(EMPLOYEE_COLLECTION)
        return response_wrapper(200, "All employees fetched", employees)
    
    except Exception as e:
        error_message = f"Error fetching all employees: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)


def verify_employee_exists(employee_id):
    """Check if an employee exists"""
    try:
        employee = db.get_document(EMPLOYEE_COLLECTION, employee_id)
        return response_wrapper(200, "Employee exists" if employee else "Employee does not exist",
                                {"exists": bool(employee)})
    
    except Exception as e:
        error_message = f"Error verifying employee: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)


def get_employees_by_designation(designation):
    """Get employees by designation/role"""
    try:
        if not designation:
            return response_wrapper(400, "Designation is required", None)
            
        employees = db.get_all_documents(EMPLOYEE_COLLECTION)
        filtered_employees = [emp for emp in employees if emp.get("designation", "").lower() == designation.lower()]
        
        return response_wrapper(200, f"Found {len(filtered_employees)} employees with designation '{designation}'", 
                            filtered_employees)
    
    except Exception as e:
        error_message = f"Error fetching employees by designation: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)


def delete_employee(employee_id):
    """Delete an employee"""
    try:
        if not employee_id:
            return response_wrapper(400, "Employee ID is required", None)
            
        # Check if employee exists
        employee = db.get_document(EMPLOYEE_COLLECTION, employee_id)
        if not employee:
            return response_wrapper(404, "Employee not found", None)
            
        # Delete the employee
        db.delete_document(EMPLOYEE_COLLECTION, employee_id)
        
        return response_wrapper(200, "Employee deleted successfully", {"id": employee_id})
    
    except Exception as e:
        error_message = f"Error deleting employee: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)