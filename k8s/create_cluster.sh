#!/bin/bash

# Create cockroach service
# Connection point for other services: cockroachdb-public
# Create python microservices
# Create ingress service
kubectl create \
 -f cockroachdb-statefulset.yaml \
 -f connection-manager.yaml \
 -f order-service.yaml \
 -f payment-service.yaml \
 -f stock-service.yaml \
 -f ingress-service.yaml

# One time database initialization
# kubectl create -f cluster-init.yaml
kubectl create -f database-init.yaml
