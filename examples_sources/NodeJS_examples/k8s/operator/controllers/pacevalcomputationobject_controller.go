/*
Copyright 2023.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package controllers

import (
	"context"
	pacevalv1alpha1 "github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/operator/api/v1alpha1"
	"github.com/rs/zerolog/log"
	"k8s.io/apimachinery/pkg/api/errors"
	v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"os"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/reconcile"
	"strings"
)

const finalizerName = "paceval-controller.finalizer.paceval.com"

// PacevalComputationObjectReconciler reconciles a PacevalComputationObject object
type PacevalComputationObjectReconciler struct {
	client.Client
	Scheme *runtime.Scheme
}

func init() {
	_, present := os.LookupEnv("REDIS_ADDRESS")
	if !present {
		log.Fatal().Msg("fatal error: env var REDIS_ADDRESS not set")
		panic("fail to get the redis client")
	}
}

//+kubebuilder:rbac:groups=paceval.com,resources=pacevalcomputationobjects,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=paceval.com,resources=pacevalcomputationobjects/status,verbs=get;update;patch
//+kubebuilder:rbac:groups=paceval.com,resources=pacevalcomputationobjects/finalizers,verbs=update
//+kubebuilder:rbac:groups=apps,resources=deployments,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=core,resources=services,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=core,resources=endpoints,verbs=get;list;watch;create;update;patch;delete
//+kubebuilder:rbac:groups=autoscaling,resources=horizontalpodautoscalers,verbs=get;list;watch;create;update;patch;delete

// Reconcile is part of the main kubernetes reconciliation loop which aims to
// move the current state of the cluster closer to the desired state.
// TODO(user): Modify the Reconcile function to compare the state specified by
// the PacevalComputationObject object against the actual cluster state, and then
// perform operations to make the cluster state reflect the state specified by
// the user.
//
// For more details, check Reconcile and its Result here:
// - https://pkg.go.dev/sigs.k8s.io/controller-runtime@v0.13.0/pkg/reconcile
func (r *PacevalComputationObjectReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {

	log.Info().Msg("Start reconciling...")

	address := os.Getenv("REDIS_ADDRESS")
	redis := NewRedis(address)

	defer redis.CloseConnection()
	instance := &pacevalv1alpha1.PacevalComputationObject{}

	err := r.Get(context.TODO(), req.NamespacedName, instance)
	if err != nil {
		if errors.IsNotFound(err) {
			// Request object not found, could have been deleted after reconcile request.
			// Owned objects are automatically garbage collected. For additional cleanup logic use finalizers.
			// Return and don't requeue
			log.Info().Msg("Request Object not found, end reconciling...")
			return reconcile.Result{}, nil
		}
		// Error reading the object - requeue the request.
		return reconcile.Result{}, err
	}

	//clean up cache in redis upon deletion of CRD
	if !instance.GetDeletionTimestamp().IsZero() {
		redisKey := instance.Spec.FunctionStr

		if strings.HasPrefix(redisKey, "redis") {
			log.Info().Msgf("check redis value with key %s", redisKey)
			if redis.Exist(redisKey) {
				log.Info().Msgf("delete redis value with key %s", redisKey)
				err := redis.Delete(redisKey)

				if err != nil {
					log.Error().Msgf("unable to delete redis value: %s , requeue...", err)
					return reconcile.Result{}, err
				}
			}
		}

		log.Info().Msgf("remove finalizer from CRD %s", instance.Name)
		removeFinalizer(instance)

		err = r.Client.Update(context.TODO(), instance)

		if err != nil {
			log.Error().Msgf("unable to remove finalizer : %s , requeue...", err)
			return reconcile.Result{}, err
		}

		return reconcile.Result{}, nil

	}

	var result *reconcile.Result
	dep, err := r.backendDeployment(instance, redis)

	if err != nil {
		log.Error().Msgf("Deployment failed, error: %s, requeue...", err)
		return reconcile.Result{}, err
	}

	result, err = r.ensureDeployment(req, instance, dep)
	if err != nil {
		log.Error().Msgf("Deployment failed, error: %s", err)
		return ctrl.Result{}, err
	} else {
		return *result, nil
	}

	result, err = r.ensureService(req, instance, r.backendService(instance))
	if err != nil {
		log.Error().Msgf("service failed, error: %s", err)
		return ctrl.Result{}, err
	} else {
		return *result, nil
	}

	result, err = r.ensureHPA(req, instance, r.backendHpa(instance))
	if err != nil {
		log.Error().Msgf("service failed, error: %s", err)
		return ctrl.Result{}, err
	} else {
		return *result, nil
	}

	// set the instance status to true
	instance.Status.Ready = v1.ConditionTrue
	if instance.Status.LastActiveTime.IsZero() {
		instance.Status.LastActiveTime = v1.Now()
	}

	r.Status().Update(context.TODO(), instance)

	return ctrl.Result{}, nil
}

func removeFinalizer(instance *pacevalv1alpha1.PacevalComputationObject) {
	var finalizers []string

	for _, finalizer := range instance.GetFinalizers() {
		if finalizer != finalizerName {
			finalizers = append(finalizers, finalizer)
		}
	}

	instance.SetFinalizers(finalizers)
}

// SetupWithManager sets up the controller with the Manager.
func (r *PacevalComputationObjectReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&pacevalv1alpha1.PacevalComputationObject{}).
		Complete(r)
}
