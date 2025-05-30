build-consumer-image:
	@eval $$(minikube docker-env) && \
	docker build -t uber-consumer:latest -f consumers/Dockerfile .

create-namespace:
	 kubectl apply -f namespace.yml

add-common-env-config-map:
	kubectl create configmap common-env \
	  --from-env-file=.env \
	  -n uber-service

add-postgres-secrets:
	kubectl create secret generic postgres-secret \
	  --from-env-file=.env \
	  -n uber-service

create-resources:
	kubectl apply -f kubernetes.yml && \
	kubectl apply -f kafka-zk.yaml

pg-socat:
	socat TCP-LISTEN:15432,fork,reuseaddr TCP:127.0.0.1:5432

minikube-tunnel:
	minikube tunnel

deploy-all:
	make create-namespace
	make build-consumer-image
	make add-common-env-config-map
	make add-postgres-secrets
	make create-resources