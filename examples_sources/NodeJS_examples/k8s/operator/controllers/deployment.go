package controllers

import (
	"context"
	"fmt"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/operator/api/v1alpha1"
	"github.com/rs/zerolog/log"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/equality"
	"k8s.io/apimachinery/pkg/api/errors"
	"k8s.io/apimachinery/pkg/api/resource"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/apimachinery/pkg/util/intstr"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
	"strings"
	"time"
)

type ResourceQuantity struct {
	CPURequest     resource.Quantity
	CPULimit       resource.Quantity
	MemoryRequest  resource.Quantity
	MemoryLimit    resource.Quantity
	StorageRequest resource.Quantity
	StorageLimit   resource.Quantity
}

func labels(v *v1alpha1.PacevalComputationObject) map[string]string {
	// Fetches and sets labels

	return map[string]string{
		"app":         "computation",
		"name":        v.Name,
		"function-id": v.Spec.FunctionId,
	}
}

// ensureDeployment ensures Deployment resource presence in given namespace.
func (r *PacevalComputationObjectReconciler) ensureDeployment(request reconcile.Request,
	instance *v1alpha1.PacevalComputationObject,
	dep *appsv1.Deployment,
) (*reconcile.Result, error) {

	// See if deployment already exists and create if it doesn't
	found := &appsv1.Deployment{}
	err := r.Get(context.TODO(), types.NamespacedName{
		Name:      dep.Name,
		Namespace: instance.Namespace,
	}, found)
	if err != nil && errors.IsNotFound(err) {

		// Create the deployment
		log.Info().Msgf("create deployment %s", dep.Name)
		err = r.Create(context.TODO(), dep)

		if err != nil {
			// Deployment failed
			log.Error().Msgf("deployment %s creation failed due to: %s", dep.Name, err)
			return &reconcile.Result{}, err
		}

		log.Info().Msgf("wait for deployment %s ready, requeue...", dep.Name)
		return &reconcile.Result{
			RequeueAfter: 500 * time.Millisecond,
		}, nil

	} else if err != nil {
		// Error that isn't due to the deployment not existing
		log.Error().Msgf("deployment %s failed due to: %s", dep.Name, err)
		log.Error().Msg(err.Error())
		return &reconcile.Result{}, err
	}

	if !equality.Semantic.DeepEqual(dep.Spec, found.Spec) {
		if err = r.Update(context.TODO(), dep); err != nil {
			log.Error().Msgf("deployment %s updating failed due to: %s", dep.Name, err)
			return &reconcile.Result{}, err
		}
	}

	// deployment is available, we need to check if it is ready
	if found.Status.ReadyReplicas != found.Status.AvailableReplicas || found.Status.AvailableReplicas < 1 {
		log.Info().Msgf("wait for deployment %s ready, requeue...", dep.Name)
		return &reconcile.Result{
			RequeueAfter: 500 * time.Millisecond,
		}, nil
	}

	r.Status().Update(context.TODO(), instance)

	return nil, nil
}

func (r *PacevalComputationObjectReconciler) backendDeployment(v *v1alpha1.PacevalComputationObject, redis Redis) (*appsv1.Deployment, error) {

	labels := labels(v)
	size := int32(1)

	var actualFunction string
	if strings.HasPrefix(v.Spec.FunctionStr, "redis") {
		key := v.Spec.FunctionStr
		val, err := redis.Get(key)

		if err != nil {
			log.Error().Msgf("error get value from redis : %s", err)
			return nil, err
		}

		actualFunction = val

	} else {
		actualFunction = v.Spec.FunctionStr
	}

	resourceMap := getResourceQuantityFromFunctionStr(actualFunction)
	dep := &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      fmt.Sprintf("paceval-computation-%s", v.Spec.FunctionId),
			Namespace: v.Namespace,
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: &size,
			Selector: &metav1.LabelSelector{
				MatchLabels: labels,
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: labels,
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{{
						Image:           "paceval/paceval-computation",
						ImagePullPolicy: corev1.PullAlways,
						Name:            "paceval-computation-object",
						Ports: []corev1.ContainerPort{{
							ContainerPort: 8080,
							Name:          "http",
							Protocol:      "TCP",
						}},
						Resources: corev1.ResourceRequirements{
							Limits: corev1.ResourceList{
								corev1.ResourceCPU:              resourceMap.CPULimit,
								corev1.ResourceMemory:           resourceMap.MemoryLimit,
								corev1.ResourceEphemeralStorage: resourceMap.StorageLimit,
							},
							Requests: corev1.ResourceList{
								corev1.ResourceCPU:              resourceMap.CPURequest,
								corev1.ResourceMemory:           resourceMap.MemoryRequest,
								corev1.ResourceEphemeralStorage: resourceMap.StorageRequest,
							},
						},
						Env: []corev1.EnvVar{
							{
								Name:  "FUNCTION_STR",
								Value: v.Spec.FunctionStr,
							},
							{
								Name:  "VARS",
								Value: v.Spec.Vars,
							},
							{
								Name:  "NUM_VARS",
								Value: v.Spec.NumOfVars,
							},
							{
								Name:  "INTERVAL",
								Value: v.Spec.Interval,
							},
							{
								Name:  "FUNCTION_ID",
								Value: v.Spec.FunctionId,
							},
							{
								Name:  "REDIS_ADDRESS",
								Value: "redis-headless.redis.svc.cluster.local:6379",
							},
						},
						LivenessProbe: &corev1.Probe{
							ProbeHandler: corev1.ProbeHandler{
								HTTPGet: &corev1.HTTPGetAction{
									Path: "/health",
									Port: intstr.FromInt(8080),
								},
							},
							InitialDelaySeconds: 5,
							PeriodSeconds:       5,
							FailureThreshold:    2,
						},
						ReadinessProbe: &corev1.Probe{
							ProbeHandler: corev1.ProbeHandler{
								HTTPGet: &corev1.HTTPGetAction{
									Path: "/ready",
									Port: intstr.FromInt(8080),
								},
							},
							InitialDelaySeconds: 5,
							PeriodSeconds:       5,
							FailureThreshold:    2,
						},
					},
					}},
			},
		},
	}

	controllerutil.SetControllerReference(v, dep, r.Scheme)
	return dep, nil
}

func getResourceQuantityFromFunctionStr(functionStr string) ResourceQuantity {
	l := len(functionStr)

	if l < 10000 {
		return ResourceQuantity{
			CPURequest:     resource.MustParse("50m"),
			CPULimit:       resource.MustParse("75m"),
			MemoryRequest:  resource.MustParse("10Mi"),
			MemoryLimit:    resource.MustParse("50Mi"),
			StorageRequest: resource.MustParse("100Mi"),
			StorageLimit:   resource.MustParse("200Mi"),
		}

	} else if l < 100000 {
		return ResourceQuantity{
			CPURequest:     resource.MustParse("250m"),
			CPULimit:       resource.MustParse("375m"),
			MemoryRequest:  resource.MustParse("10Mi"),
			MemoryLimit:    resource.MustParse("50Mi"),
			StorageRequest: resource.MustParse("100Mi"),
			StorageLimit:   resource.MustParse("200Mi"),
		}

	} else if l < 1000000 {
		return ResourceQuantity{
			CPURequest:     resource.MustParse("500m"),
			CPULimit:       resource.MustParse("750m"),
			MemoryRequest:  resource.MustParse("0.5Gi"),
			MemoryLimit:    resource.MustParse("1Gi"),
			StorageRequest: resource.MustParse("200Mi"),
			StorageLimit:   resource.MustParse("250Mi"),
		}
	} else if l < 10000000 {
		return ResourceQuantity{
			CPURequest:     resource.MustParse("1"),
			CPULimit:       resource.MustParse("1.5"),
			MemoryRequest:  resource.MustParse("1Gi"),
			MemoryLimit:    resource.MustParse("2Gi"),
			StorageRequest: resource.MustParse("200Mi"),
			StorageLimit:   resource.MustParse("250Mi"),
		}
	} else {
		return ResourceQuantity{
			CPURequest:     resource.MustParse("2"),
			CPULimit:       resource.MustParse("2"),
			MemoryRequest:  resource.MustParse("10Gi"),
			MemoryLimit:    resource.MustParse("10Gi"),
			StorageRequest: resource.MustParse("200Mi"),
			StorageLimit:   resource.MustParse("250Mi"),
		}
	}
}
