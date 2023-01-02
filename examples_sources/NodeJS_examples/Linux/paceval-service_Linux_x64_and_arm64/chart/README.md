# Guide for deploying the paceval-service on any Kubernetes (K8s) cluster

## Prerequisite

This guide describes how to easily set up your own Paceval service on Kubernetes using [Google Cloud Platform (GCP)](https://cloud.google.com/) with easy-to-follow steps. However, you can adopt it for any hyperscalar such as [Amazon Web Services (AWS)](https://aws.amazon.com/) or [Microsoft Azure](http://azure.microsoft.com/).

In short, you will need this:
- Kubernetes command-line tool, [kubectl](https://kubernetes.io/docs/tasks/tools/), allows you to run commands against Kubernetes clusters.
- [Helm CLI](https://helm.sh/docs/intro/install/) is a tool that streamlines installing and managing Kubernetes applications.
- Access to a running Kubernetes cluster with the Cluster Administrator role [cluster-admin](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#user-facing-roles) (in GCP, this also means your account must have the [Kubernetes Engine Admin](https://cloud.google.com/kubernetes-engine/docs/how-to/iam) role in IAM).

## Installation steps

### Connect to your kubernetes cluster
For any k8s cluster you can access the cluster using [kubeconfig](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/) file with kubectl, there is also UI based tool called [lens](https://k8slens.dev/).

For connecting to a GKE cluster specifically, check [here](https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-access-for-kubectl) ("Install kubectl and configure cluster access").
and wait until the helm chart is installed

### Install paceval helm chart

Now we can install the actual paceval helm chart 

in directory /paceval/examples_sources/NodeJS_examples/Linux/paceval-service_Linux_x64_and_arm64/chart/paceval/

run the following command: 

```shell
helm dep update
helm upgrade paceval . --install --debug 
```

### Wait for IP Address Allocation
run the waiting command and wait until an external IP (it is in initially pending) is available, use ctrl-c to exit the command.

```shell
kubectl get --namespace default svc -w paceval
NAME      TYPE           CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE
paceval   LoadBalancer   10.49.0.238   <pending>     80:30955/TCP   11d
paceval   LoadBalancer   10.49.0.238   34.116.196.28   80:30955/TCP   11d
```


## Call the service endpoint
Now your service is deployed on k8s cluster, you can make a test call like follows:
```shell
curl "http://<external-ip>/Demo/?functionString=x%2Ay-z&numberOfVariables=3&variables=x%3By%3Bz&values=0.534346%3B2%3B45.4536&interval=yes"
```
