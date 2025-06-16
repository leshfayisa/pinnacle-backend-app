from flask import send_from_directory
from . import video_bp

@video_bp.route('/video')
def get_video():
    return send_from_directory('static/videos', 'production_video.mp4', as_attachment=False)
