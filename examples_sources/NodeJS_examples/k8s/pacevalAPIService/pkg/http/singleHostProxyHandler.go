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
)

type SingleHostProxyHandler struct {
	manager k8s.Manager
}

func NewSingleHostProxyHandler(manager k8s.Manager) SingleHostProxyHandler {
	return SingleHostProxyHandler{manager: manager}
}

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

func (p SingleHostProxyHandler) forwardRequestToComputationObject(w http.ResponseWriter, r *http.Request) {
	id, err := p.getComputationId(r)

	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte("{ \"error\": \"missing parameters\" }"))
		return
	}

	log.Info().Msgf("forward request to computation object id: %s", id)

	endpoint, err := p.manager.GetEndpoint(id)

	//handle_pacevalComputation does not exist
	if err != nil && errorpkg.IsNotFound(err) {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte("{ \"error\": \"handle_pacevalComputation does not exist\" }"))
		return
	} else if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(fmt.Sprintf("{ \"error\": \"%s\" }", err)))
		return
	}

	log.Info().Msgf("computation object endpoint: %s", endpoint)

	targetURL, err := url.Parse("http://" + endpoint)

	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte("{ \"error\": \"error parse URL to forward request\" }"))
		return
	}

	proxy := httputil.NewSingleHostReverseProxy(targetURL)
	proxy.ServeHTTP(w, r)

	//https://stackoverflow.com/questions/34724160/go-http-send-incoming-http-request-to-an-other-server-using-client-do
	//url := r.Clone(context.Background()).URL
	//url.Host = endpoint + ":9000"
	//url.Scheme = "http"
	//
	//proxyReq, err := http.NewRequest(r.Method, url.String(), r.Clone(context.Background()).Body)
	//
	//if err != nil {
	//	w.WriteHeader(http.StatusInternalServerError)
	//	w.Write([]byte(fmt.Sprintf("{ \"error\": \"%s\" }", err)))
	//	return
	//}
	//
	//proxyReq.Header.Set("Host", r.Host)
	//proxyReq.Header.Set("X-Forwarded-For", r.RemoteAddr)
	//
	//// add all original request header to proxy request
	//for header, values := range r.Header {
	//	for _, value := range values {
	//		proxyReq.Header.Add(header, value)
	//	}
	//}
	//
	//client := &http.Client{}
	//proxyRes, err := client.Do(proxyReq)
	//if err != nil {
	//	w.WriteHeader(http.StatusInternalServerError)
	//	w.Write([]byte(fmt.Sprintf("{ \"error\": \"%s\" }", err)))
	//	return
	//}
	//
	//respBody, err := io.ReadAll(proxyRes.Body)
	//defer proxyRes.Body.Close()
	//if err != nil {
	//	w.WriteHeader(http.StatusInternalServerError)
	//	w.Write([]byte(fmt.Sprintf("{ \"error\": \"%s\" }", err)))
	//	return
	//}
	//
	//log.Info().Msg("received response from target")
	//w.WriteHeader(proxyRes.StatusCode)
	//w.Write(respBody)
}

func (p SingleHostProxyHandler) getComputationId(r *http.Request) (string, error) {
	log.Info().Msg("trying to search for computation object id")
	switch r.Method {
	case http.MethodGet:
		values := r.URL.Query()
		if !values.Has(data.HANDLEPACEVALCOMPUTATION) {
			return "", errors.New("missing parameters")
		}
		log.Info().Msgf("computation object id %s", values.Get(data.HANDLEPACEVALCOMPUTATION))
		return values.Get(data.HANDLEPACEVALCOMPUTATION), nil
	case http.MethodPost:
		requestObj := data.HandlePacevalComputationObject{}
		data, err := io.ReadAll(r.Body)

		if err != nil {
			return "", err
		}

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
		return "", errors.New("method not allowed")
	}

}
