# import Blueprints
#from .articles import bp as articles_bp
from .data import bp as data_bp
from .energy import bp as energy_bp
from .email import bp as email_bp

# Expose blueprints for easy import in app.py
__all__ = ['articles_bp', 'data_bp', 'energy_bp', 'email_bp']
