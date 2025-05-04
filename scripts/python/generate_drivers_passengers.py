import psycopg2
from faker import Faker
from faker_vehicle import VehicleProvider

import random
from datetime import datetime
from dotenv import load_dotenv
import os


faker = Faker()
faker.add_provider(VehicleProvider)

load_dotenv()

DB_CONFIG = {
    'dbname':os.getenv("POSTGRES_DB"),
    'user': os.getenv("POSTGRES_USER"),
    'password': os.getenv("POSTGRES_PASSWORD"),
    'host': '192.168.178.93',
    'port': 5432
}

def create_connection():
    return psycopg2.connect(**DB_CONFIG)

def seed_drivers(cursor, count=10):
    for _ in range(count):
        name = faker.name()
        vehicle = faker.vehicle_make_model()
        rating = round(random.uniform(3.5, 5.0), 2)
        cursor.execute(
            "INSERT INTO drivers (name, vehicle, rating) VALUES (%s, %s, %s);",
            (name, vehicle, rating)
        )

def seed_passengers(cursor, count=50):
    for _ in range(count):
        name = faker.name()
        signup_date = faker.date_between(start_date='-2y', end_date='today')
        cursor.execute(
            "INSERT INTO passengers (name, signup_date) VALUES (%s, %s);",
            (name, signup_date)
        )

if __name__ == "__main__":
    conn = create_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                print("Seeding drivers...")
                seed_drivers(cursor)
                print("Seeding passengers...")
                seed_passengers(cursor)
        print("Data seeded successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
