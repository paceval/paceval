package controllers

import (
	"context"
	"fmt"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/operator/api/v1alpha1"
	"github.com/rs/zerolog/log"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/equality"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"k8s.io/apimachinery/pkg/util/intstr"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
	"time"
)

// ensureService ensures Service is Running in a namespace.
func (r *PacevalComputationObjectReconciler) ensureService(request reconcile.Request,
	instance *v1alpha1.PacevalComputationObject,
	service *corev1.Service,
) (*reconcile.Result, error) {

	// See if service already exists and create if it doesn't
	found := &corev1.Service{}
	err := r.Get(context.TODO(), types.NamespacedName{
		Name:      service.Name,
		Namespace: instance.Namespace,
	}, found)
	if err != nil && errors.IsNotFound(err) {

		log.Info().Msgf("create service %s", service.Name)

		// Create the service
		err = r.Create(context.TODO(), service)
		instance.Status.Endpoint = fmt.Sprintf("%s.%s.svc.cluster.local", service.Name, service.Namespace)
		log.Info().Msgf("wait for service %s ready, requeue...", found.Name)

		if err != nil {
			// Service creation failed
			log.Error().Msgf("service %s creation failed due to: %s", service.Name, err)
			return &reconcile.Result{}, err
		}

		return &reconcile.Result{
			RequeueAfter: 100 * time.Millisecond,
		}, nil

	} else if err != nil {
		// Error that isn't due to the service not existing
		log.Error().Msg(err.Error())
		return &reconcile.Result{}, err
	}

	if equality.Semantic.DeepEqual(service.Spec, found.Spec) {
		log.Info().Msgf("updating service %s", service.Name)
		if err = r.Update(context.TODO(), service); err != nil {
			log.Error().Msgf("service %s updating failed due to: %s", service.Name, err)
			return nil, err
		}
	}

	endpoint := &corev1.Endpoints{}
	err = r.Get(context.TODO(), types.NamespacedName{
		Name:      found.Name,
		Namespace: found.Namespace,
	}, endpoint)

	if err != nil && errors.IsNotFound(err) {
		log.Info().Msgf("endpoint %s not found, requeue...", found.Name)
		return &reconcile.Result{
			RequeueAfter: 100 * time.Millisecond,
		}, nil
	} else if err != nil {
		log.Error().Msg(err.Error())
		return &reconcile.Result{}, err
	}

	if len(endpoint.Subsets) == 0 || len(endpoint.Subsets[0].Addresses) == 0 {
		log.Info().Msgf("wait for service %s ready, requeue...", found.Name)
		return &reconcile.Result{
			RequeueAfter: 100 * time.Millisecond,
		}, nil
	}

	instance.Status.Endpoint = fmt.Sprintf("%s.%s.svc.cluster.local", service.Name, service.Namespace)

	r.Status().Update(context.TODO(), instance)

	return nil, nil
}

// backendService is a code for creating a Service
func (r *PacevalComputationObjectReconciler) backendService(v *v1alpha1.PacevalComputationObject) *corev1.Service {
	labels := labels(v)

	service := &corev1.Service{
		ObjectMeta: metav1.ObjectMeta{
			Name:      fmt.Sprintf("paceval-computation-%s", v.Spec.FunctionId),
			Namespace: v.Namespace,
		},
		Spec: corev1.ServiceSpec{
			Selector: labels,
			Ports: []corev1.ServicePort{{
				Protocol:   corev1.ProtocolTCP,
				Port:       80,
				TargetPort: intstr.FromInt(8080),
			}},
			Type: corev1.ServiceTypeNodePort,
		},
	}

	controllerutil.SetControllerReference(v, service, r.Scheme)
	return service
}
