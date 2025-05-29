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


## 🌐 Accessing PostgreSQL in Minikube from Another Machine on Local Network

### 🐘 The Problem

Minikube is running inside a **Docker container**, which is launched from **WSL2** (a lightweight Linux VM on Windows).  
This creates a deeply nested environment:

```
[Other machine] → [Windows Host] → [WSL2 VM] → [Docker] → [Kubernetes pod]
```

Even though your PostgreSQL pod has a Kubernetes `LoadBalancer` service, it’s only accessible from **inside** this nested chain — not from other devices on your LAN.

---

### ✅ The Solution

To expose PostgreSQL externally, you need to bridge the layers manually:

1. **Start the Minikube tunnel (inside WSL2)**  
   This maps Kubernetes `LoadBalancer` services to the WSL2 loopback.

   ```bash
   sudo minikube tunnel
   ```

2. **Forward WSL2 port to Minikube service using `socat`**

   Replace `192.168.49.2` with the actual IP of your PostgreSQL service inside Minikube:

   ```bash
   socat TCP-LISTEN:15432,fork,reuseaddr TCP:192.168.49.2:5432
   ```
    This command listens on port `15432` in WSL2 and forwards it to the PostgreSQL service running in Minikube.


3. **Forward Windows port to WSL2 using `netsh`**

   Replace `<WSL2-IP>` with your actual WSL2 IP (e.g. `172.20.143.18` — find it via `wsl hostname -I`):

   ```powershell
   netsh interface portproxy add v4tov4 `
     listenport=5432 listenaddress=0.0.0.0 `
     connectport=15432 connectaddress=<WSL2-IP>
   ```
    This command forwards all traffic on port `5432` of your Windows host to the `15432` port in WSL2, which is listening for PostgreSQL connections.


4. **Allow port 5432 through Windows Firewall (if needed)**

   ```powershell
   netsh advfirewall firewall add rule name="Postgres K8s" `
     dir=in action=allow protocol=TCP localport=5432
   ```

---

### 🧪 Result

You can now connect to your PostgreSQL service running in Kubernetes from **any machine on the same LAN** using:

```bash
psql -h <Windows-IP> -p 5432 -U <user> -d <db>
```

This setup avoids using Ingress or cloud load balancers — all local, all manual, and works beautifully.

A similar approach can be used for other services like Kafka, Redis, etc.

## 🔌 Accessing Kafka UI from LAN

When running Minikube inside Docker via WSL2, `LoadBalancer` services (like Kafka UI) are not directly reachable from other machines on the network.

To expose Kafka UI externally, apply this manual bridge:

### ✅ Kafka UI External Access

1. **Start the Minikube tunnel inside WSL2:**

   ```bash
   sudo minikube tunnel
   ```

2. **Forward WSL2 port to Minikube service via `socat`:**

   Find the Kafka UI LoadBalancer IP:

   ```bash
   kubectl get svc kafka-ui -n uber-service
   ```

   Then forward:

   ```bash
   socat TCP-LISTEN:18080,fork,reuseaddr TCP:<EXTERNAL-IP>:8080
   ```

3. **Forward Windows port to WSL2 using `netsh` (PowerShell):**

   ```powershell
   netsh interface portproxy add v4tov4 `
     listenport=18080 listenaddress=0.0.0.0 `
     connectport=18080 connectaddress=<WSL2-IP>
   ```

   Find WSL2 IP via `wsl hostname -I`.

4. **(Optional) Allow through Windows Firewall:**

   ```powershell
   netsh advfirewall firewall add rule name="Kafka UI K8s" `
     dir=in action=allow protocol=TCP localport=18080
   ```

### 🧪 Result

You can now access Kafka UI from any device on your local network via:

```
http://<Windows-IP>:18080
```

---
