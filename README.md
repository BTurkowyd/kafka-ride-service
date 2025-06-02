# 🚕 Kafka Ride Service
### NOTE: This guide was generated with ChatGPT based on the provided context.

## 🛠 Purpose of This Project

This project simulates an **event-driven ride-hailing platform**, built to demonstrate real-world usage of:

- **Kafka** as a message broker
- **FastAPI** as the producer-facing HTTP service
- **Avro serialization** with a Schema Registry
- **Minikube** and **Kubernetes** for orchestration
- **PostgreSQL** for reference data (drivers, passengers, etc.)

The goal is to simulate ride events (e.g., `ride_requested`, `ride_started`, `location_update`, `ride_completed`) and send them into Kafka, either through a script or via a REST API exposed by a FastAPI Kafka producer.

![kafka-based_event_pipeline.png](assets/kafka-based_event_pipeline.png)

## ✅ Prerequisites for Running the Kafka Ride Service

### 💻 Required Software

#### 🐍 Python 3.11+
Used across both producers and consumers.
- Recommended: Use a virtual environment (e.g. `uv`, `venv`, or `virtualenv`)
- Install from [https://www.python.org](https://www.python.org)

#### 📦 Poetry or uv (for dependency management)
Project uses `pyproject.toml` and `uv.lock` for dependencies.
- Recommended: `uv` for speed → [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv)
```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

---

### 🐋 Docker and 🐳 Docker Compose (optional)
Used for:
- Containerizing producer/consumer services (`Dockerfile`)
- Building images used in Kubernetes

> Install from: [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)

---

### ☸️ Kubernetes via Minikube (or alternative local cluster)
To run manifests from `k8s-manifests/`, you'll need:
- [Minikube](https://minikube.sigs.k8s.io/docs/start/)
- `kubectl` CLI

If running Minikube on Windows, use Docker driver for easiest LAN access:
```bash
minikube start --driver=docker
```
---

### 📡 Kafka Ecosystem

These are provisioned by `k8s/k8s-kafka-zookeeper.yaml`. 

---

### 🗃️ PostgreSQL

Required by both the producer and consumer services:
- A Postgres deployment is defined in `k8s-manifests/k8s-postgres.yaml`
- Initialization via `scripts/sql/create_tables.sql`

Postgres credentials should be set via Kubernetes secrets or `.env`.

---

### 🧪 Tools for Testing & Development

#### 🧰 Makefile Targets

These `make` commands streamline building images, configuring Kubernetes, and exposing local services via `socat`.
To use them, in terminal from the root directory of the repository use `make COMMAND`.

#### 🏗️ `build-images`

Builds Docker images for the Kafka consumer and producer using the Docker daemon inside Minikube.

```bash
make build-images
```

#### 🛡️ `create-namespace`

Creates the `uber-service` namespace in Kubernetes.

```bash
make create-namespace
```

#### 🧾 `add-common-env-config-map`

Creates a `ConfigMap` from your local `.env` file under the `uber-service` namespace.

```bash
make add-common-env-config-map
```

#### 🔐 `add-postgres-secrets`

Creates a Kubernetes **Secret** from your `.env` file for use with PostgreSQL credentials.

```bash
make add-postgres-secrets
```

#### 🚀 `create-resources`

Applies all required Kubernetes manifests to launch the system:

```bash
make create-resources
```

#### 🌉 `socat-ports`

Bridges internal Kubernetes services (inside WSL2 or Minikube) to your Windows host using `socat`.

```bash
make socat-ports
```

#### ❌ `socat-kill`

Stops all running `socat` port-forwarding processes.

```bash
make socat-kill
```

---

#### 📜 Curl
Used to hit HTTP endpoints like `/ride-request`.

---

### 📁 Directory Overview

| Directory         | Purpose                                  |
|------------------|------------------------------------------|
| `producer/`       | Kafka event producer (FastAPI-based)     |
| `consumers/`      | Kafka event consumers (Python scripts)   |
| `scripts/`        | Event simulation + SQL bootstrap         |
| `k8s-manifests/`  | Kubernetes manifests for deployment      |
| `topics/`         | Kafka topic bootstrap script             |

---
### 🧾 Environment Variables in ConfigMap and Secrets

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
### 🌐 Exposed LoadBalancer Services in Kubernetes

The following services are exposed externally using the `LoadBalancer` type in Kubernetes. They are accessible via their corresponding ports once `minikube tunnel` is running.

| Service Name       | Namespace      | Port  | Description                          |
|--------------------|----------------|-------|--------------------------------------|
| `kafka-producer`   | `uber-service` | 8888  | HTTP API exposed by FastAPI Producer |
| `kafka-ui`         | `uber-service` | 8080  | Web UI to monitor Kafka              |
| `postgres`         | `uber-service` | 5432  | PostgreSQL instance                  |

To expose these externally (e.g., for access from another device), run:

```powershell
minikube tunnel
```

---
### Tunenl access to minikube cluster
To access some of those services (especially Kafka UI, Potgres and the producer deployment), you will need to expose the minikube cluster via **tunnel access** using:

- `minikube tunnel` to expose LoadBalancer services
- Optional `socat` or `netsh` if using Minikube via WSL2

---
## 📡 System Overview

### Producer Service

- Exposes a FastAPI-based HTTP API.
- Accepts POST requests like `/ride-request`, `/ride-started`, etc.
- Publishes serialized Avro messages to Kafka topics (one per event type).
- Runs inside Kubernetes as a service of type `LoadBalancer`.

### Event Generator

- A Python script simulating real ride activity.
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

### 📡 Kafka Topics

| Topic Name              | Event Type         | Description                      |
|-------------------------|--------------------|----------------------------------|
| `uber.ride_requested`   | `ride_requested`   | When a passenger requests a ride |
| `uber.ride_started`     | `ride_started`     | When a driver accepts & starts   |
| `uber.location_update`  | `location_update`  | Driver location during ride      |
| `uber.ride_completed`   | `ride_completed`   | When the ride finishes           |
| `uber.dlq`              | `dead_letter_event`| Failed/unparseable messages      |

---

## 🔁 Communication & Deployment Highlights

### Minikube (WSL2-Based)

To expose services outside WSL2 (e.g., to your Mac), the setup includes:

- `minikube tunnel` to expose Kubernetes LoadBalancer services.
- `socat` to bridge traffic from WSL2 to Windows.
- `netsh interface portproxy` to forward Windows ports to WSL2.
- Windows firewall rules to expose specific ports on the LAN.

### Simplified Alternative: Minikube on Windows with Docker

If you run Minikube **directly from PowerShell** using the Docker driver:

- You avoid the complexity of WSL2 networking.
- Services are accessible on `localhost` without `socat` or `portproxy`.
- LAN access only requires a firewall rule.

---

# 🔌 Exposing Kubernetes Services from Minikube to External Machines

This guide walks you through how to expose a service running in a Minikube cluster inside WSL2 so that it can be accessed from **another machine on your network (e.g., your Mac)**.

---

## 🗺️ Network Chain Overview

| Location        | Port    | Purpose |
|-----------------|---------|---------|
| Minikube inside WSL2 | 8888 | Kubernetes LoadBalancer service |
| WSL2 loopback   | 8888    | Access Minikube via `127.0.0.1:8888` |
| WSL2 (socat)    | 18888   | Bridges WSL2 → Windows |
| Windows host    | 28888   | Exposes port to LAN (e.g., your Mac) |

## 🔧 Step-by-Step

### 1. Expose the Service in Kubernetes

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

Run this and make sure `minikube tunnel` is running. Inside WSL2:

```bash
curl localhost:8888/health
# Should return {"status":"ok"}
```

---

### 2. Set Up socat in WSL2

```bash
socat TCP-LISTEN:18888,fork,reuseaddr TCP:127.0.0.1:8888
```

This bridges WSL2 port `18888` → Minikube service on `127.0.0.1:8888`.

---

### 3. Set Up Portproxy in PowerShell (on Windows)

First, find your WSL2 IP:

```bash
wsl hostname -I
```

Then set up the proxy:

```powershell
netsh interface portproxy add v4tov4 `
  listenport=8888 listenaddress=0.0.0.0 `
  connectport=18888 connectaddress=<WSL2-IP>
```

---

### 4. Open the Firewall

```powershell
netsh advfirewall firewall add rule name="ExposeAppOn8888" `
  dir=in action=allow protocol=TCP localport=8888
```

---

## ✅ Test Everything

- On Windows:
  ```powershell
  curl http://localhost:18888/health
  ```

- On LAN machine (Mac):
  ```bash
  curl http://<windows-ip>:28888/health
  ```

---

## 🧹 Cleanup

Remove portproxy:

```powershell
netsh interface portproxy delete v4tov4 listenport=28888 listenaddress=0.0.0.0
```

Kill socat in WSL2:

```bash
pkill -f "socat TCP-LISTEN"
```

---

## 🧠 Conceptual Diagram

```text
(Mac) --> (Windows Host) --> (WSL2) --> (Minikube)
 :28888      :28888           :18888     :8888
               |                |          |
          portproxy         socat     Kubernetes
```

---

# 🪟 Running Minikube on Windows for Easier LAN Access

> **NOTE**: This guide was generated with ChatGPT based on the provided context.

This guide explains how running Minikube using the Docker driver from Windows PowerShell simplifies service exposure to your Windows host and LAN devices—without `socat`, `portproxy`, or WSL networking tricks.

---

## 🗺️ Network Chain Overview

| Location          | Port | Purpose                        |
|-------------------|------|--------------------------------|
| Minikube cluster  | 8888 | Kubernetes LoadBalancer service |
| Windows host      | 8888 | Exposed directly via tunnel     |
| LAN device (Mac)  | 8888 | Can reach it via firewall rule  |

---

## 🚀 Why This Is Simpler Than WSL2 Setup

✅ **With Minikube on Windows (Docker driver)**:
- No WSL2: No virtualized networking layers.
- `minikube tunnel` runs on Windows, binding services to `localhost` or `0.0.0.0` directly.
- No need for `socat` or `netsh portproxy`.
- Only firewall configuration is needed to expose the service to the LAN.

❌ **With Minikube inside WSL2**:
- `minikube tunnel` runs inside the WSL2 VM.
- Services only available to WSL2 (`127.0.0.1` inside the VM).
- Requires bridging with `socat`, port forwarding via `portproxy`, and Windows firewall configuration.

---

## 🔧 Setup Guide

### 1. Start Minikube with Docker driver (on PowerShell)

```powershell
minikube start --driver=docker
```

This ensures the cluster runs in Docker directly accessible from Windows.

---

### 2. Deploy a Service with LoadBalancer Type

Example Kubernetes Service YAML:

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

Apply this with:

```bash
kubectl apply -f service.yaml
```

---

### 3. Run the Tunnel (on PowerShell)

```powershell
minikube tunnel
```

This binds the LoadBalancer service (e.g., kafka-producer) to `localhost:8888` on Windows.

---

### 4. Open the Port to LAN (Optional)

If you want to access it from another device on the LAN (e.g., Mac):

```powershell
netsh advfirewall firewall add rule name="ExposeKafkaProducer8888" `
  dir=in action=allow protocol=TCP localport=8888
```

Make sure your router allows LAN access to the Windows machine.

---

## ✅ Test Everything

- From **Windows**:

```powershell
curl http://localhost:8888/health
```

- From **LAN device (Mac)**:

```bash
curl http://<windows-ip>:8888/health
```

---

## 🧠 Conceptual Diagram

```text
(Mac) --> (Windows Host with Minikube) --> (Minikube Cluster)
 :8888             :8888                      :8888
                    |                          |
                firewall                 LoadBalancer
```

---

By using the Docker driver and running Minikube natively in PowerShell, you can eliminate WSL-specific network forwarding complexity, making it ideal for service development and LAN integration.