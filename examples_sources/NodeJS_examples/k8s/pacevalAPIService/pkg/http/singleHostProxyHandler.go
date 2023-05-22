package http

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/data"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/k8s"
	"github.com/rs/zerolog/log"
	"io"
	errorpkg "k8s.io/apimachinery/pkg/api/errors"
	"net/http"
	"net/http/httputil"
	"net/url"
	"strings"
)

// SingleHostProxyHandler handles a single proxy request to a computation service
type SingleHostProxyHandler struct {
	manager k8s.Manager
}

// NewSingleHostProxyHandler return a new instance of SingleHostProxyHandler
func NewSingleHostProxyHandler(manager k8s.Manager) SingleHostProxyHandler {
	return SingleHostProxyHandler{manager: manager}
}

// ServeHTTP handle the single proxy to a particular computation service
func (p SingleHostProxyHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	log.Info().Msg("handle request to get computation result")
	w.Header().Set("Content-Type", "application/json")
	log.Info().Msgf("incoming %s request", r.Method)

	switch r.Method {
	case http.MethodGet, http.MethodPost:
		p.forwardRequestToComputationObject(w, r)
	default:
		log.Info().Msg("method not allowed")
		w.WriteHeader(http.StatusMethodNotAllowed)
		w.Write([]byte("{ \"error\": \"Method not allowed\" }"))
	}
}

// forwardRequestToComputationObject proxys the single request to a particular computation service
func (p SingleHostProxyHandler) forwardRequestToComputationObject(w http.ResponseWriter, r *http.Request) {
	id, err := getComputationId(r)

	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("{ \"error\": \"missing parameters\" }"))
		return
	}

	log.Info().Msgf("forward request to computation object id: %s", id)

	endpoint, err := p.manager.GetEndpoint(id)

	//handle_pacevalComputation does not exist
	if err != nil && errorpkg.IsNotFound(err) {
		w.WriteHeader(http.StatusNotFound)
		w.Write([]byte("{ \"error\": \"handle_pacevalComputation does not exist\" }"))
		return
	} else if errors.Is(err, data.ServiceNotReadyError{}) {
		// computation is not ready
		response := NewFunctionNotReadyResponse(id, p.manager)
		responseJSON, _ := json.Marshal(response)

		w.WriteHeader(http.StatusOK)
		w.Write(responseJSON)

	} else if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		log.Error().Msgf("Error: %s", err)
		w.Write([]byte(fmt.Sprintf("{ \"error\": \"%s\" }", err)))
		return
	}

	log.Info().Msgf("computation object endpoint: %s", endpoint)

	targetURL, err := url.Parse("http://" + endpoint)

	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		log.Error().Msgf("error parsing URL to forward request: %s", err)
		w.Write([]byte("{ \"error\": \"internal error, please contact service admin\" }"))
		return
	}

	// start the request proxy
	proxy := httputil.NewSingleHostReverseProxy(targetURL)
	proxy.ServeHTTP(w, r)
}

// getComputationId fetches the UUID of a computation specified in incoming request
func getComputationId(r *http.Request) (string, error) {
	log.Info().Msg("trying to search for computation object id")
	switch r.Method {
	case http.MethodGet:
		// for GET request, the uuid should be found in query parameter
		values := r.URL.Query()
		if !values.Has(data.HANDLEPACEVALCOMPUTATION) {
			return "", errors.New("missing parameters")
		}
		log.Info().Msgf("computation object id %s", values.Get(data.HANDLEPACEVALCOMPUTATION))
		return values.Get(data.HANDLEPACEVALCOMPUTATION), nil
	case http.MethodPost:
		contentType := r.Header.Get("Content-Type")

		switch contentType {
		case "application/x-www-form-urlencoded":
			if err := r.ParseForm(); err != nil {
				return "", err
			}
			values := r.PostForm
			UrlDecode(values)
			if !values.Has(data.HANDLEPACEVALCOMPUTATION) {
				return "", errors.New("missing parameters")
			}

			r.Body = io.NopCloser(strings.NewReader(values.Encode()))
			log.Info().Msgf("computation object id %s", values.Get(data.HANDLEPACEVALCOMPUTATION))
			return values.Get(data.HANDLEPACEVALCOMPUTATION), nil

		case "application/json":
			// for POST request, the uuid should be found in request body
			requestObj := data.HandlePacevalComputationObject{}
			data, err := io.ReadAll(r.Body)

			if err != nil {
				return "", err
			}

			// make sure to set the request body back to request, otherwise it will not be readable later
			r.Body = io.NopCloser(bytes.NewBuffer(data))
			err = json.NewDecoder(bytes.NewReader(data)).Decode(&requestObj)

			if err != nil {
				return "", err
			}

			if len(requestObj.HandleCreateComputation) == 0 {
				return "", errors.New("missing parameters")
			}
			log.Info().Msgf("computation object id %s", requestObj.HandleCreateComputation)
			return requestObj.HandleCreateComputation, nil

		default:
			return "", errors.New(fmt.Sprintf("Content-type %s not allow", contentType))
		}
	default:
		return "", errors.New("method not allowed")
	}

}
