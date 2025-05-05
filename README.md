1. Start the infrastructure: `docker-compose up -d`. This will spin up the following services:
   - `postgres`: PostgreSQL database
   - `zookeeper`: Zookeeper
   - `kafka`: Kafka
2. Install `uv` and sync the environment: `uv sync`.
3. Create tables in the database. Use `scripts/sql/create_tables.sql` to create the necessary tables in the PostgreSQL database.
4. Populate the database with drivers and passengers. Use `scripts/sql/generate_drivers_passengers.py` 
to populate the database with sample data.
5. Run all Kafka consumers with the command `uv run consumers/run_all_consumers.py`. Now the consumers will start consuming messages from the Kafka topics and processing them.
6. Run the Kafka producer with the command `uv run producers/producer.py`. This will start producing messages to the Kafka topics.