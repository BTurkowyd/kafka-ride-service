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