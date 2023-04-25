package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/google/uuid"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/data"
	http2 "github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/http"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/k8s"
	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
	"net/http"
)

func main() {
	zerolog.SetGlobalLevel(zerolog.DebugLevel)
	manager := k8s.NewK8sManager()
	log.Info().Msg("starting service...")

	// init handlers
	singleProxyHandler := http2.NewSingleHostProxyHandler(manager)
	multiRequestHandler := http2.NewMultiHostRequestHandler(manager)
	multiRequestsExtHandler := http2.NewMultiHostRequestExtHandler(manager)
	demoHandler := http2.NewDemoHandler(manager)

	// assign handlers to endpoints
	http.Handle("/Demo/", demoHandler)
	http.HandleFunc("/CreateComputation/", handleCreatePacevalComputation(manager))
	http.Handle("/GetComputation/", singleProxyHandler)
	http.Handle("/GetComputationResult/", singleProxyHandler)
	http.Handle("/GetComputationResultExt/", singleProxyHandler)
	http.Handle("/GetComputationInformationXML/", singleProxyHandler)
	http.Handle("/GetErrorInformation/", singleProxyHandler)
	http.Handle("/GetMultipleComputationsResults/", multiRequestHandler)
	http.Handle("/GetMultipleComputationsResultsExt/", multiRequestsExtHandler)
	http.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Cache-Control", "no-cache, no-store, no-transform, must-revalidate, private, max-age=0")
		w.WriteHeader(http.StatusNoContent)
	})

	log.Fatal().Msg(http.ListenAndServe(":8080", nil).Error())
}

// handleCreatePacevalComputation create a CRD based on the incoming request
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

		functionId, err := manager.CreateComputation(uuid.New(), params)

		if err != nil {
			w.WriteHeader(http.StatusInternalServerError)
			w.Write([]byte(fmt.Sprintf("{ \"error\": \"%s\" }", err)))
			return
		}

		//resp :=

		//resp := data.HandlePacevalComputationObject{
		//	HandleCreateComputation: functionId,
		//}
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(http2.NewFunctionNotReadyResponse(functionId, manager))
	}
}

// fillCreateComputationQueryParam transforms the query parameters of incoming GET request into a data.ParameterSet
func fillCreateComputationQueryParam(r *http.Request) (*data.ParameterSet, error) {
	values, err := http2.ParseQuery(r.URL.RawQuery)
	if err != nil {
		// handle error: failed to parse query string
		return nil, err
	}
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

// fillCreateComputationBodyParam transforms the request body of incoming POST request into a data.ParameterSet
func fillCreateComputationBodyParam(r *http.Request) (*data.ParameterSet, error) {
	contentType := r.Header.Get("Content-Type")

	switch contentType {

	case "application/x-www-form-urlencoded":
		if err := r.ParseForm(); err != nil {
			return nil, err
		}
		values := r.PostForm
		if !values.Has(data.FUNCTIONSTR) || !values.Has(data.NUMOFVARIABLES) || !values.Has(data.VARAIBLES) || !values.Has(data.INTERVAL) {
			return nil, errors.New("missing parameters")
		}

		return &data.ParameterSet{
			FunctionStr:    values.Get(data.FUNCTIONSTR),
			NumOfVariables: values.Get(data.NUMOFVARIABLES),
			Variables:      values.Get(data.VARAIBLES),
			Interval:       values.Get(data.INTERVAL),
		}, nil

	case "application/json":
		params := data.ParameterSet{}
		err := json.NewDecoder(r.Body).Decode(&params)

		if err != nil {
			return nil, err
		}

		if len(params.Variables) == 0 || len(params.NumOfVariables) == 0 || len(params.FunctionStr) == 0 || len(params.Interval) == 0 {
			return nil, errors.New("missing parameters")
		}
		return &params, nil

	default:
		return nil, errors.New(fmt.Sprintf("Content-type %s not allow", contentType))
	}

}
