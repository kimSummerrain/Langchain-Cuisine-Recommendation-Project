from flask import Flask
from dotenv import load_dotenv
import os

def create_app():
    load_dotenv()
    app = Flask(__name__)
    
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app