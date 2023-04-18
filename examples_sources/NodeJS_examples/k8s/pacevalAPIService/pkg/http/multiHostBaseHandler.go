package http

import (
	"bytes"
	"encoding/json"
	"errors"
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
}

// getComputationIds returns computation IDs from incoming request
func (p MultiHostBaseHandler) getComputationIds(r *http.Request) ([]string, []string, error) {
	log.Info().Msg("trying to search for computation object id")
	switch r.Method {
	case http.MethodGet:
		decodeRawQuery, err := url.QueryUnescape(r.URL.RawQuery)
		if err != nil {
			// handle error: failed to parse query string
			return nil, nil, err
		}
		rawQuery := strings.ReplaceAll(decodeRawQuery, ";", "#")

		values, err := url.ParseQuery(rawQuery)
		if err != nil {
			// handle error: failed to parse query string
			return nil, nil, err
		}

		if !values.Has(data.HANDLEPACEVALCOMPUTATIONS) || !values.Has(data.VALUES) {
			return nil, nil, errors.New("missing parameters")
		}

		computationIds := strings.Split(values.Get(data.HANDLEPACEVALCOMPUTATIONS), "#")
		allValues := strings.Split(values.Get(data.VALUES), "#")
		log.Info().Msgf("computation object id %s", values.Get(data.HANDLEPACEVALCOMPUTATION))
		return computationIds, allValues, nil
	case http.MethodPost:
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

		if !hasComputationHandles || !hasValues {
			return nil, nil, errors.New("missing parameters")
		}

		computationIds := strings.Split(computationHandles, ";")
		allValues := strings.Split(values, ";")

		return computationIds, allValues, nil
	default:
		return nil, nil, errors.New("method not allowed")
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
			if err != nil {
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
