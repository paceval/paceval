# Guide for deploy paceval service to any k8s cluster

## Prerequisite

Please make sure you have followings before ypu start the installation steps
- kube control CLI ( i.e. [kubectl](https://kubernetes.io/docs/tasks/tools/))
- [helm cli](https://helm.sh/docs/intro/install/)
- access to a running kubernetes cluster with [cluster-admin](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#user-facing-roles) role (in GCP this also means you account need to have [Kubernetes Engine Admin](https://cloud.google.com/kubernetes-engine/docs/how-to/iam) role in IAM)


## Installation steps

### Connect to your kubernetes cluster
For any k8s cluster you can access the cluster using [kubeconfig](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/) file with kubectl, there is also UI based tool called [lens](https://k8slens.dev/).

For connecting to a GKE cluster specifically, check [here](https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-access-for-kubectl).


### install helm chart nginx ingress controller

[nginx ingress controller](https://docs.nginx.com/nginx-ingress-controller/) is the tools helps to route traffic coming into k8s ingress into internal services.

in directory ingress-ngix/

run the following:
```shell
helm dep update
helm upgrade nginx-ingress . --install --debug
```

and wait until the helm chart is installed

### install paceval helm chart

Now we can install the actual pavcval helm chart 
in directory chart/paceval

run the following:
```shell
helm dep update
helm upgrade paceval . --install --debug
```

## setup DNS

Wait until the k8s ingress of paceval has been assigned an IP address. You can check it with following command
```shell
% kubectl get ingresses paceval
NAME      CLASS   HOSTS                   ADDRESS         PORTS   AGE
paceval   nginx   service.paceval.cloud   34.118.104.45   80      2d
```

Add an A record into your DNS provider. Here is an example in Google Cloud DNS
![GCP-DNS.png](assets%2FGCP-DNS.png)


## Call the service endpoint
Now your service is deployed on k8s cluster, you can make a test call like follows:
```shell
curl "http://service.paceval.cloud/Demo/?functionString=x%2Ay-z&numberOfVariables=3&variables=x%3By%3Bz&values=0.534346%3B2%3B45.4536&interval=yes"
```
