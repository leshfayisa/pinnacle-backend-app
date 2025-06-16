from routes.auth import auth_bp
from routes.reviews import reviews_bp
from routes.stats import stats_bp
from routes.visitor import visitor_bp
from routes.video import video_bp

def register_all_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(reviews_bp, url_prefix="/api")
    app.register_blueprint(stats_bp, url_prefix="/api")
    app.register_blueprint(visitor_bp, url_prefix="/api")
    app.register_blueprint(video_bp, url_prefix="/api")
