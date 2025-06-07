# Improved Makefile for kafka-ride-service
# Features:
# - Idempotent ConfigMap and Secret creation
# - .PHONY targets
# - User feedback via @echo
# - Parameterization for namespace

NAMESPACE ?= uber-service
ENV_FILE ?= .env

.PHONY: build-images create-namespace add-common-env-config-map add-postgres-secrets create-resources deploy-consumers deploy-consumer delete-consumers socat-ports socat-kill clean deploy-monitoring delete-monitoring port-forward-grafana port-forward-prometheus

build-images:
	@echo "Building Docker images for producer and consumer..."
	@eval $$(minikube docker-env) && \
	docker build -t uber-consumer:latest -f consumers/Dockerfile . && \
	docker build -t uber-producer:latest -f producer/Dockerfile .

create-namespace:
	@echo "Applying namespace manifest..."
	kubectl apply -f k8s-manifests/k8s-namespace.yaml

add-common-env-config-map:
	@echo "Ensuring ConfigMap 'common-env' exists (idempotent)..."
	-@kubectl delete configmap common-env -n $(NAMESPACE) --ignore-not-found
	kubectl create configmap common-env \
	  --from-env-file=$(ENV_FILE) \
	  -n $(NAMESPACE)

add-postgres-secrets:
	@echo "Ensuring Secret 'postgres-secret' exists (idempotent)..."
	-@kubectl delete secret postgres-secret -n $(NAMESPACE) --ignore-not-found
	kubectl create secret generic postgres-secret \
	  --from-env-file=$(ENV_FILE) \
	  -n $(NAMESPACE)

create-resources:
	@echo "Applying all K8s resources..."
	kubectl apply -f k8s-manifests/k8s-postgres.yaml
	kubectl apply -f k8s-manifests/k8s-kafka-zookeeper.yaml
	kubectl apply -f k8s-manifests/k8s-producer.yaml
	$(MAKE) deploy-consumers

deploy-consumers:
	$(MAKE) deploy-consumer name=ride-requested
	$(MAKE) deploy-consumer name=ride-started
	$(MAKE) deploy-consumer name=ride-completed
	$(MAKE) deploy-consumer name=location-update
	$(MAKE) deploy-consumer name=dlq

deploy-consumer:
	@echo "Deploying consumer: $(name)"
	helm upgrade --install consumer-$(name) ./k8s-manifests/kafka-consumers-chart \
		-f k8s-manifests/kafka-consumers-chart/consumers/$(name).yaml

delete-consumers:
	@echo "Deleting all consumer releases..."
	helm uninstall consumer-ride-requested || true
	helm uninstall consumer-ride-started || true
	helm uninstall consumer-ride-completed || true
	helm uninstall consumer-location-update || true
	helm uninstall consumer-dlq || true

socat-ports:
	@echo "Forwarding local ports to services inside Minikube..."
	# Kafka
	socat TCP-LISTEN:19094,fork,reuseaddr TCP:127.0.0.1:9094 &
	# Schema Registry
	socat TCP-LISTEN:18081,fork,reuseaddr TCP:127.0.0.1:8081 &
	# Postgres
	socat TCP-LISTEN:15432,fork,reuseaddr TCP:127.0.0.1:5432 &
	# Kafka UI
	socat TCP-LISTEN:18080,fork,reuseaddr TCP:127.0.0.1:8080 &
	# Producer
	socat TCP-LISTEN:18888,fork,reuseaddr TCP:127.0.0.1:8888 &
	# Prometheus
	socat TCP-LISTEN:19090,fork,reuseaddr TCP:127.0.1:9090 &
	# Grafana
	socat TCP-LISTEN:13000,fork,reuseaddr TCP:127.0.1:3000 &

socat-kill:
	@echo "Killing all socat processes..."
	@pkill -f "socat TCP-LISTEN"


deploy-monitoring:
	@echo "Deploying Prometheus and Grafana (idempotent)..."
	helm repo add prometheus-community https://prometheus-community.github.io/helm-charts || true
	helm repo add grafana https://grafana.github.io/helm-charts || true
	helm repo update
	helm upgrade --install prometheus prometheus-community/prometheus --namespace monitoring --create-namespace
	helm upgrade --install grafana grafana/grafana --namespace monitoring --create-namespace
	@echo "Grafana admin password:"
	kubectl get secret --namespace monitoring grafana -o jsonpath="{.data.admin-password}" | base64 --decode ; echo

delete-monitoring:
	@echo "Deleting Prometheus and Grafana..."
	helm uninstall prometheus -n monitoring || true
	helm uninstall grafana -n monitoring || true

port-forward-grafana:
	kubectl port-forward svc/grafana 3000:80 -n monitoring

port-forward-prometheus:
	kubectl port-forward svc/prometheus-server 9090:80 -n monitoring

clean:
	@echo "Cleaning up all resources..."
	kubectl delete -f k8s-manifests/k8s-postgres.yaml --ignore-not-found
	kubectl delete -f k8s-manifests/k8s-kafka-zookeeper.yaml --ignore-not-found
	kubectl delete -f k8s-manifests/k8s-producer.yaml --ignore-not-found
	kubectl delete configmap common-env -n $(NAMESPACE) --ignore-not-found
	kubectl delete secret postgres-secret -n $(NAMESPACE) --ignore-not-found
	$(MAKE) delete-consumers