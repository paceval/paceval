package http

import (
	"bytes"
	"encoding/json"
	"github.com/google/uuid"
	"github.com/rs/zerolog/log"
	"io"
	"net/http"
	"net/http/httputil"
	"net/url"
)

const demoEndpoint = "http://demo-service-demoservice.default.svc.cluster.local"

type DemoHandler struct {
}

func NewDemoHandler() DemoHandler {
	return DemoHandler{}
}

func (d DemoHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	log.Info().Msg("handle request to demo request")
	w.Header().Set("Content-Type", "application/json")
	log.Info().Msgf("incoming %s request", r.Method)

	targetURL, err := url.Parse(demoEndpoint)
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		log.Error().Msgf("error parsing URL to forward request: %s", err)
		w.Write([]byte("{ \"error\": \"internal error, please contact service admin\" }"))
		return
	}

	uid, err := uuid.NewUUID()

	proxy := httputil.NewSingleHostReverseProxy(targetURL)

	proxy.ModifyResponse = func(response *http.Response) error {
		respObject := make(map[string]interface{})
		body, err := io.ReadAll(response.Body)

		if err != nil {
			return err
		}

		if err = json.Unmarshal(body, &respObject); err != nil {
			return err
		}

		respObject["handle_pacevalComputation"] = uid.String()
		modifiedBody, err := json.Marshal(respObject)

		if err != nil {
			return err
		}

		response.Body = io.NopCloser(bytes.NewBuffer(modifiedBody))

		return nil

	}

	proxy.ServeHTTP(w, r)

}
