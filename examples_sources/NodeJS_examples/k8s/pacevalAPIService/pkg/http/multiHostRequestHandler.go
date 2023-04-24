package http

import (
	"encoding/json"
	"fmt"
	"github.com/hashicorp/go-multierror"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/data"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/k8s"
	"github.com/rs/zerolog/log"
	"io"
	"net/http"
	"strings"
	"sync"
)

// MultiHostRequestHandler is the handler for getMultipleComputationResult
type MultiHostRequestHandler struct {
	manager     k8s.Manager
	baseHandler MultiHostBaseHandler
}

// NewMultiHostRequestHandler return new instance of handler
func NewMultiHostRequestHandler(manager k8s.Manager) MultiHostRequestHandler {
	return MultiHostRequestHandler{manager: manager}
}

// ServeHTTP proxy the requests to multiple computation services with a single value set
func (p MultiHostRequestHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	log.Info().Msg("handle request to get multiple computation result")
	w.Header().Set("Content-Type", "application/json")
	log.Info().Msgf("incoming %s request", r.Method)

	switch r.Method {
	case http.MethodGet, http.MethodPost:
		p.forwardRequestToComputationObjects(w, r)

	default:
		log.Info().Msg("method not allowed")
		w.WriteHeader(http.StatusMethodNotAllowed)
		w.Write([]byte("{ \"error\": \"Method not allowed\" }"))
	}

}

// forwardRequestToComputationObjects send the computation request to multiple computation services and combine their response into a single slice
func (p MultiHostRequestHandler) forwardRequestToComputationObjects(w http.ResponseWriter, r *http.Request) {
	// get all IDs of computation service to call
	ids, values, err := p.baseHandler.getComputationIds(r)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("{ \"error\": \"missing parameters\" }"))
		return
	}

	// do not allow duplicated computation service in the call
	if p.baseHandler.containsDuplicatedId(ids) {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("{ \"error\": \"duplicate handle_pacevalComputation\" }"))
		return
	}

	// get all endpoints to call
	endpoints, _, err := p.baseHandler.getEndpointsWithNumOfVariables(ids, p.manager)

	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		log.Error().Msgf("Error: %s", err)
		w.Write([]byte("{ \"error\": \"handle_pacevalComputation does not exist\" }"))
		return
	}

	resultLock := sync.Mutex{}
	var wg sync.WaitGroup
	wg.Add(len(endpoints))
	errorChan := make(chan error, len(endpoints))
	aggregatedResponse := make([][]byte, len(endpoints))

	for index, endpoint := range endpoints {
		if endpoint == "" {
			w.WriteHeader(http.StatusNotFound)
			log.Error().Msg("Error: endpoint not found: %s")
			w.Write([]byte(fmt.Sprintf("{ \"error\": \"not able to call the %dth computation object\" }", index)))
			return
		}

		// call each endpoint in a go routine
		go func(index int, endpoint string) {
			defer wg.Done()

			// Create a new HTTP client
			client := &http.Client{}

			proxyReq, err := http.NewRequest(http.MethodGet, "http://"+endpoint+"/GetComputationResult/", r.Body)
			//proxyReq, err := http.NewRequest(http.MethodGet, "http://localhost:9000/GetComputationResult/", r.Body)
			param := proxyReq.URL.Query()

			param.Add(data.VALUES, strings.Join(values, ";"))
			proxyReq.URL.RawQuery = param.Encode()

			if err != nil {
				log.Info().Msgf("endpoint: %s , issue creating new request due to : %s", endpoint, err)
				errorChan <- err
				return
			}

			resp, err := client.Do(proxyReq)

			if err != nil {
				log.Info().Msgf("endpoint: %s ,issue sending new request due to : %s", endpoint, err)
				errorChan <- err
				return
			}

			defer resp.Body.Close()

			// Read the response body into a byte slice
			body, err := io.ReadAll(resp.Body)
			if err != nil {
				log.Info().Msgf("endpoint: %s ,issue reading response body : %s", endpoint, err)
				errorChan <- err
				return
			}

			resultLock.Lock()
			defer resultLock.Unlock()

			aggregatedResponse[index] = body

		}(index, endpoint)
	}

	wg.Wait()
	close(errorChan)

	if len(errorChan) == 0 {

		responseJSON, _ := json.Marshal(p.baseHandler.transformResponse(aggregatedResponse))

		w.WriteHeader(http.StatusOK)
		w.Write(responseJSON)
		return
	}

	var combinedError error

	for err := range errorChan {
		combinedError = multierror.Append(combinedError, err)
	}

	w.WriteHeader(http.StatusInternalServerError)
	log.Error().Msgf("error calling functions: %s", combinedError)
	w.Write([]byte("{ \"error\": \"internal error, please contact service admin\" }"))

}
