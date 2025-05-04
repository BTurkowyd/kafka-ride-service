1. Start the infrastructure: `docker-compose up -d`. This will spin up the following services:
   - `postgres`: PostgreSQL database
   - `zookeeper`: Zookeeper
   - `kafka`: Kafka
2. Install `uv` and sync the environment: `uv sync`.
3. Create tables in the database. Use `scripts/sql/create_tables.sql` to create the necessary tables in the PostgreSQL database.
4. Populate the database with drivers and passengers. Use `scripts/sql/generate_drivers_passengers.py` 
to populate the database with sample data.