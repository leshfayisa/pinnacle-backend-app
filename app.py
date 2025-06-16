from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os
from register_routes import register_all_blueprints

load_dotenv()

app = Flask(__name__)
CORS(app)

# Load config from environment
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')

# Register all blueprints
register_all_blueprints(app)

if __name__ == "__main__":
    app.run(debug=True)
