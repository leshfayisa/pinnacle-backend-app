import pymysql
from flask import current_app

# Use PyMySQL
pymysql.install_as_MySQLdb()

def get_db_connection():
    try:
        conn = pymysql.connect(
            host=current_app.config['MYSQL_HOST'],
            user=current_app.config['MYSQL_USER'],
            password=current_app.config['MYSQL_PASSWORD'],
            database=current_app.config['MYSQL_DB'],
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except pymysql.MySQLError as e:
        print(f"Database connection error: {str(e)}")
        return None
