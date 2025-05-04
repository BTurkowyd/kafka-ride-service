import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'dbname': os.getenv("POSTGRES_DB"),
    'user': os.getenv("POSTGRES_USER"),
    'password': os.getenv("POSTGRES_PASSWORD"),
    'host': '192.168.178.93',
    'port': 5432,
}

def load_ids():
    """Load all driver and passenger IDs once."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM drivers")
    drivers = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT id FROM passengers")
    passengers = [row[0] for row in cursor.fetchall()]
    conn.close()
    return drivers, passengers