import jwt
import datetime
from functools import wraps
from flask import request, jsonify, current_app


def generate_token(user_id, role, secret_key):
    """
    Generate a JWT token with user ID and role.
    """
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=100),  # Token expires in 100 hours
        'iat': datetime.datetime.utcnow()  # Issued at
    }
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({
                'message': 'Token is missing',
                'loginRequired': True,
                'userMessage': 'Please login to access this resource.'
            }), 403

        try:
            # Extract token from "Bearer <token>" format
            token = token.split(" ")[1] if " " in token else token.strip()
            secret_key = current_app.config['SECRET_KEY']

            # Decode the token
            data = jwt.decode(token, secret_key, algorithms=['HS256'])
            current_user_id = data['user_id']
            current_user_role = data.get('role', 'user')  # Default to 'user' if no role specified
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
        except Exception as e:
            return jsonify({
                'message': f'An error occurred: {str(e)}',
                'loginRequired': True,
                'userMessage': 'Please login to access this resource.'
            }), 403

        # Pass current_user_id and role as keyword arguments
        return f(*args, current_user_id=current_user_id, current_user_role=current_user_role, **kwargs)

    return decorated

