from flask import send_from_directory
from . import video_bp

@video_bp.route('/video')
def get_video():
    """
    Serve a static video file from the /static/videos directory.

    Returns:
        200 OK: Video file stream.
        404 Not Found: If the file doesn't exist.
    """

    return send_from_directory('static/videos', 'production_video.mp4', as_attachment=False)
