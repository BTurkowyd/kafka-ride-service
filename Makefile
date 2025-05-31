build-images:
	@eval $$(minikube docker-env) && \
	docker build -t uber-consumer:latest -f consumers/Dockerfile . && \
	docker build -t uber-producer:latest -f producer/Dockerfile .

create-namespace:
	 kubectl apply -f k8s-manifests/namespace.yml

add-common-env-config-map:
	kubectl create configmap common-env \
	  --from-env-file=.env \
	  -n uber-service

add-postgres-secrets:
	kubectl create secret generic postgres-secret \
	  --from-env-file=.env \
	  -n uber-service

create-resources:
	kubectl apply -f k8s-manifests/k8s-postgres && \
	kubectl apply -f k8s-manifests/k8s-kafka-zookeeper.yaml && \
	kubectl apply -f k8s-manifests/k8s-consumers.yaml && \
	kubectl apply -f k8s-manifests/k8s-producer.yaml && \

socat-ports:
	# Kafka
	socat TCP-LISTEN:19094,fork,reuseaddr TCP:127.0.0.1:9094 &

	# Schema Registry
	socat TCP-LISTEN:18081,fork,reuseaddr TCP:127.0.0.1:8081 &

	# Postgres
	socat TCP-LISTEN:15432,fork,reuseaddr TCP:127.0.0.1:5432 &

	# Kafka UI
	socat TCP-LISTEN:18080,fork,reuseaddr TCP:127.0.0.1:8080 &


minikube-tunnel:
	minikube tunnel

deploy-all:
	make create-namespace
	make build-images
	make add-common-env-config-map
	make add-postgres-secrets
	make create-resources
	make socat-ports