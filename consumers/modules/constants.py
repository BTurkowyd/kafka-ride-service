"""
Constants and configuration for database connections.

Loads environment variables and provides a dictionary for PostgreSQL connection.
"""

import os
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()

# Database connection configuration dictionary
DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": 5432,
}
