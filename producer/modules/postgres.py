"""
PostgreSQL connection configuration for the producer.

Loads environment variables and provides a dictionary for psycopg2 connection.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database connection configuration dictionary
DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST", "127.0.0.1"),
    "port": 5432,
}
