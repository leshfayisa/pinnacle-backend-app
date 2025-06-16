from flask import Blueprint

# Blueprint instances
auth_bp = Blueprint('auth', __name__)
reviews_bp = Blueprint('reviews', __name__)
stats_bp = Blueprint('stats', __name__)
visitor_bp = Blueprint('visitor', __name__)
video_bp = Blueprint('video', __name__)
