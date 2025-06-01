1. Start the infrastructure: `docker-compose up -d`. This will spin up the following services:
   - `postgres`: PostgreSQL database in which the data will be stored.
   - `zookeeper`: Zookeeper for managing Kafka brokers.
   - `kafka`: Kafka broker for message streaming.
   - `schema-registry`: Confluent Schema Registry for managing Avro schemas.
   - `kafka-ui`: Kafka UI for monitoring Kafka topics and messages.
   - Consumers, that will consume messages from Kafka topics, process them and store them in the PostgreSQL database.
2. Install `uv` and sync the environment: `uv sync`.
3. Create tables in the database. Use `scripts/sql/create_tables.sql` to create the necessary tables in the PostgreSQL database.
4. Populate the database with drivers and passengers. Use `scripts/sql/generate_drivers_passengers.py` 
to populate the database with sample data.
5. Run the Kafka producer with the command `uv run producers/producer.py`. This will start producing messages to the Kafka topics.

![kafka-based_event_pipeline.png](assets/kafka-based_event_pipeline.png)



# 🔌 Exposing Kubernetes Services from Minikube to External Machines
### NOTE: This guide was generated with ChatGPT based on the provided context.

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
  listenport=28888 listenaddress=0.0.0.0 `
  connectport=18888 connectaddress=<WSL2-IP>
```

---

### 4. Open the Firewall

```powershell
netsh advfirewall firewall add rule name="ExposeAppOn28888" `
  dir=in action=allow protocol=TCP localport=28888
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