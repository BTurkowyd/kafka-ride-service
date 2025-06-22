"""
Helper functions for database access and event preparation.
"""

import psycopg2
import json
import base64
from .constants import DB_CONFIG


def get_db_connection():
    """
    Establishes and returns a new database connection using DB_CONFIG.
    """
    return psycopg2.connect(**DB_CONFIG)


def ride_exists(conn, ride_id):
    """
    Checks if a ride with the given ride_id exists in the database.

    Args:
        conn: Active database connection.
        ride_id: UUID of the ride.

    Returns:
        bool: True if the ride exists, False otherwise.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM rides WHERE ride_id = %s;", (ride_id,))
        return cur.fetchone() is not None


def prepare_original_event(msg, event=None):
    """
    Returns a stringified version of the event or a base64-encoded fallback.

    Args:
        msg: Kafka message object.
        event: (Optional) Decoded event dictionary.

    Returns:
        str: JSON string if possible, otherwise base64-encoded message value.
    """
    if event is not None:
        try:
            return json.dumps(event)
        except (TypeError, ValueError):
            pass  # fall through to base64

    try:
        return base64.b64encode(msg.value()).decode("utf-8") if msg.value() else ""
    except Exception:
        return ""
