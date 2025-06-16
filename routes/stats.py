from flask import jsonify
from db_config import get_db_connection
from . import stats_bp
import pymysql

@stats_bp.route("/visitor-stats", methods=["GET"])
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


@stats_bp.route("/online-users", methods=["GET"])
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
