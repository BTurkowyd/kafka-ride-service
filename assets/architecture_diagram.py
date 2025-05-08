from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.queue import Kafka
from diagrams.onprem.database import PostgreSQL
from diagrams.generic.compute import Rack
from diagrams.programming.language import Python
from diagrams.custom import Custom

with Diagram("Kafka-based Event Pipeline", show=False, direction="LR"):

    producer = Python("producer.py")

    with Cluster("Docker Compose"):
        zookeeper = Rack("Zookeeper")
        kafka_ui = Custom("Kafka UI", "./kafka-ui.png")
        schema_registry = Rack("Schema Registry")

        with Cluster("Kafka Cluster"):
            kafka_broker = Kafka("Kafka Broker")

            with Cluster("Topics"):
                with Cluster("Streaming Topics"):
                    topic1 = Kafka("ride_requested")
                    topic2 = Kafka("ride_started")
                    topic3 = Kafka("ride_completed")
                    topic4 = Kafka("location_update")
                with Cluster("Dead Letter Queue"):
                    topic5 = Kafka("dead_letter_queue")

        with Cluster("Consumers"):
            with Cluster("Streaming Consumers"):
                c1 = Python("ride_requested")
                c2 = Python("ride_started")
                c3 = Python("ride_completed")
                c4 = Python("location_update")

            with Cluster("Dead Letter Queue Consumer"):
                c5 = Python("dead_letter_queue")

        db = PostgreSQL("PostgreSQL")

    # Connections
    producer >> Edge(label="Avro Serialized") >> kafka_broker
    zookeeper >> kafka_broker
    schema_registry >> kafka_broker
    kafka_ui << kafka_broker

    kafka_broker >> [topic1, topic2, topic3, topic4]

    topic1 >> Edge(label="Avro Deserialized") >> c1 >> db
    topic2 >> Edge(label="Avro Deserialized") >> c2 >> db
    topic3 >> Edge(label="Avro Deserialized") >> c3 >> db
    topic4 >> Edge(label="Avro Deserialized") >> c4 >> db
    [c1, c2, c3, c4] >> Edge(label="Error") >> topic5 >> c5 >> db