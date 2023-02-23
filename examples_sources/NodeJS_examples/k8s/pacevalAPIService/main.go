package main

import (
	"encoding/json"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"log"
	"net/http"
	"os"

	pacevalv1alpha1 "github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/operator/api/v1alpha1"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
)

type PacevalComputationObject struct {
	ID     int    `json:"id"`
	Name   string `json:"name"`
	Status string `json:"status"`
}

var (
	apiVersion   = "paceval.com/v1alpha1"
	kind         = "PacevalComputationObject"
	group        = "paceval.com"
	resourceName = "pacevalcomputations"
)

func main() {
	config, err := rest.InClusterConfig()
	if err != nil {
		// If not running inside a Kubernetes cluster, use the default kubeconfig file.
		kubeconfig := os.Getenv("HOME") + "/.kube/config"
		config, err = clientcmd.BuildConfigFromFlags("", kubeconfig)
		if err != nil {
			log.Fatalf("Failed to get Kubernetes config: %v", err)
		}
	}

	client, err := dynamic.NewForConfig(config)
	if err != nil {
		log.Fatalf("Failed to create Kubernetes client: %v", err)
	}

	http.HandleFunc("/pacevalcomputations", handlePacevalComputations(client))
	log.Fatal(http.ListenAndServe(":8080", nil))
}

func handlePacevalComputations(client dynamic.Interface) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			getPacevalComputations(client, w)
		//case http.MethodPost:
		//	createPacevalComputation(client, w, r)
		default:
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		}
	}
}

func getPacevalComputations(client dynamic.Interface, w http.ResponseWriter) {
	gvr := schema.GroupVersionResource{Group: group, Version: apiVersion, Resource: resourceName}
	obj, err := client.Resource(gvr).List(r.Context(), metav1.ListOptions{})
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	pacevalComputations := []pacevalv1alpha1.PacevalComputationObject{}
	for _, item := range obj.Items {
		var pacevalComputation PacevalComputationObject
		err := json.Unmarshal(item.Object["spec"].([]byte), &pacevalComputation)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		pacevalComputations = append(pacevalComputations, pacevalComputation)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(pacevalComputations)
}
