# Guide for deploying the Kubernetes native paceval-service on any cluster

## Introduction

### System diagram

![paceval_system_diagram.png](paceval_system_diagram.png)

The Paceval service in k8s consist of the following components

1. Paceval API Service handle external request from user
   1. request **createComputation**: create CRD `pacevalcomputationobject` when creating computation
   2. requests **getComputation**, **getComputationResult** , **getComputationResult**, **GetComputationResultExt**,**GetComputationInformationXML**,**GetErrorInformation**:
   reserve proxy user request to respective computation object
   3. request **Demo**: forward request to demo service and create a CRD `pacevalcomputationobject` based on the request (noted that the creating of computation take some time)
   4. request **GetMultipleComputationsResults**: forward request to multiple computation object in parallel and return an array of ordered results
   5. It has healthiness and readiness endpoint for k8s to know it health status
2. Paceval computation Object
   1. This is a version of nodejs paceval-server when the function parameter (in environment variables) loaded upon started up, it is owned by CRD `pacevalcomputationobject`
   2. It has healthiness and readiness endpoint for k8s to know it health status

3. Paceval K8S operator
   1. The operator create/delete the k8s deployment, service as well as HPA (horizontal pod autoscaler) of Paceval computation Object based on the existence of  CRD `pacevalcomputationobject`
   2. It has healthiness and readiness endpoint for k8s to know it health status

4. Paceval Demo service
   1. This is a version of nodejs paceval-server when the function parameter is loaded using endpoint `createComputation`. It allow faster return of result. The function created will be delete in 2 seconds
   2. It has healthiness and readiness endpoint for k8s to know it health status

5. Delete old paceval object
   This is a k8s cronjob that triggered every 5 mins. It detect CRDs that has not been active in one hours and delete the CRD.

Remarks:

If you want to replace the paceval library, please make sure to replace them in both components: [Paceval computation Object](https://github.com/paceval/paceval/tree/main/examples_sources/NodeJS_examples/k8s/pacevalComputationService) & [Paceval Demo service](https://github.com/paceval/paceval/tree/main/examples_sources/NodeJS_examples/k8s/demoService)

## Installation Step

### Prerequisite

This guide describes how to set up your own paceval-service on Kubernetes using [Google Cloud Platform (GCP)](https://cloud.google.com/) with easy-to-follow steps. However, you can adopt it for any hyperscalar such as [Amazon Web Services (AWS)](https://aws.amazon.com/) or [Microsoft Azure](http://azure.microsoft.com/).

In short, you will need this:
- Kubernetes command-line tool, [kubectl](https://kubernetes.io/docs/tasks/tools/), allows you to run commands against Kubernetes clusters.
- Access to a running Kubernetes cluster with the Cluster Administrator role [cluster-admin](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#user-facing-roles) (in GCP, this also means your account must have the [Kubernetes Engine Admin](https://cloud.google.com/kubernetes-engine/docs/how-to/iam) role in IAM).

## Installation steps

As a first step, create an empty project and enable the Kubernets Engine APIs.

In GCP, creating an empty project is done through the [Google Cloud console](https://www.google.com/url?sa=t&rct=j&q=&esrc=s&source=web&cd=&cad=rja&uact=8&ved=2ahUKEwiAsPaz-qj8AhUGm_0HHV_4AjcQFnoECA0QAQ&url=https%3A%2F%2Fcloud.google.com%2Fresource-manager%2Fdocs%2Fcreating-managing-projects&usg=AOvVaw2rNNmaoita-LBuwPL3xncu). Click the Project dropdown menu, then click "NEW PROJECT".
Then select the project and [enable the Kubernetes Engine APIs](https://console.cloud.google.com/marketplace/product/google/container.googleapis.com) from the Google Cloud console.

### Create a Kubernetes cluster

In general, you have two options in [Google Cloud Platform (GCP)](https://cloud.google.com/) to create a new Kubernetes cluster.

Option 1. The easiest way to create a new Kubernetes cluster with GCP is the so-called [autopilot mode](https://cloud.google.com/kubernetes-engine/docs/concepts/types-of-clusters). Just follow these steps for autopilot mode: [Create an Autopilot cluster](https://cloud.google.com/kubernetes-engine/docs/how-to/creating-an-autopilot-cluster)

Option 2. If you are more experienced with configuring Kubernetes and specifically want to benefit from performance, you should use the [standard method](https://cloud.google.com/kubernetes-engine/docs/concepts/types-of-clusters) in GCP. To create a new standard cluster using Google Kubernetes Engine (GKE), run the following command (please replace  `<gcp-project-name>` with your own GCP project name and `<cluster-name>` with your own cluster name):

```shell
gcloud beta container --project <gcp-project-name> clusters create <cluster-name> --zone "europe-central2-a" --no-enable-basic-auth --cluster-version "1.25.6-gke.1000" --release-channel "regular" --machine-type "e2-medium" --image-type "COS_CONTAINERD" \
 --disk-type "pd-balanced" --disk-size "100" --metadata disable-legacy-endpoints=true \
 --scopes "https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append" \
 --max-pods-per-node "110" --num-nodes "3" --logging=SYSTEM,WORKLOAD --monitoring=SYSTEM --enable-ip-alias --network "projects/optimal-buffer-368615/global/networks/default" --subnetwork "projects/optimal-buffer-368615/regions/europe-central2/subnetworks/default" \
 --no-enable-intra-node-visibility --default-max-pods-per-node "110" --no-enable-master-authorized-networks --addons HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver --enable-autoupgrade --enable-autorepair --max-surge-upgrade 1 \
 --max-unavailable-upgrade 0 --enable-autoprovisioning --min-cpu 1 --max-cpu 20 --min-memory 1 --max-memory 1000 --autoprovisioning-locations=europe-central2-a --enable-autoprovisioning-autorepair --enable-autoprovisioning-autoupgrade --autoprovisioning-max-surge-upgrade 1 \
 --autoprovisioning-max-unavailable-upgrade 0 --enable-shielded-nodes --node-locations "europe-central2-a"
```

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
gcloud container clusters get-credentials paceval-dev --region=europe-central2 --project optimal-buffer-368615
```

You can test the configuration with this:
```shell
kubectl get namespaces
```

### Install Redius cluster

To install redis cluster
```shell
kubectl create ns redis
kubectl apply -f examples_sources/NodeJS_examples/k8s/redis/redius-template.yaml
```

and wait all stateful sets to be ready, master has one pods and slave has three pods 
```shell
kubectl get statefulsets -n redis
NAME             READY   AGE
redis-master     1/1     8m29s
redis-replicas   3/3     8m28s
```
this process will be ready long in GKW autopilot cluster because lots of VM has to be added into the node pool

To uninstall, run the following command
```shell
kubectl delete -f examples_sources/NodeJS_examples/k8s/redis/redius-template.yaml
kubectl delete ns redis
```

### Install paceval operator
To install, run the following command
```shell
kubectl apply -f examples_sources/NodeJS_examples/k8s/operator/template/operator-manifest.yaml
```
Potentially you will have to change the path to your local GitHub

and wait for deployment to be complete
```shell
kubectl get deployment operator-controller-manager -n operator-system        
NAME                          READY   UP-TO-DATE   AVAILABLE   AGE
operator-controller-manager   1/1     1            1           99s
```
To uninstall, run the following command
```shell
kubectl delete -f examples_sources/NodeJS_examples/k8s/operator/template/operator-manifest.yaml
```

If `Ready` is 1/1 then it is ready

### Install paceval API service
To install, run the following command
```shell
kubectl apply -f examples_sources/NodeJS_examples/k8s/pacevalAPIService/chart/api-service-manifest.yaml
```
and wait for deployment to be complete
```shell
kubectl get deployment api-service-apiservice                                                          
NAME                     READY   UP-TO-DATE   AVAILABLE   AGE
api-service-apiservice   1/1     1            1           20s
```
To uninstall, run the following command
```shell
kubectl delete -f examples_sources/NodeJS_examples/k8s/pacevalAPIService/chart/api-service-manifest.yaml
```

### Install paceval demo service
To install, run the following command
```shell
kubectl apply -f examples_sources/NodeJS_examples/k8s/demoService/chart/demo-service-manifest.yaml
```
and wait for deployment to be complete
```shell
kubectl get deployment demo-service-demoservice
NAME                       READY   UP-TO-DATE   AVAILABLE   AGE
demo-service-demoservice   1/1     1            1           100s
```
To uninstall, run the following command
```shell
kubectl delete -f examples_sources/NodeJS_examples/k8s/demoService/chart/demo-service-manifest.yaml
```

### Wait/Check for API Service external IP Address Allocation

It may take a few minutes for the LoadBalancer's external IP address to be available.
You can view the status with this command (use Ctrl + C to end the command):

```shell
kubectl get svc api-service-apiservice
```

You will get an output similar to this:

```shell
NAME                     TYPE           CLUSTER-IP    EXTERNAL-IP    PORT(S)        AGE
api-service-apiservice   LoadBalancer   10.49.7.202   34.118.106.7   80:30726/TCP   5m
```

## Call the paceval-service endpoint

Note down your LoadBalancer's external IP address (see EXTERNAL-IP above).
Now the paceval-service is deployed on your Kubernetes cluster and you can make a test call as follows (use your LoadBalancer's external IP address):

```shell
curl --location --request GET 'http://<EXTERNAL-IP>/Demo/?functionString=x%2Ay-z&numberOfVariables=3&variables=x%3By%3Bz&values=0.534346%3B2%3B45.4536&interval=yes'
```

You will get a response similar to this from your paceval-service:

```shell
{"error-message":"No error has occurred for this computation object (PACEVAL_ERR_NO_ERROR).","error-position":"","error-type":"[NO ERROR]","error-type-number":0,"handle_pacevalComputation":"6dd3ac29-beb3-11ed-989c-a2a45b63c3f5","interval-max-result":"-44.384908","interval-min-result":"-44.384908","result":"-44.384908","time-calculate":"0.000203s","version-number":4.04}
```

## Limitation for GCP Autopilot K8s cluster
1. When cluster resource (e.g. vCPU, memory) is not sufficient when installing/use service. GCP automatically trys to add more VM into the cluster (i.e. scale out). The process take time. So you can find occasionally your computation object take mins to be ready.
2. There is a quota limit in GCP where your cluster are not allowed to scale up beyond the limit. In this case, please request to Google to increase the quotas.
![quotas.png](quotas.png)
For details, see reference [here](https://cloud.google.com/compute/resource-usage?_ga=2.58764011.-75868254.1678303802&_gac=1.156671177.1678389429.Cj0KCQiApKagBhC1ARIsAFc7Mc6pL5xk0PfPUtgXTWQmokAHkssCS_WzA087GiRw3Miou6V4LuUZ7zQaAuvjEALw_wcB#requesting_additional_quota)



## API Definition
Refer to the new [openAPI definition](swagger.yaml) for the APIs.
