package http

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/hashicorp/go-multierror"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/data"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/k8s"
	"github.com/rs/zerolog/log"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"sync"
)

// MultiHostBaseHandler is a base handler that has the common functions shared by multiple host request handlers
type MultiHostBaseHandler struct {
	requestPath            string
	manager                k8s.Manager
	extraReqParam          func(url.Values, *data.MultipleComputationRequestParam)
	paramFromRequestValues func(url.Values, *k8s.Manager) (*data.MultipleComputationRequestParam, error)
	transformResponse      func([][]byte) interface{}
}

// getRequestParams returns computation IDs from incoming request
func (p MultiHostBaseHandler) getRequestParams(r *http.Request) (*data.MultipleComputationRequestParam, error) {
	log.Info().Msg("trying to search for computation object id")
	switch r.Method {
	case http.MethodGet:
		values, err := ParseQuery(r.URL.RawQuery)

		if err != nil {
			// handle error: failed to parse query string
			return nil, err
		}

		reqParam, err := p.paramFromRequestValues(values, &p.manager)

		if err != nil {
			log.Debug().Msgf("req error: %s", err)
			return reqParam, err
		}

		log.Info().Msgf("computation object id %s", values.Get(data.HANDLEPACEVALCOMPUTATION))
		return reqParam, nil
	case http.MethodPost:
		contentType := r.Header.Get("Content-Type")

		switch contentType {
		case "application/x-www-form-urlencoded":
			if err := r.ParseForm(); err != nil {
				return nil, err
			}
			values := r.PostForm
			UrlDecode(values)

			reqParam, err := p.paramFromRequestValues(values, &p.manager)

			if err != nil {
				log.Debug().Msgf("req error: %s", err)
				return reqParam, err
			}

			r.Body = io.NopCloser(strings.NewReader(values.Encode()))
			log.Info().Msgf("computation object id %s", values.Get(data.HANDLEPACEVALCOMPUTATION))
			return reqParam, nil

		case "application/json":
			requestObject := make(map[string]string)
			body, err := io.ReadAll(r.Body)

			if err != nil {
				return nil, err
			}

			r.Body = io.NopCloser(bytes.NewBuffer(body))

			if err = json.Unmarshal(body, &requestObject); err != nil {
				return nil, err
			}

			values := make(url.Values)
			for k, v := range requestObject {
				values.Set(k, v)
			}

			reqParam, err := p.paramFromRequestValues(values, &p.manager)

			if err != nil {
				log.Debug().Msgf("req error: %s", err)
				return reqParam, err
			}

			return reqParam, nil

		default:
			return nil, errors.New(fmt.Sprintf("Content-type %s not allow", contentType))
		}
	default:
		return nil, errors.New("method not allowed")
	}

}

// getEndpointsWithNumOfVariables return endpoints and number of variables from multiple CRDs
// the request will be running in parallel, the output slices of string is the slice of endpoints
// and output slices of integers is the slice of numOfVariables
// the order of data in the slice is the order of ids from the input
func getEndpointsWithNumOfVariables(ids []string, manager k8s.Manager) ([]string, []int, error) {

	endpoints := make([]string, len(ids))
	numOfValues := make([]int, len(ids))
	errorChan := make(chan error, len(ids))

	var wg sync.WaitGroup
	wg.Add(len(ids))
	resultLock := sync.Mutex{}

	for index, id := range ids {
		go func(index int, id string) {
			defer wg.Done()
			endpoint, err := manager.GetEndpoint(id)
			if err != nil && errors.Is(err, data.ServiceNotReadyError{}) {
				endpoint = data.NOTREADY_ENDPOINT
			} else if err != nil {
				log.Info().Msgf("id: %s, issue receiving endpoint : %s", id, err)
				errorChan <- err
				return
			}
			numOfVariablesStr, err := manager.GetNumOfVariables(id)

			if err != nil {
				log.Info().Msgf("id: %s, issue receiving num of variable : %s", id, err)
				errorChan <- err
				return
			}

			numOfVariables, err := strconv.Atoi(numOfVariablesStr)

			if err != nil {
				log.Info().Msgf("id: %s, issue receiving num of variable : %s", id, err)
				errorChan <- err
				return
			}

			resultLock.Lock()
			defer resultLock.Unlock()

			endpoints[index] = endpoint
			numOfValues[index] = numOfVariables

		}(index, id)
	}

	wg.Wait()
	close(errorChan)

	if len(errorChan) == 0 {
		return endpoints, numOfValues, nil
	}

	var combinedError error

	for err := range errorChan {
		combinedError = multierror.Append(combinedError, err)
	}

	return nil, nil, combinedError

}

// forwardRequestToComputationObjects send the computation request to multiple computation services and combine their response into a single slice
func (p MultiHostBaseHandler) forwardRequestToComputationObjects(w http.ResponseWriter, r *http.Request) {
	// get all parameters from request
	//ids, values, numCalculations, err := p.getRequestParams(r, &p.manager, validateRequest)
	reqParam, err := p.getRequestParams(r)
	if err != nil && errors.Is(err, data.InvalidRequestError{}) {
		buildResponseForInvalidReq(reqParam.ComputationIds, w)
		return
	} else if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte(fmt.Sprintf("{ \"error\": \"%s\" }", err.Error())))
		return
	}

	// do not allow duplicated computation service in the call
	if containsDuplicatedId(reqParam.ComputationIds) {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("{ \"error\": \"duplicated handle_pacevalComputation\" }"))
		return
	}

	// get all endpoints to call
	endpoints, numOfVariables, err := getEndpointsWithNumOfVariables(reqParam.ComputationIds, p.manager)

	if !validateFunctionsFromRequest(numOfVariables) {
		buildResponseForInvalidReq(reqParam.ComputationIds, w)
		return
	}

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

		// call each endpoint in a go routine
		go func(index int, endpoint string) {
			defer wg.Done()

			if endpoint == data.NOTREADY_ENDPOINT || endpoint == "" {
				resp, err := json.Marshal(NewFunctionNotReadyResponse(reqParam.ComputationIds[index], p.manager))

				if err != nil {
					errorChan <- err
				}
				aggregatedResponse[index] = resp
				return
			}

			// Create a new HTTP client
			client := &http.Client{}

			proxyReq, err := http.NewRequest(http.MethodGet, "http://"+endpoint+"/"+p.requestPath+"/", r.Body)
			//proxyReq, err := http.NewRequest(http.MethodGet, "http://localhost:9000/"+p.requestPath+"/", r.Body)
			param := proxyReq.URL.Query()

			param.Add(data.VALUES, strings.Join(reqParam.Values, ";"))
			p.extraReqParam(param, reqParam)
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

		responseJSON, _ := json.Marshal(p.transformResponse(aggregatedResponse))

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

// containsDuplicatedId check for duplicated id in slices of ID
func containsDuplicatedId(ids []string) bool {
	m := make(map[string]struct{})

	for _, id := range ids {
		m[id] = struct{}{}
	}

	if len(m) != len(ids) {
		return true
	}

	return false
}

// createRespForInvalidReq create response object of data.MultipleComputationResult when incoming request for GetMultipleComputationResult
// is invalid
func createRespForInvalidReq(ids []string, errorTypeNumber int) data.MultipleComputationResult {
	errNumberArray := make([]int, len(ids))

	for i := 0; i < len(errNumberArray); i++ {
		errNumberArray[i] = errorTypeNumber
	}

	return data.MultipleComputationResult{
		NumOfComputations: len(ids),
		FunctionIds:       ids,
		HasError:          true,
		Results:           make([]string, len(ids)),
		IntervalMins:      make([]string, len(ids)),
		IntervalMaxs:      make([]string, len(ids)),
		ErrorTypeNums:     errNumberArray,
		TimeCalculate:     "0s",
		Version:           data.PACEVAL_VERSION,
	}

}

// buildResponseForInvalidReq write an error response when the request parameter is invalid
func buildResponseForInvalidReq(ids []string, w http.ResponseWriter) {
	w.WriteHeader(http.StatusBadRequest)
	resp := createRespForInvalidReq(ids, data.PACEVAL_ERR_COMPUTATION_WRONGLY_USED_PARAMETERS)
	json.NewEncoder(w).Encode(resp)
}

// validateFunctionsFromRequest validate if all functions from the request is having same number of variables
func validateFunctionsFromRequest(numOfVariables []int) bool {

	if len(numOfVariables) < 2 {
		return true
	}

	for i := 1; i < len(numOfVariables); i++ {
		if numOfVariables[i] != numOfVariables[i-1] {
			return false
		}
	}
	return true
}
