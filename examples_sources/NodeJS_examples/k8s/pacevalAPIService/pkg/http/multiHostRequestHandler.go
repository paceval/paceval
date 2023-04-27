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

// MultiHostRequestHandler is the handler for getMultipleComputationResult
type MultiHostRequestHandler struct {
	baseHandler MultiHostBaseHandler
}

// NewMultiHostRequestHandler return new instance of handler
func NewMultiHostRequestHandler(manager k8s.Manager) MultiHostRequestHandler {
	return MultiHostRequestHandler{
		baseHandler: MultiHostBaseHandler{
			requestPath: "GetComputationResult",
			manager:     manager,
		},
	}
}

// ServeHTTP proxy the requests to multiple computation services with a single value set
func (p MultiHostRequestHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	log.Info().Msg("handle request to get multiple computation result")
	w.Header().Set("Content-Type", "application/json")
	log.Info().Msgf("incoming %s request", r.Method)

	switch r.Method {
	case http.MethodGet, http.MethodPost:
		p.baseHandler.forwardRequestToComputationObjects(w, r, validateRequest, transformMultipleComputationResultResponse)

	default:
		log.Info().Msg("method not allowed")
		w.WriteHeader(http.StatusMethodNotAllowed)
		w.Write([]byte("{ \"error\": \"Method not allowed\" }"))
	}

}

func validateRequest(ids []string, _ []string, numOfComputations int, _ *k8s.Manager) bool {
	if len(ids) >= 1 {
		return len(ids) == numOfComputations
	}
	return false
}

func transformMultipleComputationResultResponse(aggregatedResponse [][]byte) interface{} {
	log.Info().Msgf(" Transforming aggregatedResponse for MultipleComputationResult")
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
