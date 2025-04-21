from flask import Blueprint, request, jsonify
from api.service import (
    add_company,
    get_company,
    get_all_companies,
    update_company,
    delete_company,
    search_companies,
    get_companies_by_size,
    verify_company_exists
)
from utils.response_wrapper import response_wrapper

company_blueprint = Blueprint("company", __name__)


@company_blueprint.route("/register", methods=["POST"])
def create_company():
    """Create a new company"""
    try:
        data = request.get_json()
        if not data:
            return response_wrapper(400, "Invalid JSON or no data provided", None)
            
        # add_company already returns the response_wrapper tuple
        return add_company(data)
        
    except Exception as e:
        error_message = f"Error in create_company: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)


@company_blueprint.route("/<company_id>", methods=["GET"])
def fetch_company(company_id):
    """Fetch a single company by ID"""
    try:
        # get_company already returns the response_wrapper tuple
        return get_company(company_id)
        
    except Exception as e:
        error_message = f"Error in fetch_company: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)


@company_blueprint.route("/<company_id>", methods=["PUT"])
def update_company_route(company_id):
    """Update a company's information"""
    try:
        data = request.get_json()
        if not data:
            return response_wrapper(400, "Invalid JSON or no data provided", None)
            
        # update_company already returns the response_wrapper tuple
        return update_company(company_id, data)
        
    except Exception as e:
        error_message = f"Error in update_company_route: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)


@company_blueprint.route("/<company_id>", methods=["DELETE"])
def delete_company_route(company_id):
    """Delete a company"""
    try:
        # delete_company already returns the response_wrapper tuple
        return delete_company(company_id)
        
    except Exception as e:
        error_message = f"Error in delete_company_route: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)


@company_blueprint.route("/all", methods=["GET"])
def fetch_all_companies():
    """Fetch all companies"""
    try:
        # get_all_companies already returns the response_wrapper tuple
        return get_all_companies()
        
    except Exception as e:
        error_message = f"Error in fetch_all_companies: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)


@company_blueprint.route("/verify", methods=["GET"])
def check_company_exists():
    """Verify if a company exists"""
    try:
        company_id = request.args.get("id")
        if not company_id:
            return response_wrapper(400, "Company ID is required", None)

        # verify_company_exists already returns the response_wrapper tuple
        return verify_company_exists(company_id)
        
    except Exception as e:
        error_message = f"Error in check_company_exists: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)


@company_blueprint.route("/search", methods=["GET"])
def search_companies_route():
    """Search for companies by name, email, or other fields"""
    try:
        query = request.args.get("q", "")
        field = request.args.get("field", "name")  # Default search by name
        
        if not query:
            return response_wrapper(400, "Search query is required", None)
        
        # search_companies already returns the response_wrapper tuple
        return search_companies(query, field)
        
    except Exception as e:
        error_message = f"Error in search_companies_route: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)


@company_blueprint.route("/size/<size>", methods=["GET"])
def get_companies_by_size_route(size):
    """Get companies by size"""
    try:
        # get_companies_by_size already returns the response_wrapper tuple
        return get_companies_by_size(size)
        
    except Exception as e:
        error_message = f"Error in get_companies_by_size_route: {str(e)}"
        print(error_message)
        return response_wrapper(500, error_message, None)