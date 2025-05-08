import psycopg2
import json
import base64
from .constants import DB_CONFIG

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def ride_exists(conn, ride_id):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM rides WHERE ride_id = %s;", (ride_id,))
        return cur.fetchone() is not None


def prepare_original_event(msg, event=None):
    """
    Returns a stringified version of the event or raw base64 fallback.
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