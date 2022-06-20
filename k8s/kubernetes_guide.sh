#!/bin/bash

kubectl create -f cockroachdb-statefulset.yaml
# Connection point for other services: cockroachdb-public

# One time initialisation of cluster
kubectl create -f cluster-init.yaml

# Access cockroach management console
kubectl port-forward service/cockroachdb-public 8080

# Manually run SQL queries on the database
kubectl run cockroachdb -it --image=cockroachdb/cockroach:v22.1.0 --rm --restart=Never -- sql --insecure --host=cockroachdb-public

# Scale up
kubectl scale statefulset cockroachdb --replicas=6

# Scale down
# get ids:
kubectl run cockroachdb -it --image=cockroachdb/cockroach:v22.1.0 --rm --restart=Never -- node status --insecure --host=cockroachdb-public
# decommission all ids higher than the new replica count
kubectl run cockroachdb -it --image=cockroachdb/cockroach:v22.1.0 --rm --restart=Never -- node decommission 4 5 6 --insecure --host=cockroachdb-public
# scale the cockroach service to stop the decommissioned nodes
kubectl scale statefulset cockroachdb --replicas=3
# find volumes and check if they are no longer used by
kubectl get pvc
kubectl describe pvc datadir-cockroachdb-3 datadir-cockroachdb-4 datadir-cockroachdb-5
# delete the persistent volumes
kubectl delete pvc datadir-cockroachdb-3 datadir-cockroachdb-4 datadir-cockroachdb-5
