# Guide for deploy paceval service to any k8s cluster

## Prerequisite

Please make sure you have followings before you start the installation steps
- kube control CLI ( i.e. [kubectl](https://kubernetes.io/docs/tasks/tools/))
- [helm cli](https://helm.sh/docs/intro/install/)
- access to a running kubernetes cluster with [cluster-admin](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#user-facing-roles) role (in GCP this also means you account need to have [Kubernetes Engine Admin](https://cloud.google.com/kubernetes-engine/docs/how-to/iam) role in IAM)


## Installation steps

### Connect to your kubernetes cluster
For any k8s cluster you can access the cluster using [kubeconfig](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/) file with kubectl, there is also UI based tool called [lens](https://k8slens.dev/).

For connecting to a GKE cluster specifically, check [here](https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-access-for-kubectl) ("Install kubectl and configure cluster access").


### Install helm chart nginx ingress controller

[nginx ingress controller](https://docs.nginx.com/nginx-ingress-controller/) is the tools helps to route incoming traffics into internal services.

in directory /paceval/examples_sources/NodeJS_examples/Linux/paceval-service_Linux_x64_and_arm64/chart/ingress-nginx/

run the following:
```shell
helm dep update
helm upgrade nginx-ingress . --install --debug
```

and wait until the helm chart is installed

### Install paceval helm chart

Now we can install the actual pavcval helm chart 
in directory chart/paceval

run the following,use your own [subdomain](#use-a-subdomain):
```shell
helm dep update
helm upgrade paceval . --install --debug \
    --set 'ingress.hosts[0].host=<your subdomain>' \
    --set 'ingress.hosts[0].paths[0].path=/' \
    --set 'ingress.hosts[0].paths[0].pathType=Prefix'
```


## Use a subdomain

If you want to use a DNS domain instead of IP address, please make sure you purchased and owning a domain (e.g. paceval.cloud)
You can use a subdomain to access the paceval service (e.g. `service.paceval.cloud`). Remember you should just use one level of subdomain,
subdomain such as `example.service.paceval.cloud` does not work. Now refer to [DNS guide](#setup-dns) for how to add the corresponding IP address to your DNS routing table.

## Setup DNS

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
