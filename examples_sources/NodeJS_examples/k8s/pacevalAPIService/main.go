package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/data"
	http2 "github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/http"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/k8s"
	"github.com/rs/zerolog/log"
	"net/http"
)

func main() {

	manager := k8s.NewK8sManager()
	log.Info().Msg("starting service...")

	singleProxyHandler := http2.NewSingleHostProxyHandler(manager)
	multiRequestsHander := http2.NewMultiHostProxyHandler(manager)

	http.HandleFunc("/CreateComputation/", handleCreatePacevalComputation(manager))
	http.Handle("/GetComputation/", singleProxyHandler)
	http.Handle("/GetComputationResult/", singleProxyHandler)
	http.Handle("/GetComputationResultExt/", singleProxyHandler)
	http.Handle("/GetComputationInformationXML/", singleProxyHandler)
	http.Handle("/GetErrorInformation/", singleProxyHandler)
	http.Handle("/GetMultipleComputationsResults/", multiRequestsHander)
	http.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "no-cache, no-store, no-transform, must-revalidate, private, max-age=0")
		w.WriteHeader(http.StatusNoContent)
	})

	log.Fatal().Msg(http.ListenAndServe(":8080", nil).Error())
}

func handleCreatePacevalComputation(manager k8s.Manager) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		log.Info().Msg("handle request to create computation")
		w.Header().Set("Content-Type", "application/json")
		var params *data.ParameterSet
		var err error

		switch r.Method {
		case http.MethodGet:
			params, err = fillCreateComputationQueryParam(r)
			if err != nil {
				w.WriteHeader(http.StatusBadRequest)
				w.Write([]byte(fmt.Sprintf("{ \"error\": \"%s\" }", err)))
				return
			}
			break
		case http.MethodPost:
			params, err = fillCreateComputationBodyParam(r)
			if err != nil {
				w.WriteHeader(http.StatusBadRequest)
				w.Write([]byte(fmt.Sprintf("{ \"error\": \"%s\" }", err)))
				return
			}
			break

		default:
			log.Info().Msg("method not allowed")
			w.WriteHeader(http.StatusMethodNotAllowed)
			w.Write([]byte("{ \"error\": \"Method not allowed\" }"))
			return
		}

		functionId, err := manager.CreateComputation(params)

		if err != nil {
			w.WriteHeader(http.StatusMethodNotAllowed)
			w.Write([]byte(fmt.Sprintf("{ \"error\": \"%s\" }", err)))
			return
		}

		resp := data.HandlePacevalComputationObject{
			HandleCreateComputation: functionId,
		}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(resp)
	}
}

func fillCreateComputationQueryParam(r *http.Request) (*data.ParameterSet, error) {
	values := r.URL.Query()
	if !values.Has(data.FUNCTIONSTR) || !values.Has(data.NUMOFVARIABLES) || !values.Has(data.VARAIBLES) || !values.Has(data.INTERVAL) {
		return nil, errors.New("missing parameters")
	}

	return &data.ParameterSet{
		FunctionStr:    values.Get(data.FUNCTIONSTR),
		NumOfVariables: values.Get(data.NUMOFVARIABLES),
		Variables:      values.Get(data.VARAIBLES),
		Interval:       values.Get(data.INTERVAL),
	}, nil
}

func fillCreateComputationBodyParam(r *http.Request) (*data.ParameterSet, error) {
	params := data.ParameterSet{}
	err := json.NewDecoder(r.Body).Decode(&params)

	if err != nil {
		return nil, err
	}

	if len(params.Variables) == 0 || len(params.NumOfVariables) == 0 || len(params.FunctionStr) == 0 || len(params.Interval) == 0 {
		return nil, errors.New("missing parameters")
	}
	return &params, nil
}
