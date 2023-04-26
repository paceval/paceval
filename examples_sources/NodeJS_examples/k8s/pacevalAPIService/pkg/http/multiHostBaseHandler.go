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
	"math"
	"net/http"
	"strconv"
	"strings"
	"sync"
)

// MultiHostBaseHandler is a base handler that has the common functions shared by multiple host request handlers
type MultiHostBaseHandler struct {
}

// transformResponse transforms the aggregatedResponse in [][] into a data.MultipleComputationResult object
func (p MultiHostBaseHandler) transformResponse(aggregatedResponse [][]byte) data.MultipleComputationResult {
	log.Info().Msgf(" Transforming aggregatedResponse")
	transformedResponse := data.MultipleComputationResult{
		NumOfComputations: len(aggregatedResponse),
		FunctionIds:       []string{},
		HasError:          false,
		Results:           []string{},
		IntervalMins:      []string{},
		IntervalMaxs:      []string{},
		ErrorTypeNums:     []int{},
	}

	var maxTimeCalculate float64 = 0

	for _, body := range aggregatedResponse {
		var response data.ComputationResult
		json.Unmarshal(body, &response)

		log.Debug().Msgf("response : %v", response)

		transformedResponse.FunctionIds = append(transformedResponse.FunctionIds, response.FunctionId)
		transformedResponse.Results = append(transformedResponse.Results, response.Result)
		transformedResponse.IntervalMins = append(transformedResponse.IntervalMins, response.IntervalMin)
		transformedResponse.IntervalMaxs = append(transformedResponse.IntervalMaxs, response.IntervalMax)
		transformedResponse.ErrorTypeNums = append(transformedResponse.ErrorTypeNums, response.ErrorTypeNum)

		if response.ErrorTypeNum != 0 {
			transformedResponse.HasError = true
		}

		timeCalculate, err := strconv.ParseFloat(strings.TrimSuffix(response.TimeCalculate, "s"), 64)

		if err != nil {
			log.Debug().Msgf(" Unable to parse time calculate, skipping...")
			continue
		}

		maxTimeCalculate = math.Max(maxTimeCalculate, timeCalculate)

		transformedResponse.Version = response.Version
	}

	transformedResponse.TimeCalculate = fmt.Sprintf("%fs", maxTimeCalculate)

	return transformedResponse

}

// getComputationIds returns computation IDs from incoming request
func (p MultiHostBaseHandler) getComputationIds(r *http.Request, validateRequest func([]string, int) bool) ([]string, []string, error) {
	log.Info().Msg("trying to search for computation object id")
	switch r.Method {
	case http.MethodGet:
		values, err := ParseQuery(r.URL.RawQuery)

		if err != nil {
			// handle error: failed to parse query string
			return nil, nil, err
		}

		if !values.Has(data.HANDLEPACEVALCOMPUTATIONS) || !values.Has(data.NUMOFPACEVALCOMPUTATIONS) || !values.Has(data.VALUES) {
			return nil, nil, errors.New("missing parameters")
		}

		computationIds := strings.Split(values.Get(data.HANDLEPACEVALCOMPUTATIONS), ";")

		numComputations, err := strconv.Atoi(values.Get(data.NUMOFPACEVALCOMPUTATIONS))

		if err != nil {
			return nil, nil, fmt.Errorf("parameter %s must be a integer", data.NUMOFPACEVALCOMPUTATIONS)
		}

		if !validateRequest(computationIds, numComputations) {
			return computationIds, nil, data.InvalidRequestError{}
		}

		allValues := strings.Split(values.Get(data.VALUES), ";")
		log.Info().Msgf("computation object id %s", values.Get(data.HANDLEPACEVALCOMPUTATION))
		return computationIds, allValues, nil
	case http.MethodPost:
		contentType := r.Header.Get("Content-Type")

		switch contentType {
		case "application/x-www-form-urlencoded":
			if err := r.ParseForm(); err != nil {
				return nil, nil, err
			}
			values := r.PostForm

			if !values.Has(data.HANDLEPACEVALCOMPUTATIONS) || !values.Has(data.NUMOFPACEVALCOMPUTATIONS) || !values.Has(data.VALUES) {
				return nil, nil, errors.New("missing parameters")
			}

			computationIds := strings.Split(values.Get(data.HANDLEPACEVALCOMPUTATIONS), ";")

			numComputations, err := strconv.Atoi(values.Get(data.NUMOFPACEVALCOMPUTATIONS))

			if err != nil {
				return nil, nil, fmt.Errorf("parameter %s must be a integer", data.NUMOFPACEVALCOMPUTATIONS)
			}

			if !validateRequest(computationIds, numComputations) {
				return computationIds, nil, data.InvalidRequestError{}
			}

			allValues := strings.Split(values.Get(data.VALUES), ";")

			r.Body = io.NopCloser(strings.NewReader(values.Encode()))
			log.Info().Msgf("computation object id %s", values.Get(data.HANDLEPACEVALCOMPUTATION))
			return computationIds, allValues, nil

		case "application/json":
			requestObject := make(map[string]string)
			body, err := io.ReadAll(r.Body)

			if err != nil {
				return nil, nil, err
			}

			r.Body = io.NopCloser(bytes.NewBuffer(body))

			if err = json.Unmarshal(body, &requestObject); err != nil {
				return nil, nil, err
			}

			computationHandles, hasComputationHandles := requestObject[data.HANDLEPACEVALCOMPUTATIONS]
			values, hasValues := requestObject[data.VALUES]
			numOfComputations, hasNumOfComputations := requestObject[data.NUMOFPACEVALCOMPUTATIONS]

			if !hasComputationHandles || !hasValues || !hasNumOfComputations {
				return nil, nil, errors.New("missing parameters")
			}

			computationIds := strings.Split(computationHandles, ";")

			numComputations, err := strconv.Atoi(numOfComputations)

			if err != nil {
				return nil, nil, fmt.Errorf("parameter %s must be a integer", data.NUMOFPACEVALCOMPUTATIONS)
			}

			if !validateRequest(computationIds, numComputations) {
				return computationIds, nil, data.InvalidRequestError{}
			}

			allValues := strings.Split(values, ";")

			return computationIds, allValues, nil

		default:
			return nil, nil, errors.New(fmt.Sprintf("Content-type %s not allow", contentType))
		}
	default:
		return nil, nil, errors.New("method not allowed")
	}

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

// getEndpointsWithNumOfVariables return endpoints and number of variables from multiple CRDs
// the request will be running in parallel, the output slices of string is the slice of endpoints
// and output slices of integers is the slice of numOfVariables
// the order of data in the slice is the order of ids from the input
func (p MultiHostBaseHandler) getEndpointsWithNumOfVariables(ids []string, manager k8s.Manager) ([]string, []int, error) {

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

// containsDuplicatedId check for duplicated id in slices of ID
func (p MultiHostBaseHandler) containsDuplicatedId(ids []string) bool {
	m := make(map[string]struct{})

	for _, id := range ids {
		m[id] = struct{}{}
	}

	if len(m) != len(ids) {
		return true
	}

	return false
}

func (p MultiHostBaseHandler) buildResponseForInvalidReq(ids []string, w http.ResponseWriter) {
	w.WriteHeader(http.StatusBadRequest)
	resp := createRespForInvalidReq(ids, data.PACEVAL_ERR_COMPUTATION_WRONGLY_USED_PARAMETERS)
	json.NewEncoder(w).Encode(resp)
}

func (p MultiHostBaseHandler) validateFunctionsFromRequest(numOfVariables []int) bool {

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
