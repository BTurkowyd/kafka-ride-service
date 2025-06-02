build-images:
	@eval $$(minikube docker-env) && \
	docker build -t uber-consumer:latest -f consumers/Dockerfile . && \
	docker build -t uber-producer:latest -f producer/Dockerfile .

create-namespace:
	 kubectl apply -f k8s-manifests/k8s-namespace.yaml

add-common-env-config-map:
	kubectl create configmap common-env \
	  --from-env-file=.env \
	  -n uber-service

add-postgres-secrets:
	kubectl create secret generic postgres-secret \
	  --from-env-file=.env \
	  -n uber-service

create-resources:
	kubectl apply -f k8s-manifests/k8s-postgres.yaml && \
	kubectl apply -f k8s-manifests/k8s-kafka-zookeeper.yaml && \
	kubectl apply -f k8s-manifests/k8s-producer.yaml && \
	$(MAKE) deploy-consumers

deploy-consumers:
	$(MAKE) deploy-consumer name=ride-requested
	$(MAKE) deploy-consumer name=ride-started
	$(MAKE) deploy-consumer name=ride-completed
	$(MAKE) deploy-consumer name=location-update
	$(MAKE) deploy-consumer name=dlq

deploy-consumer:
	helm upgrade --install consumer-$(name) ./k8s-manifests/kafka-consumers-chart \
		-f k8s-manifests/kafka-consumers-chart/consumers/$(name).yaml

delete-consumers:
	helm uninstall consumer-ride-requested
	helm uninstall consumer-ride-started
	helm uninstall consumer-ride-completed
	helm uninstall consumer-location-update
	helm uninstall consumer-dlq

socat-ports:
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

socat-kill:
	@echo "Killing all socat processes..."
	@pkill -f "socat TCP-LISTEN"
