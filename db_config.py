import os
import pymysql
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Flask with environment variables
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')

# Use PyMySQL
pymysql.install_as_MySQLdb()

# Database Connection Function
def get_db_connection():
    try:
        conn = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB'],
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except pymysql.MySQLError as e:
        print(f"Database connection error: {str(e)}")
        return None
