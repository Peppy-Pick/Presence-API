from flask import Flask
from flask_restful import Api
from api.controller import company_blueprint  # Import the new company blueprint
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
api = Api(app)

# Register Blueprints
app.register_blueprint(company_blueprint, url_prefix="/api/company")  # Register the company blueprint

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)