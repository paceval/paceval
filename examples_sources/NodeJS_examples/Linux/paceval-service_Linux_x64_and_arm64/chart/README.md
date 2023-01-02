# Guide for deploying the paceval-service on any Kubernetes (K8s) cluster

## Prerequisite

This guide describes how to easily set up your own paceval-service on Kubernetes using [Google Cloud Platform (GCP)](https://cloud.google.com/) with easy-to-follow steps. However, you can adopt it for any hyperscalar such as [Amazon Web Services (AWS)](https://aws.amazon.com/) or [Microsoft Azure](http://azure.microsoft.com/).

In short, you will need this:
- Kubernetes command-line tool, [kubectl](https://kubernetes.io/docs/tasks/tools/), allows you to run commands against Kubernetes clusters.
- [Helm CLI](https://helm.sh/docs/intro/install/) is a tool that streamlines installing and managing Kubernetes applications.
- Access to a running Kubernetes cluster with the Cluster Administrator role [cluster-admin](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#user-facing-roles) (in GCP, this also means your account must have the [Kubernetes Engine Admin](https://cloud.google.com/kubernetes-engine/docs/how-to/iam) role in IAM).

## Installation steps

As a first step, create an empty project and enable the Kubernets Engine APIs. 

In GCP, creating an empty project is done through the [Google Cloud console](https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=&cad=rja&uact=8&ved=2ahUKEwiAsPaz-qj8AhUGm_0HHV_4AjcQFnoECA0QAQ&url=https%3A%2F%2Fcloud.google.com%2Fresource-manager%2Fdocs%2Fcreating-managing-projects&usg=AOvVaw2rNNmaoita-LBuwPL3xncu). Click the Project dropdown menu, then click "NEW PROJECT".
Then select the project and [enable the Kubernetes Engine APIs](https://console.cloud.google.com/marketplace/product/google/container.googleapis.com) from the Google Cloud console.

### Connect to your kubernetes cluster

For any Kubernetes cluster, you can access the cluster from the [kubeconfig](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/) file using kubectl, there is also a UI-based tool called [Lens](https://k8slens.dev/).

To connect to a cluster in GCP, specifically install the [Google Cloud CLI (gcloud CLI)](https://cloud.google.com/sdk/docs/install). Start the Google Cloud CLI and [install kubectl](https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-access-for-kubectl) (the gke-gcloud-auth-plugin will also be installed):
```shell
gcloud components install kubectl
```

To generate the kubeconfig entry, run this:
```shell
gcloud container clusters get-credentials <cluster-name> --region=<region-name>
```

For example:
```shell
gcloud container clusters get-credentials autopilot-cluster-1 --region=europe-central2
```

You can test the configuration with this:
```shell
kubectl get namespaces
```

### Install paceval. Helm Chart

Now you can install the actual paceval. Helm Chart. In directory /paceval/examples_sources/NodeJS_examples/Linux/paceval-service_Linux_x64_and_arm64/chart/paceval/ run the following commands: 

```shell
helm dep update
helm upgrade paceval . --install --debug 
```

In the GCP you stay in the Google Cloud CLI, change to the directory for the paceval. Helm chart. From there, run the commands in the Google Cloud CLI.

### Wait for IP Address Allocation

It may take a few minutes for the LoadBalancer's external IP address to be available.
You can view the status with this command (use Ctrl + C to end the command):

```shell
kubectl get --namespace default svc -w paceval
```

You will get an output similar to this:

```shell
NAME      TYPE           CLUSTER-IP    EXTERNAL-IP     PORT(S)        AGE
paceval   LoadBalancer   10.49.0.238   34.116.196.28   80:30632/TCP   7m28s
```

## Call the paceval-service endpoint

Note down your LoadBalancer's external IP address (see EXTERNAL-IP above). 
Now the paceval-service is deployed on your Kubernetes cluster and you can make a test call as follows (use your LoadBalancer's external IP address):

```shell
curl --data "functionString=-sin(x*cos(x))^(1/y)&numberOfVariables=2&variables=x;y&values=0.5;2&interval=yes" -X POST http://<EXTERNAL-IP>/Demo/
```

You will get a response similar to this from your paceval-service:

```shell
{"handle_pacevalComputation":139698524825392,"result":"-0.651801782452278","interval-min-result":"-0.651801782452306","interval-max-result":"-0.65180178245225","error-type-number":0,"error-position":"","error-type":"[NO ERROR]","error-message":"No error has occurred for this computation object (PACEVAL_ERR_NO_ERROR).","time-calculate":"0.056092s","version-number":4.04}
```

(see [paceval at SwaggerHub](https://app.swaggerhub.com/apis-docs/paceval/paceval-service/4.04) for more information)
