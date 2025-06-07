# 🚕 Kafka Ride Service

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![License](https://img.shields.io/github/license/BTurkowyd/kafka-ride-service)](LICENSE)

A repository focused on implementing Apache Kafka combined with Kubernetes and PostgreSQL to simulate a simplistic "Uber-like" service.

---

## Table of Contents

- [🚕 Kafka Ride Service](#-kafka-ride-service)
  - [Table of Contents](#table-of-contents)
  - [Project Overview](#project-overview)
  - [Quickstart](#quickstart)
  - [Prerequisites](#prerequisites)
  - [Directory Structure](#directory-structure)
  - [Configuration](#configuration)
  - [How It Works](#how-it-works)
    - [Producer Service](#producer-service)
    - [Event Generator](#event-generator)
    - [Consumer Services](#consumer-services)
    - [PostgreSQL Database](#postgresql-database)
    - [Kafka Topics](#kafka-topics)
  - [Kubernetes \& Networking](#kubernetes--networking)
    - [🛡️ Network Policies](#️network-policies)
      - [🔐 Policy Overview](#-policy-overview)
    - [Exposing Services](#exposing-services)
      - [Example: Exposing kafka-producer](#example-exposing-kafka-producer)
    - [Networking \& LAN Access](#networking--lan-access)
  - [Testing](#testing)
  - [Troubleshooting](#troubleshooting)
  - [Contributing](#contributing)
  - [License](#license)

---

## Project Overview

This project simulates an **event-driven ride-hailing platform**, demonstrating real-world usage of:

- **Kafka** as a message broker
- **FastAPI** as the producer-facing HTTP service
- **Avro serialization** with a Schema Registry
- **Minikube** and **Kubernetes** for orchestration
- **PostgreSQL** for reference data (drivers, passengers, etc.)

The goal is to simulate ride events (`ride_requested`, `ride_started`, `location_update`, `ride_completed`) and send them into Kafka, either through a script or via a REST API exposed by a FastAPI Kafka producer.

![kafka-based_event_pipeline.png](assets/kafka-based_event_pipeline_(kubernetes).png)

---

## Quickstart

The following steps will get you up and running quickly on your local machine (using Minikube and Docker).

**1. Clone the repository**

```bash
git clone https://github.com/BTurkowyd/kafka-ride-service.git
cd kafka-ride-service
```

**2. Install Python (3.11+) and [uv](https://github.com/astral-sh/uv)**

```bash
# Recommended: install uv for fast dependency management
curl -Ls https://astral.sh/uv/install.sh | sh
```

**3. Set up your virtual environment and install dependencies**

```bash
uv sync  # uses uv.lock for dependency resolution
```
*Alternatively, use `uv pip install -r uv.lock` if you prefer lockfile-only installations.*

**4. Start Minikube and build images**

```bash
minikube start --driver=docker
make build-images
```

**5. Deploy resources to Kubernetes**

```bash
make create-namespace
make add-common-env-config-map
make add-postgres-secrets
make create-resources
minikube tunnel
```

**6. Simulate events or use the API**

- Use the event generator script in `scripts/`
- Or, interact with the FastAPI endpoints (see [API Usage](#how-it-works))

---

## Prerequisites

- **Python 3.11+** (Recommended: use a virtual environment)
- **uv** for dependency management (Poetry is an alternative, not the primary approach)
- **Docker** & **Docker Compose** (optional, for local dev)
- **Minikube** & **kubectl** (for Kubernetes)
- **curl** (for testing endpoints)

---

## Directory Structure

| Directory          | Purpose                                  |
|--------------------|------------------------------------------|
| `producer/`        | Kafka event producer (FastAPI-based)     |
| `consumers/`       | Kafka event consumers (Python scripts)   |
| `scripts/`         | Event simulation & SQL bootstrap         |
| `k8s-manifests/`   | Kubernetes manifests for deployment      |
| `assets/`          | Images and documentation assets          |
| `docs/`            | Extended documentation and guides        |

---

## Configuration

Copy `.env.example` to `.env` and adjust as needed.  
All environment variables are documented here:

| Variable             | Description                         | Default                       |
|----------------------|-------------------------------------|-------------------------------|
| `KAFKA_BROKER`       | Kafka broker address                | `localhost:9092`              |
| `SCHEMA_REGISTRY_URL`| URL to Schema Registry              | `http://localhost:8081`       |
| `POSTGRES_HOST`      | PostgreSQL host                     | `localhost`                   |
| `POSTGRES_PORT`      | PostgreSQL port                     | `5432`                        |
| `POSTGRES_USER`      | PostgreSQL username                 | _from secret_                 |
| `POSTGRES_PASSWORD`  | PostgreSQL password                 | _from secret_                 |
| `POSTGRES_DB`        | PostgreSQL database name            | `uber`                        |
| `PRODUCER_URL`       | HTTP base URL of Kafka producer     | `http://localhost:8888`       |

---

## How It Works

### Producer Service

- Exposes a FastAPI-based HTTP API.
- Accepts POST requests like `/ride-request`, `/ride-started`, etc.
- Publishes serialized Avro messages to Kafka topics (one per event type).
- Runs inside Kubernetes as a service of type `LoadBalancer`.

### Event Generator

- Python script simulating real ride activity.
- Loads driver and passenger IDs from Postgres.
- Generates random routes, coordinates, and timestamps.
- Sends HTTP requests to the producer API instead of producing directly to Kafka (decoupling transport from generation).

### Consumer Services

- Each consumer listens to a specific Kafka topic.
- Consumes and deserializes Avro-encoded messages.
- Processes messages and persists or updates relevant data in PostgreSQL.
- Includes a Dead Letter Queue (DLQ) handler for failed messages.
- Deployed as a Kubernetes `Deployment` within the `uber-service` namespace.

### PostgreSQL Database

- Stores static and processed data like:
  - Drivers and passengers
  - Ride logs (requested, started, completed)
  - Location updates
- Shared between the producer (for data lookup) and consumers (for writes).
- Exposed as a `LoadBalancer` service in Kubernetes.
- Schema initialization is handled by `scripts/sql/create_tables.sql`.

### Kafka Topics

| Topic Name              | Event Type         | Description                      |
|-------------------------|--------------------|----------------------------------|
| `uber.ride_requested`   | `ride_requested`   | When a passenger requests a ride |
| `uber.ride_started`     | `ride_started`     | When a driver accepts & starts   |
| `uber.location_update`  | `location_update`  | Driver location during ride      |
| `uber.ride_completed`   | `ride_completed`   | When the ride finishes           |
| `uber.dlq`              | `dead_letter_event`| Failed/unparseable messages      |

---

## Kubernetes & Networking

### 🛡️ Network Policies

To simulate a secure, production-like environment even in local development (e.g., with **Minikube**), this project uses **Kubernetes NetworkPolicies** to restrict inter-pod communication.

#### 🔐 Policy Overview

| Policy                                | Source Pod(s)         | Destination Pod     | Port  | Purpose                              |
|--------------------------------------|------------------------|----------------------|-------|---------------------------------------|
| **Deny all ingress**                 | _All_                  | All                  | —     | Default isolation                     |
| **Allow producer ➝ Kafka**           | `app=kafka-producer`   | `app=kafka`          | 9092  | Send events to Kafka broker           |
| **Allow producer ➝ PostgreSQL**      | `app=kafka-producer`   | `app=postgres`       | 5432  | Persist metadata in database          |
| **Allow consumer ➝ Kafka**           | `role=consumer`        | `app=kafka`          | 9092  | Consume events from Kafka             |
| **Allow consumer ➝ PostgreSQL**      | `role=consumer`        | `app=postgres`       | 5432  | Enrich or store consumed data         |
| **Allow Kafka ➝ Zookeeper**          | `app=kafka`            | `app=zookeeper`      | 2181  | Internal Kafka coordination           |
| **Allow schema-registry ➝ Kafka**    | `app=schema-registry`  | `app=kafka`          | 9092  | Schema registration and lookup        |
| **Allow Kafka ➝ Schema Registry**    | `app=kafka`            | `app=schema-registry`| 8081  | Fetch Avro schemas                    |
| **Allow Kafka UI ➝ Kafka**           | `app=kafka-ui`         | `app=kafka`          | 9092  | Kafka UI dashboard access             |

### Exposing Services

- Use `minikube tunnel` to expose Kubernetes LoadBalancer services.
- For WSL2 users, use `socat` and `netsh` for port forwarding if needed.
- For simplified networking, run Minikube with the Docker driver on Windows.

#### Example: Exposing kafka-producer

```yaml
apiVersion: v1
kind: Service
metadata:
  name: kafka-producer
  namespace: uber-service
spec:
  type: LoadBalancer
  ports:
    - port: 8888
      targetPort: 8888
  selector:
    app: kafka-producer
```

- Start the tunnel:  
  ```bash
  minikube tunnel
  ```
- Test the endpoint:  
  ```bash
  curl http://localhost:8888/health
  # Should return {"status":"ok"}
  ```

### Networking & LAN Access

For detailed instructions on exposing Kubernetes services to your LAN or handling Minikube networking on Windows/WSL2, see:

- [Exposing Kubernetes Services from Minikube to External Machines](docs/network-exposure-minikube.md)
- [Running Minikube on Windows for Easier LAN Access](docs/minikube-windows-lan-access.md)

These guides cover port forwarding, tunnels, firewall rules, and more.

---

## Testing

Run tests with:

```bash
pytest
# or
make test
```

---

## Troubleshooting

- Ensure all required services are running (Kafka, Schema Registry, PostgreSQL).
- Make sure environment variables are set correctly.
- If using WSL2, ensure port forwarding is properly configured.
- For Minikube networking issues, see the [Exposing Kubernetes Services from Minikube to External Machines](docs/network-exposure-minikube.md) and/or [Running Minikube on Windows for Easier LAN Access](docs/minikube-windows-lan-access.md)

---

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.  
For major changes, please open an issue first to discuss what you would like to change.

---

## License

MIT License. See [LICENSE](LICENSE) for details.