from flask import Flask
from flask_mysqldb import MySQL
from flask_cors import CORS
from flask_jwt_extended import JWTManager

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'your_secret_key'


@app.teardown_appcontext
def close_connection(exception):
    try:
        pass
    except Exception as e:
        app.logger.warning(f"Error during MySQL connection teardown: {str(e)}")



# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234567890'
app.config['MYSQL_DB'] = 'pinnacle_app'

mysql = MySQL(app)

