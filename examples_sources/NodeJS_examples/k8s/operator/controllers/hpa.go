package controllers

import (
	"context"
	"fmt"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/operator/api/v1alpha1"
	"github.com/rs/zerolog/log"
	v2 "k8s.io/api/autoscaling/v2"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/utils/pointer"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
)

// ensureHPA ensures HPA is present
func (r *PacevalComputationObjectReconciler) ensureHPA(request reconcile.Request,
	instance *v1alpha1.PacevalComputationObject,
	hpa *v2.HorizontalPodAutoscaler,
) (*reconcile.Result, error) {

	// See if hpa already exists and create if it doesn't
	found := &v2.HorizontalPodAutoscaler{}
	err := r.Get(context.TODO(), types.NamespacedName{
		Name:      hpa.Name,
		Namespace: instance.Namespace,
	}, found)
	if err != nil && errors.IsNotFound(err) {

		log.Info().Msgf("create HPA %s", hpa.Name)

		// Create the HPA
		err = r.Create(context.TODO(), hpa)

		if err != nil {
			// HPA creation failed
			return &reconcile.Result{}, err
		}

	} else if err != nil {
		// Error that isn't due to the hpa not existing
		log.Error().Msg(err.Error())
		return nil, err
	}

	return nil, nil
}

// backendHpa is a code for creating a HPA based on CRD
func (r *PacevalComputationObjectReconciler) backendHpa(v *v1alpha1.PacevalComputationObject) *v2.HorizontalPodAutoscaler {

	// return a new HPA manifest
	hpa := &v2.HorizontalPodAutoscaler{
		ObjectMeta: metav1.ObjectMeta{
			Name:      fmt.Sprintf("paceval-computation-%s", v.Spec.FunctionId),
			Namespace: v.Namespace,
		},
		Spec: v2.HorizontalPodAutoscalerSpec{
			ScaleTargetRef: v2.CrossVersionObjectReference{
				APIVersion: "apps/v1",
				Kind:       "Deployment",
				Name:       fmt.Sprintf("paceval-computation-%s", v.Spec.FunctionId),
			},
			MinReplicas: pointer.Int32(1),
			MaxReplicas: 4,
			Metrics: []v2.MetricSpec{
				{
					Type: v2.ResourceMetricSourceType,
					Resource: &v2.ResourceMetricSource{
						Name: corev1.ResourceCPU,
						Target: v2.MetricTarget{
							Type:               v2.UtilizationMetricType,
							AverageUtilization: pointer.Int32(90),
						},
					},
				},
				{
					Type: v2.ResourceMetricSourceType,
					Resource: &v2.ResourceMetricSource{
						Name: corev1.ResourceMemory,
						Target: v2.MetricTarget{
							Type:               v2.UtilizationMetricType,
							AverageUtilization: pointer.Int32(90),
						},
					},
				},
			},
		},
	}

	controllerutil.SetControllerReference(v, hpa, r.Scheme)
	return hpa
}
