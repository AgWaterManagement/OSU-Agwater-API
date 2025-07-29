from flask import Flask, request
import os
from routes import misc_bp, email_bp, agrimet_bp, llm_bp, articles_bp, data_bp, cms_bp
from config import config_by_name
from dotenv import load_dotenv
import globals

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Load configuration based on the environment
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config_by_name[env])

# Initialize globals (including loggers)
globals.init()

# Middleware to log each API call
@app.before_request
def log_request_info():
    globals.main_logger.info(
        f"API Call: {request.method} {request.path} | "
        f"Parameters: {request.args.to_dict()} | "
        f"Body: {request.get_json(silent=True)}"
    )


# Register blueprints
app.register_blueprint(articles_bp)
app.register_blueprint(data_bp)
#app.register_blueprint(energy_bp)
app.register_blueprint(email_bp)
app.register_blueprint(llm_bp)
app.register_blueprint(misc_bp)
app.register_blueprint(cms_bp)
app.register_blueprint(agrimet_bp)

@app.route('/')
def index():
    return "Welcome to the Ag Water API!"

if __name__ == "__main__":
    app.run(debug=False)
