import psycopg2
from .constants import DB_CONFIG

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def ride_exists(conn, ride_id):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM rides WHERE ride_id = %s;", (ride_id,))
        return cur.fetchone() is not None