package http

import (
	"encoding/json"
	"fmt"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/data"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/k8s"
	"github.com/rs/zerolog/log"
	"math"
	"net/http"
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
		p.baseHandler.forwardRequestToComputationObjects(w, r, validateRequestExt, transformMultipleComputationResultExtResponse)

	default:
		log.Info().Msg("method not allowed")
		w.WriteHeader(http.StatusMethodNotAllowed)
		w.Write([]byte("{ \"error\": \"Method not allowed\" }"))
	}

}

func validateRequestExt(ids []string, allValues []string, numOfComputations int, manager *k8s.Manager) bool {
	if len(ids) >= 1 {
		numVariables, _ := manager.GetNumOfVariables(ids[0])
		numberOfVariablePerFunction, err := strconv.Atoi(numVariables)

		if err != nil {
			return false
		}

		if len(allValues) != numberOfVariablePerFunction*len(ids) {
			return false
		}

		return len(ids) == numOfComputations
	}
	return false
}

func transformMultipleComputationResultExtResponse(aggregatedResponse [][]byte) interface{} {
	log.Info().Msgf(" Transforming aggregatedResponse for MultipleComputationResult")
	transformedResponse := data.MultipleComputationExtResult{
		MultipleComputationResult: data.MultipleComputationResult{
			NumOfComputations: len(aggregatedResponse),
			FunctionIds:       []string{},
			HasError:          false,
			Results:           []string{},
			IntervalMins:      []string{},
			IntervalMaxs:      []string{},
			ErrorTypeNums:     []int{},
		},
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
