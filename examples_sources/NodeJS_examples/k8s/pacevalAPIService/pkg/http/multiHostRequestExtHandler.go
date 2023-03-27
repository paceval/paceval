package http

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/hashicorp/go-multierror"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/data"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/k8s"
	"github.com/rs/zerolog/log"
	math "github.com/spatialcurrent/go-math/pkg/math"
	"io"
	"net/http"
	"strings"
	"sync"
)

type MultiHostRequestExtHandler struct {
	manager     k8s.Manager
	baseHandler MultiHostBaseHandler
}

func NewMultiHostRequestExtHandler(manager k8s.Manager) MultiHostRequestExtHandler {
	return MultiHostRequestExtHandler{manager: manager}
}

func (p MultiHostRequestExtHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
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

func (p MultiHostRequestExtHandler) organizeValues(numOfVariablesArr []int, allValues []string) ([][]string, error) {
	sum, err := math.Sum(numOfVariablesArr)

	if err != nil {
		log.Error().Msgf("error calculating sum of variables: %s", err)
		return nil, errors.New("problem verifying functions")
	}

	if sum != len(allValues) {
		return nil, errors.New("variables sent does not match expectations")
	}

	var organizedValuesArr [][]string

	i := 0
	for _, numOfVariables := range numOfVariablesArr {
		organizedValues := allValues[i : i+numOfVariables]
		organizedValuesArr = append(organizedValuesArr, organizedValues)
		i = i + numOfVariables
	}

	return organizedValuesArr, nil
}

//func (p MultiHostRequestExtHandler) containsDuplicatedId(ids []string) bool {
//	m := make(map[string]struct{})
//
//	for _, id := range ids {
//		m[id] = struct{}{}
//	}
//
//	if len(m) != len(ids) {
//		return true
//	}
//
//	return false
//}

func (p MultiHostRequestExtHandler) forwardRequestToComputationObjects(w http.ResponseWriter, r *http.Request) {
	ids, allValues, err := p.baseHandler.getComputationIds(r)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("{ \"error\": \"missing parameters\" }"))
		return
	}

	if p.baseHandler.containsDuplicatedId(ids) {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("{ \"error\": \"duplicate handle_pacevalComputation\" }"))
		return
	}

	endpoints, numOfVariables, err := p.baseHandler.getEndpointsWithNumOfVariables(ids, p.manager)

	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		log.Error().Msgf("Error: %s", err)
		w.Write([]byte("{ \"error\": \"handle_pacevalComputation does not exist\" }"))
		return
	}

	organizedValues, err := p.organizeValues(numOfVariables, allValues)
	if err != nil {
		log.Error().Msgf("error: %s", err)
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte(fmt.Sprintf("{ \"error\": \"%s\" }", err)))
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

		go func(index int, endpoint string) {
			defer wg.Done()

			// Create a new HTTP client
			client := &http.Client{}

			proxyReq, err := http.NewRequest(http.MethodGet, "http://"+endpoint+"/GetComputationResult/", r.Body)
			//proxyReq, err := http.NewRequest(http.MethodGet, "http://localhost:9000/GetComputationResult/", r.Body)
			param := proxyReq.URL.Query()

			param.Add(data.VALUES, strings.Join(organizedValues[index], ";"))
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

		var responseArray []map[string]interface{}
		for _, body := range aggregatedResponse {
			var response map[string]interface{}
			json.Unmarshal(body, &response)

			responseArray = append(responseArray, response)
		}

		responseJSON, _ := json.Marshal(responseArray)

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

//func (p MultiHostRequestExtHandler) getEndpointsWithNumOfVariables(ids []string) ([]string, []int, error) {
//
//	endpoints := make([]string, len(ids))
//	numOfValues := make([]int, len(ids))
//	errorChan := make(chan error, len(ids))
//
//	var wg sync.WaitGroup
//	wg.Add(len(ids))
//	resultLock := sync.Mutex{}
//
//	for index, id := range ids {
//		go func(index int, id string) {
//			defer wg.Done()
//			endpoint, err := p.manager.GetEndpoint(id)
//			if err != nil {
//				log.Info().Msgf("id: %s, issue receiving endpoint : %s", id, err)
//				errorChan <- err
//				return
//			}
//			numOfVariablesStr, err := p.manager.GetNumOfVariables(id)
//			if err != nil {
//				log.Info().Msgf("id: %s, issue receiving num of variable : %s", id, err)
//				errorChan <- err
//				return
//			}
//
//			numOfVariables, err := strconv.Atoi(numOfVariablesStr)
//
//			if err != nil {
//				log.Info().Msgf("id: %s, issue receiving num of variable : %s", id, err)
//				errorChan <- err
//				return
//			}
//
//			resultLock.Lock()
//			defer resultLock.Unlock()
//
//			endpoints[index] = endpoint
//			numOfValues[index] = numOfVariables
//
//		}(index, id)
//	}
//
//	wg.Wait()
//	close(errorChan)
//
//	if len(errorChan) == 0 {
//		return endpoints, numOfValues, nil
//	}
//
//	var combinedError error
//
//	for err := range errorChan {
//		combinedError = multierror.Append(combinedError, err)
//	}
//
//	return nil, nil, combinedError
//
//}

//func (p MultiHostRequestExtHandler) getComputationIds(r *http.Request) ([]string, []string, error) {
//	log.Info().Msg("trying to search for computation object id")
//	switch r.Method {
//	case http.MethodGet:
//		decodeRawQuery, err := url.QueryUnescape(r.URL.RawQuery)
//		if err != nil {
//			// handle error: failed to parse query string
//			return nil, nil, err
//		}
//		rawQuery := strings.ReplaceAll(decodeRawQuery, ";", "#")
//
//		values, err := url.ParseQuery(rawQuery)
//		if err != nil {
//			// handle error: failed to parse query string
//			return nil, nil, err
//		}
//
//		if !values.Has(data.HANDLEPACEVALCOMPUTATIONS) || !values.Has(data.VALUES) {
//			return nil, nil, errors.New("missing parameters")
//		}
//
//		computationIds := strings.Split(values.Get(data.HANDLEPACEVALCOMPUTATIONS), "#")
//		allValues := strings.Split(values.Get(data.VALUES), "#")
//		log.Info().Msgf("computation object id %s", values.Get(data.HANDLEPACEVALCOMPUTATION))
//		return computationIds, allValues, nil
//	case http.MethodPost:
//		requestObject := make(map[string]string)
//		body, err := io.ReadAll(r.Body)
//
//		if err != nil {
//			return nil, nil, err
//		}
//
//		r.Body = io.NopCloser(bytes.NewBuffer(body))
//
//		if err = json.Unmarshal(body, &requestObject); err != nil {
//			return nil, nil, err
//		}
//
//		computationHandles, hasComputationHandles := requestObject[data.HANDLEPACEVALCOMPUTATIONS]
//		values, hasValues := requestObject[data.VALUES]
//
//		if !hasComputationHandles || !hasValues {
//			return nil, nil, errors.New("missing parameters")
//		}
//
//		computationIds := strings.Split(computationHandles, ";")
//		allValues := strings.Split(values, ";")
//
//		return computationIds, allValues, nil
//	default:
//		return nil, nil, errors.New("method not allowed")
//	}
//
//}
