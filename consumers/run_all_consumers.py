import threading
from modules.consumers.consumer_ride_requested import consume_ride_requested
from modules.consumers.consumer_ride_started import consume_ride_started
from modules.consumers.consumer_ride_completed import consume_ride_completed
from modules.consumers.consumer_location_update import consume_location_updates

def start_consumer(target_func, name):
    thread = threading.Thread(target=target_func, name=name, daemon=True)
    thread.start()
    return thread

if __name__ == "__main__":
    print("[INFO] Starting all Kafka consumers...")

    threads = [
        start_consumer(consume_ride_requested, "RideRequestedConsumer"),
        start_consumer(consume_ride_started, "RideStartedConsumer"),
        start_consumer(consume_ride_completed, "RideCompletedConsumer"),
        start_consumer(consume_location_updates, "LocationUpdateConsumer")
    ]

    # Keep the main thread alive to let daemon threads run
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down consumers...")