package controllers

import (
	"context"
	"fmt"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/operator/api/v1alpha1"
	"github.com/rs/zerolog/log"
	v1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/types"
	"sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
)

func (r *PacevalComputationObjectReconciler) ensureConfigMap(request reconcile.Request,
	instance *v1alpha1.PacevalComputationObject,
	cm *v1.ConfigMap,
) (*reconcile.Result, error) {

	found := &v1.ConfigMap{}

	err := r.Get(context.TODO(), types.NamespacedName{
		Name:      cm.Name,
		Namespace: instance.Namespace,
	}, found)

	if err != nil && errors.IsNotFound(err) {
		log.Info().Msgf("create configMap %s", cm.Name)

		err := r.Create(context.TODO(), cm)

		if err != nil {
			// ConfigMap creation failed
			log.Error().Msgf("configMap %s failed due to: %s", cm.Name, err)
			return &reconcile.Result{}, err
		} else {
			// configMap creation was successful
			return nil, nil
		}

	} else if err != nil {
		// Error that isn't due to the service not existing
		log.Error().Msg(err.Error())
		return &reconcile.Result{}, err
	}

	return nil, nil

}

func (r *PacevalComputationObjectReconciler) backendConfigMap(v *v1alpha1.PacevalComputationObject) *v1.ConfigMap {

	cm := &v1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{
			Name:      fmt.Sprintf("paceval-computation-%s", v.Spec.FunctionId),
			Namespace: v.Namespace,
		},
		Data: map[string]string{
			"functionStr": v.Spec.FunctionStr,
		},
	}

	controllerutil.SetControllerReference(v, cm, r.Scheme)
	return cm
}
