package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/data"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/k8s"
	"github.com/rs/zerolog/log"
	"io"
	"net/http"
)

func main() {

	manager := k8s.NewK8sManager()
	log.Info().Msg("starting service...")

	http.HandleFunc("/CreateComputation/", handleCreatePacevalComputation(manager))
	http.HandleFunc("/GetComputation/", handleSingleComputationProcess(manager))
	http.HandleFunc("/GetComputationResult/", handleSingleComputationProcess(manager))
	http.HandleFunc("/GetComputationResultExt/", handleSingleComputationProcess(manager))
	http.HandleFunc("/GetComputationInformationXML/", handleSingleComputationProcess(manager))
	http.HandleFunc("/GetErrorInformation/", handleSingleComputationProcess(manager))
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

func handleSingleComputationProcess(manager k8s.Manager) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		log.Info().Msg("handle request to get computation result")
		w.Header().Set("Content-Type", "application/json")

		switch r.Method {
		case http.MethodGet:
			forwardRequestToComputationObject(w, r, manager)
			break

		default:
			log.Info().Msg("method not allowed")
			w.WriteHeader(http.StatusMethodNotAllowed)
			w.Write([]byte("{ \"error\": \"Method not allowed\" }"))
		}
	}
}

func forwardRequestToComputationObject(w http.ResponseWriter, r *http.Request, manager k8s.Manager) {
	id, err := getComputationId(r)

	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("{ \"error\": \"missing parameters\" }"))
		return
	}

	log.Info().Msgf("forward request to conmputation object id: %s", id)

	endpoint, err := manager.GetEndpoint(id)

	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte(fmt.Sprintf("{ \"error\": \"%s\" }", err)))
		return
	}

	log.Info().Msgf("conmputation object endpoint: %s", endpoint)

	//https://stackoverflow.com/questions/34724160/go-http-send-incoming-http-request-to-an-other-server-using-client-do
	url := r.URL
	url.Host = endpoint
	url.Scheme = "http"

	proxyReq, err := http.NewRequest(r.Method, url.String(), r.Body)

	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(fmt.Sprintf("{ \"error\": \"%s\" }", err)))
		return
	}

	proxyReq.Header.Set("Host", r.Host)
	proxyReq.Header.Set("X-Forwarded-For", r.RemoteAddr)

	// add all original request header to proxy request
	for header, values := range r.Header {
		for _, value := range values {
			proxyReq.Header.Add(header, value)
		}
	}

	client := &http.Client{}
	proxyRes, err := client.Do(proxyReq)
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(fmt.Sprintf("{ \"error\": \"%s\" }", err)))
		return
	}

	respBody, err := io.ReadAll(proxyRes.Body)
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(fmt.Sprintf("{ \"error\": \"%s\" }", err)))
		return
	}

	log.Info().Msg("received response from target")
	w.WriteHeader(proxyRes.StatusCode)
	w.Write(respBody)
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

func getComputationId(r *http.Request) (string, error) {
	log.Info().Msg("trying to search for computation object id")
	switch r.Method {
	case http.MethodGet:
		values := r.URL.Query()
		if !values.Has(data.HANDLEPACEVALCOMPUTATION) {
			return "", errors.New("missing parameters")
		}
		log.Info().Msgf("computation object id %s", values.Get(data.HANDLEPACEVALCOMPUTATION))
		return values.Get(data.HANDLEPACEVALCOMPUTATION), nil
	case http.MethodPost:
		requestObj := data.HandlePacevalComputationObject{}
		err := json.NewDecoder(r.Body).Decode(requestObj)
		if err != nil {
			return "", err
		}

		if len(requestObj.HandleCreateComputation) == 0 {
			return "", errors.New("missing parameters")
		}
		log.Info().Msgf("computation object id %s", requestObj.HandleCreateComputation)
		return requestObj.HandleCreateComputation, nil
	default:
		return "", errors.New("method not allowed")
	}

}
