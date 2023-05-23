package http

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/data"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/k8s"
	"github.com/rs/zerolog/log"
	"k8s.io/utils/pointer"
	"math"
	"net/http"
	"net/url"
	"strconv"
	"strings"
)

// MultiHostRequestExtHandler is the handler for getMultipleComputationResultExt
type MultiHostRequestExtHandler struct {
	manager     k8s.Manager
	baseHandler MultiHostBaseHandler
}

// NewMultiHostRequestExtHandler return a new instance of handler
func NewMultiHostRequestExtHandler(manager k8s.Manager) MultiHostRequestExtHandler {
	return MultiHostRequestExtHandler{
		baseHandler: MultiHostBaseHandler{
			requestPath: "GetComputationResultExt",
			manager:     manager,
			extraReqParam: func(values url.Values, reqParam *data.MultipleComputationRequestParam) {
				values.Add(data.NUMOFCALCULATIONS, strconv.Itoa(*reqParam.NumOfCalculations))
			},
			paramFromRequestValues: paramFromRequestExtValues,
			transformResponse:      transformMultipleComputationResultExtResponse,
		},
	}
}

// ServeHTTP proxy the requests to multiple computation services with different value sets
func (p MultiHostRequestExtHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	log.Info().Msg("handle request to get multiple computation ext result")
	w.Header().Set("Content-Type", "application/json")
	log.Info().Msgf("incoming %s request", r.Method)

	switch r.Method {
	case http.MethodGet, http.MethodPost:
		p.baseHandler.forwardRequestToComputationObjects(w, r)

	default:
		log.Info().Msg("method not allowed")
		w.WriteHeader(http.StatusMethodNotAllowed)
		w.Write([]byte("{ \"error\": \"Method not allowed\" }"))
	}

}

func paramFromRequestExtValues(values url.Values, manager *k8s.Manager) (*data.MultipleComputationRequestParam, error) {

	if !values.Has(data.HANDLEPACEVALCOMPUTATIONS) || !values.Has(data.NUMOFPACEVALCOMPUTATIONS) || !values.Has(data.VALUES) || !values.Has(data.NUMOFCALCULATIONS) {
		return nil, errors.New("missing parameters")
	}

	if values.Get(data.HANDLEPACEVALCOMPUTATIONS) == "" || values.Get(data.VALUES) == "" {
		return nil, errors.New("parameter cannot be empty")
	}
	computationIds := strings.Split(values.Get(data.HANDLEPACEVALCOMPUTATIONS), ";")
	allValues := strings.Split(values.Get(data.VALUES), ";")

	numComputations, err := strconv.Atoi(values.Get(data.NUMOFPACEVALCOMPUTATIONS))
	if err != nil {
		return nil, fmt.Errorf("parameter %s must be a integer", data.NUMOFPACEVALCOMPUTATIONS)
	}

	numCalculations, err := strconv.Atoi(values.Get(data.NUMOFCALCULATIONS))
	if err != nil {
		return nil, fmt.Errorf("parameter %s must be a integer", data.NUMOFCALCULATIONS)
	}

	numVariables, _ := manager.GetNumOfVariables(computationIds[0])
	numberOfVariablePerFunction, err := strconv.Atoi(numVariables)

	if err != nil {
		return nil, fmt.Errorf("parameter %s must be a integer", data.NUMOFPACEVALCOMPUTATIONS)
	}

	if len(computationIds) != numComputations || len(allValues) != numberOfVariablePerFunction*numCalculations {
		log.Debug().Msg("computationsIds & numComputation mismatch")
		return &data.MultipleComputationRequestParam{ComputationIds: computationIds}, data.InvalidRequestError{}
	}

	return &data.MultipleComputationRequestParam{
		ComputationIds:    computationIds,
		Values:            allValues,
		NumOfComputations: pointer.Int(numComputations),
		NumOfCalculations: pointer.Int(numCalculations),
	}, nil
}

func transformMultipleComputationResultExtResponse(aggregatedResponse [][]byte) interface{} {
	log.Info().Msgf(" Transforming aggregatedResponse for MultipleComputationResult")
	transformedResponse := data.MultipleComputationExtResult{
		NumOfComputations: len(aggregatedResponse),
		FunctionIds:       []string{},
		HasError:          false,
		Results:           []string{},
		IntervalMins:      []string{},
		IntervalMaxs:      []string{},
		ErrorTypeNums:     []int{},
	}

	var maxTimeCalculate float64 = 0
	var numOfCalculation int = 0

	for _, body := range aggregatedResponse {
		var response data.ComputationResultExt
		json.Unmarshal(body, &response)

		log.Debug().Msgf("response : %v", response)

		transformedResponse.FunctionIds = append(transformedResponse.FunctionIds, response.FunctionId)
		transformedResponse.Results = append(transformedResponse.Results, response.Results...)
		transformedResponse.IntervalMins = append(transformedResponse.IntervalMins, response.IntervalMins...)
		transformedResponse.IntervalMaxs = append(transformedResponse.IntervalMaxs, response.IntervalMaxs...)
		transformedResponse.ErrorTypeNums = append(transformedResponse.ErrorTypeNums, response.ErrorTypeNums...)

		if response.HasError {
			transformedResponse.HasError = true
		}

		timeCalculate, err := strconv.ParseFloat(strings.TrimSuffix(response.TimeCalculate, "s"), 64)
		if err != nil {
			log.Debug().Msgf(" Unable to parse time calculate, skipping...")
			continue
		}

		maxTimeCalculate = math.Max(maxTimeCalculate, timeCalculate)
		transformedResponse.Version = response.Version

		numOfCalculation = response.NumOfCalculation

	}

	transformedResponse.NumOfCalculation = numOfCalculation
	transformedResponse.TimeCalculate = fmt.Sprintf("%fs", maxTimeCalculate)

	return transformedResponse

}
