package http

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/google/uuid"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/data"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/k8s"
	"github.com/rs/zerolog/log"
	"io"
	"net/http"
	"net/http/httputil"
	"net/url"
	"strings"
)

const demoEndpoint = "http://demo-service-demoservice.default.svc.cluster.local"

//const demoEndpoint = "http://localhost:9000"

type DemoHandler struct {
	manager k8s.Manager
}

func NewDemoHandler(manager k8s.Manager) DemoHandler {
	return DemoHandler{manager: manager}
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

	uid, _ := uuid.NewUUID()
	param, err := d.getParameters(r)

	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		log.Error().Msgf("error parsing URL to forward request: %s", err)
		w.Write([]byte(fmt.Sprintf("{ \"error\": \"%s\" }", err)))
		return
	}

	d.manager.CreateComputation(uid, &param.ParameterSet)

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

func (d DemoHandler) getParameters(r *http.Request) (*data.DemoParameterSet, error) {
	switch r.Method {
	case http.MethodGet:
		decodeRawQuery, err := url.QueryUnescape(r.URL.RawQuery)
		if err != nil {
			// handle error: failed to parse query string
			return nil, err
		}
		rawQuery := strings.ReplaceAll(decodeRawQuery, ";", "#")

		values, err := url.ParseQuery(rawQuery)
		if err != nil {
			// handle error: failed to parse query string
			return nil, err
		}
		if !values.Has(data.FUNCTIONSTR) || !values.Has(data.NUMOFVARIABLES) || !values.Has(data.VARAIBLES) || !values.Has(data.VALUES) || !values.Has(data.INTERVAL) {
			return nil, errors.New("missing parameters")
		}

		values.Set(data.VARAIBLES, strings.ReplaceAll(values.Get(data.VARAIBLES), "#", ";"))
		values.Set(data.VALUES, strings.ReplaceAll(values.Get(data.VALUES), "#", ";"))

		log.Info().Msgf("computation object id %s", values.Get(data.HANDLEPACEVALCOMPUTATION))
		return &data.DemoParameterSet{
			ParameterSet: data.ParameterSet{
				FunctionStr:    values.Get(data.FUNCTIONSTR),
				NumOfVariables: values.Get(data.NUMOFVARIABLES),
				Variables:      values.Get(data.VARAIBLES),
				Interval:       values.Get(data.INTERVAL),
			},
			Values: values.Get(data.VALUES),
		}, nil

	case http.MethodPost:
		requestObj := data.DemoParameterSet{}
		data, err := io.ReadAll(r.Body)

		if err != nil {
			return nil, err
		}

		r.Body = io.NopCloser(bytes.NewBuffer(data))
		err = json.NewDecoder(bytes.NewReader(data)).Decode(&requestObj)

		if err != nil {
			return nil, err
		}

		if len(requestObj.Values) == 0 || len(requestObj.FunctionStr) == 0 || len(requestObj.Variables) == 0 || len(requestObj.NumOfVariables) == 0 || len(requestObj.Interval) == 0 {
			return nil, errors.New("missing parameters")
		}
		return &requestObj, nil
	default:
		return nil, errors.New("method not allowed")
	}
}
