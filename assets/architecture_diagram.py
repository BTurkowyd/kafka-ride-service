from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.queue import Kafka
from diagrams.onprem.database import PostgreSQL
from diagrams.programming.language import Python
from diagrams.custom import Custom
from diagrams.k8s.compute import StatefulSet, Deployment

with Diagram("Kafka-based Event Pipeline (Kubernetes)", show=False, direction="LR"):

    rest_producer = Python("event_sender.py")

    with Cluster("Kubernetes Cluster (Minikube)"):

        zookeeper = StatefulSet("Zookeeper (StatefulSet)")
        schema_registry = Deployment("Schema Registry (Deployment)")
        kafka_ui = Custom("Kafka UI", "./kafka-ui.png")
        db = PostgreSQL("PostgreSQL (StatefulSet)")

        with Cluster("Kafka Cluster"):
            kafka_broker = Kafka("Kafka Broker (StatefulSet)")

            with Cluster("Topics"):
                with Cluster("Streaming Topics"):
                    topic1 = Kafka("ride_requested")
                    topic2 = Kafka("ride_started")
                    topic3 = Kafka("ride_completed")
                    topic4 = Kafka("location_update")
                with Cluster("Dead Letter Queue"):
                    topic5 = Kafka("dead_letter_queue")

        api_producer = Deployment("FastAPI Kafka Producer (Deployment)")

        with Cluster("Consumers"):
            with Cluster("Streaming Consumers"):
                c1 = Python("ride_requested (Deployment)")
                c2 = Python("ride_started (Deployment)")
                c3 = Python("ride_completed (Deployment)")
                c4 = Python("location_update (Deployment)")

            with Cluster("Dead Letter Queue Consumer"):
                c5 = Python("dead_letter_queue (Deployment)")

    # Flow connections
    (
        rest_producer
        >> Edge(label="REST")
        >> api_producer
        >> Edge(label="Avro Serialized")
        >> kafka_broker
    )
    zookeeper >> kafka_broker
    schema_registry >> kafka_broker
    kafka_ui << kafka_broker

    kafka_broker >> [topic1, topic2, topic3, topic4]

    topic1 >> Edge(label="Avro Deserialized") >> c1 >> Edge(color="green") >> db
    topic2 >> Edge(label="Avro Deserialized") >> c2 >> Edge(color="green") >> db
    topic3 >> Edge(label="Avro Deserialized") >> c3 >> Edge(color="green") >> db
    topic4 >> Edge(label="Avro Deserialized") >> c4 >> Edge(color="green") >> db

    (
        [c1, c2, c3, c4]
        >> Edge(label="Error", color="red")
        >> topic5
        >> c5
        >> Edge(color="green")
        >> db
    )
