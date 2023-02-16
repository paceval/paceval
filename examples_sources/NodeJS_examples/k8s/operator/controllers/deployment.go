package controllers

import (
	"context"
	"fmt"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/operator/api/v1alpha1"
	"github.com/rs/zerolog/log"
	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
)

func labels(v *v1alpha1.PacevalComputationObject, tier string) map[string]string {
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
			log.Error().Msgf("deployment %s failed due to: %s", dep.Name, err.Error())
			return &reconcile.Result{}, err
		}
	} else if err != nil {
		// Error that isn't due to the deployment not existing
		log.Error().Msg(err.Error())
		return &reconcile.Result{}, err
	}

	return nil, nil
}

func (r *PacevalComputationObjectReconciler) backendDeployment(v *v1alpha1.PacevalComputationObject) *appsv1.Deployment {

	labels := labels(v, "backend")
	size := int32(1)
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
						}},
					}},
			},
		},
	}

	controllerutil.SetControllerReference(v, dep, r.Scheme)
	return dep
}
