from flask import request, jsonify, current_app
from db_config import get_db_connection
from authentication.token_generator import token_required
from . import reviews_bp
import pymysql
import jwt

@reviews_bp.route("/reviews", methods=["POST"])
def add_review():
    """
    Submit a user review.

    Accepts a JSON payload with 'name', 'review', and 'rating'.
    Validates and stores the review with a default status of 'pending'.

    Returns:
        201 Created: Review submitted successfully.
        400 Bad Request: Validation error.
        409 Conflict: Duplicate entry.
        500 Internal Server Error: Database or internal error.
    """

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


@reviews_bp.route("/reviews", methods=["GET"])
def get_reviews():
    """
    Retrieve a paginated list of reviews.

    - Admins see all reviews.
    - Other users see only 'approved' reviews.
    - Uses JWT if provided in Authorization header.

    Query Params:
        offset (int): Pagination offset (default: 0)
        limit (int): Number of items per page (default: 5)

    Returns:
        200 OK: List of reviews.
        403 Forbidden: Token error.
        404 Not Found: No reviews.
        500 Internal Server Error: Database or internal error.
    """

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


@reviews_bp.route('/reviews/<int:review_id>/status', methods=["PUT"])
@token_required
def update_review_status(current_user_id, review_id, current_user_role):
    """
    Update the status of a user review (admin only).

    Requires admin role and a valid JWT token. Accepts a 'status' field in the JSON payload.

    Args:
        review_id (int): The ID of the review to update.

    Returns:
        200 OK: Status updated or already set.
        400 Bad Request: Invalid input or status.
        403 Forbidden: User is not an admin.
        404 Not Found: Review not found.
        500 Internal Server Error: Database or internal error.
    """

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

