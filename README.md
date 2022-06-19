# Web-scale Data Management Project Template

Basic project structure with Python's Flask and Redis. 
**You are free to use any web framework in any language and any database you like for this project.**

### Project structure

* `env`
    Folder containing the Redis env variables for the docker-compose deployment
    
* `helm-config` 
   Helm chart values for Redis and ingress-nginx
        
* `k8s`
    Folder containing the kubernetes deployments, apps and services for the ingress, order, payment and stock services.
    
* `order`
    Folder containing the order application logic and dockerfile. 
    
* `payment`
    Folder containing the payment application logic and dockerfile. 

* `stock`
    Folder containing the stock application logic and dockerfile. 

* `test`
    Folder containing some basic correctness tests for the entire system. (Feel free to enhance them)

### Deployment types:

#### docker-compose (local development)

After coding the REST endpoint logic run `docker-compose up --build` in the base folder to test if your logic is correct
(you can use the provided tests in the `\test` folder and change them as you wish). 

***Requirements:*** You need to have docker and docker-compose installed on your machine.

#### minikube (local k8s cluster)

***Start Up***
* ```minikube start --extra-config=kubelet.housekeeping-interval=10s```
* ```minikube addons enable metrics-server```
* ```minikube addons enable ingress```
* ```minikube docker-env``` 

COPY PASTE OUTPUT: 

***For Windows users also run:*** ```@FOR /f "tokens=*" %i IN ('minikube -p minikube docker-env --shell cmd') DO @%i```

```cd ./k8s/```

* ```docker build order -t order:latest```
* ```docker build payment -t payment:latest```
* ```docker build stock -t stock:latest```
* ```docker build connection_manager -t connection-manager:latest```
* ```docker build db-init -t db-init:latest```

#### Create the cluster
```./create_cluster.sh```

#### Setup the auto scaling for the pods
* ```kubectl -n kube-system rollout status deployment metrics-server```
* ```kubectl autoscale deployment stock-deployment --cpu-percent=50 --min=1 --max=3```
* ```kubectl autoscale deployment order-deployment --cpu-percent=50 --min=1 --max=3```
* ```kubectl autoscale deployment payment-deployment --cpu-percent=50 --min=1 --max=3```

#### Connecting to the dashboard
* ```minikube tunnel```
* ```minikube dashboard```

***Delete old minikubes***
```kubectl delete -f .\cockroachdb-statefulset.yaml -f .\connection-manager.yaml -f .\order-service.yaml -f .\payment-service.yaml -f .\stock-service.yaml -f .\ingress-service.yaml -f .\database-init.yaml```