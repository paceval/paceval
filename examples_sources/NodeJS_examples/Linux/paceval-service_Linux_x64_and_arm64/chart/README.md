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

and wait until the helm chart is installed

### Install paceval helm chart

Now we can install the actual paceval helm chart 
in directory chart/paceval

run the following command: 
```shell
helm dep update
helm upgrade paceval . --install --debug 
```

### Wait for IP Address Allocation
run the waiting command and wait until an external IP (it is in initially pending), once you see an external ip is available, use ctrl-c to exit the command.
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
