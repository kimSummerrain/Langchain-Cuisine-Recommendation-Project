import os
from flask import Flask
from flask_cors import CORS  
from dotenv import load_dotenv
from app.routes import bp

load_dotenv()

app = Flask(__name__)
CORS(app)  

app.register_blueprint(bp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
