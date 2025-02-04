from flask import Flask, jsonify, request, current_app
import jwt
import pymysql
from db_config import app, get_db_connection
from datetime import datetime, timedelta
from functools import wraps

from authentication.token_generator import generate_token, token_required
from authentication.hash_password import verify_password, hash_password_with_salt

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
        token = generate_token(user_id, role, app.config['SECRET_KEY'])

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

    # Validate status
    if not new_status or new_status not in ['approved', 'rejected']:
        return jsonify({'message': 'Invalid status value'}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': "Database connection error"}), 500

    try:
        with conn.cursor() as cursor:
            # Check if review exists
            cursor.execute("SELECT status FROM user_reviews WHERE id = %s", (review_id,))
            review = cursor.fetchone()

            if not review:
                return jsonify({'message': 'Review not found'}), 404

            # Check if the status is already set
            if review['status'] == new_status:
                return jsonify({'message': f'Review status is already {new_status}'}), 200

            # Update review status
            cursor.execute(
                "UPDATE user_reviews SET status = %s, updated_time = NOW() WHERE id = %s",
                (new_status, review_id)
            )
            conn.commit()

        return jsonify({'message': f"Review status updated to {new_status}"}), 200

    except pymysql.MySQLError as db_err:
        return jsonify({'message': f"Database error: {str(db_err)}"}), 500

    except Exception as e:
        return jsonify({'message': f"Internal error: {str(e)}"}), 500

    finally:
        conn.close()


@app.route("/api/visitor-stats", methods=["GET"])
def get_visitor_stats():
    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': "Database connection error"}), 500

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:  # Ensure DictCursor is used
            cursor.execute("""
                SELECT date, visitors_today, visitors_yesterday, 
                       visitors_this_week, visitors_this_month, total_visitors
                FROM visitor_stats 
                ORDER BY date DESC 
                LIMIT 1
            """)
            row = cursor.fetchone()

        if not row:
            return jsonify({"message": "No visitor statistics available"}), 404

        return jsonify(row), 200  # Directly return the dictionary

    except pymysql.MySQLError as db_err:
        return jsonify({'message': f"Database error: {str(db_err)}"}), 500

    except Exception as e:
        return jsonify({'message': f"Internal error: {str(e)}"}), 500

    finally:
        conn.close()



@app.route("/api/reviews", methods=["POST"])
def add_review():
    data = request.get_json()
    
    if not data:
        return jsonify({"message": "Invalid input"}), 400

    name = data.get("name", "").strip()
    review = data.get("review", "").strip()
    rating = data.get("rating")

    # Validate input fields
    if not name or not review or rating is None:
        return jsonify({"message": "All fields (name, review, rating) are required"}), 400

    if not isinstance(name, str) or not isinstance(review, str):
        return jsonify({"message": "Invalid input: name and review must be strings"}), 400

    if len(name) > 255 or len(review) > 1000:
        return jsonify({"message": "Name or review is too long"}), 400

    try:
        rating = int(rating)  # Ensure rating is an integer
        if rating < 1 or rating > 5:
            raise ValueError
    except ValueError:
        return jsonify({"message": "Rating must be an integer between 1 and 5"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Database connection error"}), 500

    try:
        with conn.cursor() as cursor:
            # Insert review with default 'pending' status
            query = """
            INSERT INTO user_reviews (name, review, rating, status, timestamp)
            VALUES (%s, %s, %s, %s, NOW())
            """
            cursor.execute(query, (name, review, rating, 'pending'))
            conn.commit()

        return jsonify({"message": "Review submitted successfully"}), 201

    except pymysql.IntegrityError:
        return jsonify({"message": "Duplicate entry detected"}), 409  # Handle duplicates if constraints exist

    except pymysql.MySQLError as db_err:
        return jsonify({"message": f"Database error: {str(db_err)}"}), 500

    except Exception as e:
        return jsonify({"message": f"Internal error: {str(e)}"}), 500

    finally:
        conn.close()


@app.route("/api/reviews", methods=["GET"])
def get_reviews():
    current_user_role = 'guest'
    token = request.headers.get('Authorization')
    if token:
        try:
            token = token.split(" ")[1] if " " in token else token.strip()
            secret_key = current_app.config['SECRET_KEY']
            data = jwt.decode(token, secret_key, algorithms=['HS256'])
            current_user_role = data.get('role', 'guest')

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 403
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 403

    conn = get_db_connection()
    if conn is None:
        return jsonify({'message': "Database connection error"}), 500

    try:
        offset = request.args.get('offset', default=0, type=int)
        limit = request.args.get('limit', default=5, type=int)

        with conn.cursor() as cursor:
            if current_user_role == 'admin':
                query = """
                    SELECT id, name, review, rating, timestamp, status
                    FROM user_reviews
                    ORDER BY timestamp DESC
                    LIMIT %s OFFSET %s
                """
            else:
                query = """
                    SELECT id, name, review, rating, timestamp, status
                    FROM user_reviews
                    WHERE status = 'approved'
                    ORDER BY timestamp DESC
                    LIMIT %s OFFSET %s
                """
            cursor.execute(query, (limit, offset))
            rows = cursor.fetchall()

        if not rows:
            return jsonify({"message": "No reviews found"}), 404

        # Directly return rows if DictCursor is used
        return jsonify(rows), 200
    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
    finally:
        conn.close()


@app.route("/api/track-visitor", methods=["POST"])
def track_visitor():
    data = request.get_json()

    if not data:
        return jsonify({"message": "Invalid input"}), 400

    user_agent = data.get("user_agent", "").strip()
    visit_date = data.get("visit_date", "").strip()
    ip_address = request.remote_addr

    if not user_agent:
        user_agent = request.headers.get("User-Agent", "Unknown")

    # Validate visit_date format
    try:
        visit_date = datetime.strptime(visit_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Invalid date format, expected YYYY-MM-DD"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Database connection error"}), 500

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:  # Use DictCursor to return dictionary results

            # Step 1: Fetch Previous Data Before Insert
            cursor.execute("SELECT visitors_today FROM visitor_stats WHERE date = DATE_SUB(%s, INTERVAL 1 DAY) LIMIT 1", (visit_date,))
            previous_day_result = cursor.fetchone()
            visitors_yesterday = previous_day_result["visitors_today"] if previous_day_result else 0

            cursor.execute("SELECT COALESCE(SUM(visitors_today), 0) AS visitors_this_week FROM visitor_stats WHERE date BETWEEN DATE_SUB(%s, INTERVAL 6 DAY) AND %s", (visit_date, visit_date))
            visitors_this_week = cursor.fetchone()["visitors_this_week"]

            cursor.execute("SELECT COALESCE(SUM(visitors_today), 0) AS visitors_this_month FROM visitor_stats WHERE date BETWEEN DATE_SUB(%s, INTERVAL 29 DAY) AND %s", (visit_date, visit_date))
            visitors_this_month = cursor.fetchone()["visitors_this_month"]

            cursor.execute("SELECT COALESCE(SUM(visitors_today), 0) AS total_visitors FROM visitor_stats")
            total_visitors = cursor.fetchone()["total_visitors"]

            # Step 2: Attempt to insert visitor into visitor_logs
            try:
                query_logs = """
                    INSERT INTO visitor_logs (ip_address, user_agent, visit_date)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(query_logs, (ip_address, user_agent, visit_date))
                is_new_visitor = True  # Visitor was successfully inserted

            except pymysql.IntegrityError:
                # Visitor already exists (same IP + User Agent + Date), do not count again
                is_new_visitor = False

            # Step 3: If this is a new visitor, update visitor_stats
            if is_new_visitor:
                query_stats = """
                    INSERT INTO visitor_stats (date, visitors_today, visitors_yesterday, visitors_this_week, visitors_this_month, total_visitors)
                    VALUES (%s, 1, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        visitors_today = visitors_today + 1,
                        visitors_yesterday = VALUES(visitors_yesterday),
                        visitors_this_week = VALUES(visitors_this_week),
                        visitors_this_month = VALUES(visitors_this_month),
                        total_visitors = total_visitors + 1;
                """
                cursor.execute(query_stats, (visit_date, visitors_yesterday, visitors_this_week, visitors_this_month, total_visitors))

        conn.commit()
        return jsonify({"message": "Visitor logged and stats updated successfully"}), 200

    except pymysql.MySQLError as db_err:
        return jsonify({"message": f"Database error: {str(db_err)}"}), 500

    except Exception as e:
        return jsonify({"message": f"Internal error: {str(e)}"}), 500

    finally:
        conn.close()


@app.route("/api/track-online", methods=["POST"])
def track_online():
    data = request.get_json()

    if not data or "session_id" not in data:
        return jsonify({"message": "Missing session_id"}), 400

    session_id = data.get("session_id", "").strip()
    ip_address = request.remote_addr

    if not session_id:
        return jsonify({"message": "Invalid session_id"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Database connection error"}), 500

    try:
        with conn.cursor() as cursor:
            # Ensure session_id is unique and update last_active on duplicate
            cursor.execute("""
                INSERT INTO online_users (session_id, ip_address, last_active)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON DUPLICATE KEY UPDATE last_active = CURRENT_TIMESTAMP
            """, (session_id, ip_address))

            # Clean up inactive sessions older than 10 minutes
            cursor.execute("DELETE FROM online_users WHERE last_active < NOW() - INTERVAL 10 MINUTE")

        conn.commit()
        return jsonify({"message": "Online user tracked successfully"}), 200

    except pymysql.MySQLError as db_err:
        return jsonify({"message": f"Database error: {str(db_err)}"}), 500

    except Exception as e:
        return jsonify({"message": f"Internal error: {str(e)}"}), 500

    finally:
        conn.close()



@app.route("/api/online-users", methods=["GET"])
def get_online_users():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"message": "Database connection error"}), 500

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:  # Ensure DictCursor is used
            cursor.execute("SELECT COUNT(*) AS total FROM online_users")
            row = cursor.fetchone()


        if row is None:
            return jsonify({"online_users": 0}), 200

        count = row.get("total")

        if count is None:
            raise ValueError("Unexpected data format: 'total' key is missing from result.")

        return jsonify({"online_users": count}), 200

    except pymysql.MySQLError as db_err:
        return jsonify({"message": f"Database error: {str(db_err)}"}), 500

    except Exception as e:
        return jsonify({"message": f"Internal error: {str(e)}"}), 500

    finally:
        conn.close()

if __name__ == "__main__":
    app.run(debug=True)
