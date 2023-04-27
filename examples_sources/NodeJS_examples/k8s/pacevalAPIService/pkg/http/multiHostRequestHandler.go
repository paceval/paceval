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
			extraReqParam: func(_ url.Values, _ *data.MultipleComputationRequestParam) {
				return
			},
			paramFromRequestValues: paramFromRequestValues,
			transformResponse:      transformMultipleComputationResultResponse,
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
		p.baseHandler.forwardRequestToComputationObjects(w, r)

	default:
		log.Info().Msg("method not allowed")
		w.WriteHeader(http.StatusMethodNotAllowed)
		w.Write([]byte("{ \"error\": \"Method not allowed\" }"))
	}

}

func paramFromRequestValues(values url.Values, _ *k8s.Manager) (*data.MultipleComputationRequestParam, error) {

	if !values.Has(data.HANDLEPACEVALCOMPUTATIONS) || !values.Has(data.NUMOFPACEVALCOMPUTATIONS) || !values.Has(data.VALUES) {
		return nil, errors.New("missing parameters")
	}

	computationIds := strings.Split(values.Get(data.HANDLEPACEVALCOMPUTATIONS), ";")
	allValues := strings.Split(values.Get(data.VALUES), ";")

	numComputations, err := strconv.Atoi(values.Get(data.NUMOFPACEVALCOMPUTATIONS))
	if err != nil {
		return nil, fmt.Errorf("parameter %s must be a integer", data.NUMOFPACEVALCOMPUTATIONS)
	}

	if len(computationIds) < 1 || len(allValues) < 1 {
		return nil, errors.New("parameter's length less than 1")
	}

	if len(computationIds) != numComputations {
		log.Debug().Msg("computationsIds & numComputation mismatch")
		return &data.MultipleComputationRequestParam{ComputationIds: computationIds}, data.InvalidRequestError{}
	}

	return &data.MultipleComputationRequestParam{
		ComputationIds:    computationIds,
		Values:            allValues,
		NumOfComputations: pointer.Int(numComputations),
		NumOfCalculations: nil,
	}, nil
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
