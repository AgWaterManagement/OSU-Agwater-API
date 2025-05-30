from flask import Flask, request
from routes import articles_bp, data_bp, energy_bp, email_bp, llm_bp
from config import config_by_name
#from dotenv import load_dotenv
import logging
import os

# Load environment variables from .env file
#load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Load configuration based on the environment
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config_by_name[env])

# Set up logging
logging.basicConfig(
    filename='app.log',  # Log file name
    level=logging.INFO,  # Log level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)
logger = logging.getLogger(__name__)

# Middleware to log each API call
@app.before_request
def log_request_info():
    logger.info(
        f"API Call: {request.method} {request.path} | "
        f"Parameters: {request.args.to_dict()} | "
        f"Body: {request.get_json(silent=True)}"
    )

# Register blueprints
app.register_blueprint(articles_bp)
app.register_blueprint(data_bp)
app.register_blueprint(energy_bp)
app.register_blueprint(email_bp)
app.register_blueprint(llm_bp)

if __name__ == "__main__":
    app.run()
