from flask import request, jsonify, current_app
from db_config import get_db_connection
from authentication.hash_password import hash_password, verify_password
from authentication.token_generator import generate_token
from . import auth_bp
import pymysql

@auth_bp.route('/signin', methods=["POST"])
def sign_in():
    """
    Sign in a user using username and password.

    Accepts a JSON payload with 'username' and 'password', validates the credentials,
    and returns a JWT token on success.

    Returns:
        200 OK: Login successful, returns user ID, role, and JWT token.
        400 Bad Request: Missing input data.
        401 Unauthorized: Invalid username or password.
        500 Internal Server Error: Database or internal error.
    """

    data = request.get_json()
    if not data:
        return jsonify({'message': "Please provide username and password"}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': "Username and password are required"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': "Database connection error"}), 500

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:  # Ensure DictCursor is used
            cursor.execute("SELECT id, password_hash, role FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()

        if not user:
            return jsonify({'message': "Invalid username or password"}), 401


        user_id = user['id']
        stored_password = user['password_hash']
        role = user['role']

        # Verify the provided password
        if not verify_password(stored_password, password):
            return jsonify({'message': "Invalid username or password"}), 401

        # Generate a token with expiration
        token = generate_token(user_id, role, current_app.config['SECRET_KEY'], expires_in_hours=2)

        return jsonify({
            'message': "Logged in successfully",
            'user': {
                'id': user_id,
                'role': role
            },
            'token': token
        }), 200

    except pymysql.MySQLError as db_err:
        return jsonify({'message': f"Database error: {str(db_err)}"}), 500

    except Exception as e:
        return jsonify({'message': f"Internal error: {str(e)}"}), 500

    finally:
        conn.close()



@auth_bp.route('/signup', methods=["POST"])
def sign_up():
    """
    Register a new user.

    Accepts a JSON payload with 'username', 'password', and optional 'role' (default: 'user').
    Hashes the password and stores the new user in the database.

    Returns:
        201 Created: User registered successfully.
        400 Bad Request: Missing required fields.
        409 Conflict: User already exists.
        500 Internal Server Error: Database or internal error.
    """

    data = request.get_json()
    if not data:
        return jsonify({'message': "No input data provided"}), 400

    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')  # Default role is 'user'

    if not username or not password:
        return jsonify({'message': "Username and password are required"}), 400

    # Hash the password
    hashed_password = hash_password(password)

    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': "Database connection error"}), 500

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                (username, hashed_password, role)
            )
            conn.commit()
        
        return jsonify({
            "message": "User successfully registered",
            "user": {
                "username": username,
                "role": role
            }
        }), 201

    except pymysql.IntegrityError:
        return jsonify({"message": "User already exists"}), 409  # Handle duplicate entry

    except pymysql.MySQLError as db_err:
        return jsonify({"message": f"Database error: {str(db_err)}"}), 500

    except Exception as e:
        return jsonify({"message": f"Internal error: {str(e)}"}), 500

    finally:
        conn.close()
