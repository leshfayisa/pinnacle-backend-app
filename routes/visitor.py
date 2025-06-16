from flask import request, jsonify
from db_config import get_db_connection
from . import visitor_bp
import pymysql
from datetime import datetime

@visitor_bp.route("/track-visitor", methods=["POST"])
def track_visitor():
    """
    Track a unique visitor and update visitor statistics.

    Accepts a JSON payload with 'visit_date' and optional 'user_agent'.
    Logs the visitor and updates visitor stats if the visitor is new for the day.

    Returns:
        200 OK: Visitor tracked and stats updated.
        400 Bad Request: Invalid input or date format.
        500 Internal Server Error: Database or internal error.
    """

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


@visitor_bp.route("/track-online", methods=["POST"])
def track_online():
    """
    Track online user activity via session ID.

    Accepts a JSON payload with 'session_id'. Updates the last active time,
    and cleans up sessions inactive for more than 10 minutes.

    Returns:
        200 OK: User tracked.
        400 Bad Request: Invalid or missing session_id.
        500 Internal Server Error: Database or internal error.
    """

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