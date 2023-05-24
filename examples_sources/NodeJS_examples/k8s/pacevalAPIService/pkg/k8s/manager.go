package k8s

import (
	"context"
	"fmt"
	"github.com/google/uuid"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/data"
	"github.com/rs/zerolog/log"
	v1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
	"os"
)

var (
	gvk = schema.GroupVersionKind{
		Group:   "paceval.com",
		Version: "v1alpha1",
		Kind:    "PacevalComputationObject",
	}
	gvr = schema.GroupVersionResource{
		Group:    "paceval.com",
		Version:  "v1alpha1",
		Resource: "pacevalcomputationobjects",
	}
)

const finalizerName = "paceval-controller.finalizer.paceval.com"

// Manager is a struct to access k8s client
type Manager struct {
	client dynamic.Interface
}

// NewK8sManager create a new k8s manager
func NewK8sManager() Manager {
	clientset, err := getClientSet()

	if err != nil {
		log.Fatal().Msgf("fatal error: %s", err)
		panic("fail to get the clientset")
	}

	_, present := os.LookupEnv("REDIS_ADDRESS")
	if !present {
		log.Fatal().Msg("fatal error: env var REDIS_ADDRESS not set")
		panic("fail to get the redis client")
	}

	return Manager{
		client: clientset,
	}

}

// getClientSet return the k8s dynamic clientset dynamic.Interface
func getClientSet() (dynamic.Interface, error) {
	config, err := rest.InClusterConfig()
	if err != nil {
		// If not running inside a Kubernetes cluster, use the default kubeconfig file.
		kubeconfig := os.Getenv("HOME") + "/.kube/config"
		config, err = clientcmd.BuildConfigFromFlags("", kubeconfig)
		if err != nil {
			return nil, err
		}
	}

	client, err := dynamic.NewForConfig(config)
	if err != nil {
		return nil, err
	}

	return client, nil
}

// CreateComputation create the computation CRD according to the configuration given in params
func (r Manager) CreateComputation(id uuid.UUID, params *data.ParameterSet) (string, error) {
	log.Info().Msgf("create computation on function id %s", id.String())
	instanceName := fmt.Sprintf("paceval-computation-%s", id.String())
	obj := unstructured.Unstructured{}
	obj.SetGroupVersionKind(gvk)
	obj.SetName(instanceName)
	obj.SetNamespace(data.DEFAULTNAMESPACE)
	obj.SetFinalizers([]string{finalizerName})

	variables := params.Variables

	if len(variables) == 0 {
		variables = "empty"
	}

	spec := make(map[string]interface{})
	spec["Internal"] = params.Interval
	spec["NumOfVars"] = params.NumOfVariables
	spec["Vars"] = variables
	spec["functionId"] = id.String()

	if len(params.FunctionStr) < 10000 {
		// if the length of params is short, then save the functionStr into CRD directly
		spec["functionStr"] = params.FunctionStr
	} else {
		// if the length of params is too long, then save the functionStr into redis and save the redis key into CRD
		address := os.Getenv("REDIS_ADDRESS")

		redisClient := data.NewRedis(address)

		// the redis key starts with string "redis-"
		key := "redis-" + id.String()
		err := redisClient.Set(key, params.FunctionStr)

		if err != nil {
			log.Error().Msgf("error saving value in redis: %s", err)
			return "", nil
		}

		// save the redis key into CRD
		spec["functionStr"] = key

		defer redisClient.CloseConnection()
	}

	obj.Object["spec"] = spec

	_, err := r.client.Resource(gvr).Namespace(data.DEFAULTNAMESPACE).Create(context.TODO(), &obj, metav1.CreateOptions{})

	if err != nil {
		log.Error().Msgf("Error when creating computation: %s", err)
		return "", err
	}

	return id.String(), nil
}

// GetEndpoint get endpoint from CRD instance
func (r Manager) GetEndpoint(id string) (string, error) {
	return r.getAndUpdateInstanceProperty(id, "status", "endpoint")
}

// GetNumOfVariables get numbers of variables from CRD instance
func (r Manager) GetNumOfVariables(id string) (string, error) {
	return r.getInstanceProperty(id, "spec", "NumOfVars")
}

func (r Manager) GetFunctionStr(id string) (string, error) {
	return r.getInstanceProperty(id, "spec", "functionStr")
}

func (r Manager) getInstanceProperty(id string, path string, property string) (string, error) {
	instanceName := fmt.Sprintf("paceval-computation-%s", id)
	instance, err := r.client.Resource(gvr).Namespace(data.DEFAULTNAMESPACE).Get(context.TODO(), instanceName, metav1.GetOptions{})

	if err != nil {
		return "", err
	}

	attr, _, err := unstructured.NestedString(instance.Object, path, property)

	if err != nil {
		return "", err
	}

	log.Info().Msgf("property: %s", attr)

	return attr, nil
}

// getAndUpdateInstanceProperty get a property from CRD instance and update the active timestamp
func (r Manager) getAndUpdateInstanceProperty(id string, path string, property string) (string, error) {
	instanceName := fmt.Sprintf("paceval-computation-%s", id)
	instance, err := r.client.Resource(gvr).Namespace(data.DEFAULTNAMESPACE).Get(context.TODO(), instanceName, metav1.GetOptions{})

	if err != nil {
		return "", err
	}

	ready, err := r.checkServiceReady(instance)

	if err != nil {
		return "", err
	}

	if !ready {
		return "", data.ServiceNotReadyError{}
	}

	err = r.updateLastActiveTimeStamp(instance)

	if err != nil {
		return "", err
	}

	return r.getInstanceProperty(id, path, property)
}

// updateLastActiveTimeStamp update the CRD.status.lastActiveTime to current timestamp
func (r Manager) updateLastActiveTimeStamp(instance *unstructured.Unstructured) error {
	instance.Object["status"].(map[string]interface{})["lastActiveTime"] = metav1.Now()
	_, err := r.client.Resource(gvr).Namespace(data.DEFAULTNAMESPACE).UpdateStatus(context.TODO(), &unstructured.Unstructured{Object: instance.Object}, metav1.UpdateOptions{})
	return err
}

// check if the CRD.status.ready is true, which mean the computation service is ready to use
func (r Manager) checkServiceReady(instance *unstructured.Unstructured) (bool, error) {
	ready, _, err := unstructured.NestedString(instance.Object, "status", "ready")

	if err != nil {
		return false, err
	}

	if ready != string(v1.ConditionTrue) {
		return false, nil
	}

	return true, nil
}

// DeleteComputation delete the CRD by id
func (r Manager) DeleteComputation(id string) error {
	instanceName := fmt.Sprintf("paceval-computation-%s", id)
	return r.client.Resource(gvr).Namespace(data.DEFAULTNAMESPACE).Delete(context.TODO(), instanceName, metav1.DeleteOptions{})
}
