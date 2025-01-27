from flask import Flask, jsonify, request, current_app
import jwt
from db_config import app, mysql
from datetime import datetime, timedelta
from functools import wraps

from token_generator import generate_token, token_required
from hash_password import verify_password, hash_password_with_salt

@app.route("/")
def home():
    return "Welcome to Pinnacle App!"

@app.route('/api/signin', methods=["POST"])
def sign_in():
    data = request.get_json()
    if not data:
        return jsonify({'message': "Please provide username and password"}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': "Username and password are required"}), 400

    try:
        # Fetch user details from the database
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute("SELECT id, password_hash, role FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()

        if not user:
            return jsonify({'message': "Incorrect username or password"}), 401

        user_id, stored_password, role = user

        # Verify the provided password
        if not verify_password(stored_password, password):
            return jsonify({'message': "Incorrect username or password"}), 401

        # Generate a token
        token = generate_token(user_id, role, app.config['SECRET_KEY'])

        return jsonify({'message': "Logged in successfully", 'user_id': user_id, 'role': role, 'token': token}), 200
    except Exception as e:
        return jsonify({'message': f"Internal error: {str(e)}"}), 500

@app.route('/api/signup', methods=["POST"])
def sign_up():
    data = request.get_json()
    if not data:
        return jsonify({'message': "No input data provided"}), 400

    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')  # Default role is 'user'

    if not username or not password:
        return jsonify({'message': "Username and password are required"}), 400

    # Hash the password
    hashed_password = hash_password_with_salt(password)

    try:
        # Insert the user into the database
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
            (username, hashed_password, role)
        )
        conn.commit()
        cursor.close()
        return jsonify({"message": "User successfully registered"}), 201
    except Exception as e:
        if "Duplicate entry" in str(e):
            return jsonify({"message": "User already exists"}), 409
        return jsonify({"message": f"Internal error: {str(e)}"}), 500   

@app.route('/api/reviews/<int:review_id>/status', methods=["PUT"])
@token_required
def update_review_status(current_user_id, review_id, current_user_role):
    # Check if the user has admin privileges
    if current_user_role != 'admin':
        return jsonify({
            'message': 'Admin access required',
            'userMessage': 'You do not have permission to perform this action.'
        }), 403

    data = request.get_json()
    new_status = data.get('status')

    if not new_status or new_status not in ['approved', 'rejected']:
        return jsonify({'message': 'Invalid status value'}), 400

    try:
        conn = mysql.connection
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE user_reviews SET status = %s, updated_time = NOW() WHERE id = %s",
            (new_status, review_id)
        )
        conn.commit()
        cursor.close()
        return jsonify({'message': f"Review status updated to {new_status}"}), 200
    except Exception as e:
        return jsonify({'message': f"Internal error: {str(e)}"}), 500

# Endpoint: Get Visitor Statistics
@app.route("/api/visitor-stats", methods=["GET"])
def get_visitor_stats():
    # Use mysql.connection
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM visitor_stats ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    cursor.close()
    if row:
        keys = ["id", "date", "visitors_today", "visitors_yesterday", "visitors_this_week", "visitors_this_month", "total_visitors", "currently_online"]
        return jsonify(dict(zip(keys, row)))
    return jsonify({"message": "No data available"}), 404

# Endpoint: Submit User Review
@app.route("/api/reviews", methods=["POST"])
def add_review():
    data = request.json
    name = data.get("name")
    review = data.get("review")
    rating = data.get("rating")

    # Validate input fields
    if not (name and review and rating):
        return jsonify({"message": "All fields are required"}), 400
    if not (isinstance(rating, int) and 1 <= rating <= 5):
        return jsonify({"message": "Rating must be an integer between 1 and 5"}), 400

    try:
        conn = mysql.connection
        cursor = conn.cursor()

        # Insert review with default 'pending' status
        query = """
        INSERT INTO user_reviews (name, review, rating, status)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (name, review, rating, 'pending'))
        conn.commit()  # Commit the transaction
        cursor.close()

        return jsonify({"message": "Review submitted successfully"}), 201
    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

@app.route("/api/reviews", methods=["GET"])
def get_reviews():
    # Default role is 'guest' for unauthenticated users
    current_user_role = 'guest'

    # Check for token in the Authorization header
    token = request.headers.get('Authorization')
    if token:
        try:
            # Extract token from "Bearer <token>" format
            token = token.split(" ")[1] if " " in token else token.strip()
            secret_key = current_app.config['SECRET_KEY']

            # Decode the token
            data = jwt.decode(token, secret_key, algorithms=['HS256'])
            current_user_role = data.get('role', 'guest')  # Extract role, default to 'guest'
        except jwt.ExpiredSignatureError:
            return jsonify({
                'message': 'Token has expired',
                'loginRequired': True,
                'userMessage': 'Please login to access this resource.'
            }), 403
        except jwt.InvalidTokenError:
            return jsonify({
                'message': 'Token is invalid',
                'loginRequired': True,
                'userMessage': 'Please login to access this resource.'
            }), 403

    try:
        # Read pagination parameters from request
        offset = request.args.get('offset', default=0, type=int)
        limit = request.args.get('limit', default=5, type=int)

        conn = mysql.connection
        cursor = conn.cursor()

        # Modify query based on user role
        if current_user_role == 'admin':
            # Admins see all reviews
            query = """
                SELECT * FROM user_reviews
                ORDER BY timestamp DESC
                LIMIT %s OFFSET %s
            """
        else:
            # Guests and registered users see only approved reviews
            query = """
                SELECT * FROM user_reviews
                WHERE status = 'approved'
                ORDER BY timestamp DESC
                LIMIT %s OFFSET %s
            """
        cursor.execute(query, (limit, offset))
        rows = cursor.fetchall()
        cursor.close()

        # Map results to a list of dictionaries
        keys = ["id", "name", "review", "rating", "timestamp", "status"]
        reviews = [dict(zip(keys, row)) for row in rows]

        return jsonify(reviews)
    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

@app.route("/api/track-visitor", methods=["POST"])
def track_visitor():
    data = request.json
    user_agent = data.get("user_agent")
    visit_date = data.get("visit_date")
    ip_address = request.remote_addr

    if not (ip_address and user_agent and visit_date):
        return jsonify({"message": "Missing required fields"}), 400

    try:
        conn = mysql.connection
        cursor = conn.cursor()

        # Step 1: Check if the visitor has already been logged for the day
        query_check = """
            SELECT COUNT(*) 
            FROM visitor_logs 
            WHERE ip_address = %s AND user_agent = %s AND visit_date = %s
        """
        cursor.execute(query_check, (ip_address, user_agent, visit_date))
        visitor_count = cursor.fetchone()[0]

        if visitor_count == 0:
            # Step 2: Log the visitor in `visitor_logs`
            query_logs = """
                INSERT INTO visitor_logs (ip_address, user_agent, visit_date)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query_logs, (ip_address, user_agent, visit_date))

            # Step 3: Update visitor stats
            today = datetime.strptime(visit_date, "%Y-%m-%d").date()
            cursor.execute("""
                INSERT INTO visitor_stats (date, visitors_today)
                VALUES (%s, 1)
                ON DUPLICATE KEY UPDATE visitors_today = visitors_today + 1
            """, (today,))

            # Step 4: Update cumulative stats
            cursor.execute("""
                UPDATE visitor_stats
                SET 
                    visitors_this_week = (SELECT COUNT(*) FROM visitor_logs 
                                          WHERE visit_date >= %s AND visit_date <= %s),
                    visitors_this_month = (SELECT COUNT(*) FROM visitor_logs 
                                           WHERE MONTH(visit_date) = MONTH(%s) AND YEAR(visit_date) = YEAR(%s)),
                    total_visitors = (SELECT COUNT(*) FROM visitor_logs)
                WHERE date = %s
            """, (today - timedelta(days=today.weekday()), today, today, today, today))

        conn.commit()
        cursor.close()
        return jsonify({"message": "Visitor logged and stats updated successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

@app.route("/api/track-online", methods=["POST"])
def track_online():
    session_id = request.json.get("session_id")
    ip_address = request.remote_addr

    try:
        conn = mysql.connection
        cursor = conn.cursor()

        # Insert or update online user session
        cursor.execute("""
            INSERT INTO online_users (session_id, ip_address, last_active)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON DUPLICATE KEY UPDATE last_active = CURRENT_TIMESTAMP
        """, (session_id, ip_address))

        # Clean up inactive sessions
        cursor.execute("DELETE FROM online_users WHERE last_active < NOW() - INTERVAL 10 MINUTE")

        conn.commit()
        cursor.close()
        return jsonify({"message": "Online user tracked successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

@app.route("/api/online-users", methods=["GET"])
def get_online_users():
    conn = mysql.connection
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM online_users")
    count = cursor.fetchone()[0]
    cursor.close()
    return jsonify({"online_users": count})


if __name__ == "__main__":
    app.run(debug=True)
