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

// DemoHandler take cares of the request to demo service
type DemoHandler struct {
	manager k8s.Manager
}

func NewDemoHandler(manager k8s.Manager) DemoHandler {
	return DemoHandler{manager: manager}
}

// ServeHTTP serve the incoming request to demo endpoint
func (d DemoHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	log.Info().Msg("handle request to demo request")
	w.Header().Set("Content-Type", "application/json")
	log.Info().Msgf("incoming %s request", r.Method)

	// prepare the internal request to demo service
	targetURL, err := url.Parse(demoEndpoint)
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		log.Error().Msgf("error parsing URL to forward request: %s", err)
		w.Write([]byte("{ \"error\": \"internal error, please contact service admin\" }"))
		return
	}

	// generating UUID for the new computation object
	uid, _ := uuid.NewUUID()

	// take input from incoming request
	param, err := d.getParameters(r)

	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		log.Error().Msgf("error parsing URL to forward request: %s", err)
		w.Write([]byte(fmt.Sprintf("{ \"error\": \"%s\" }", err)))
		return
	}

	// create the computation CRD
	d.manager.CreateComputation(uid, &param.ParameterSet)

	// forward request to demo service
	proxy := httputil.NewSingleHostReverseProxy(targetURL)

	proxy.ModifyResponse = func(response *http.Response) error {
		// make sure to modify the response from demo service and replace the field `handle_pacevalComputation` with above generated uuid

		demoResponse := new(data.ComputationResult)
		body, err := io.ReadAll(response.Body)

		if err != nil {
			return err
		}

		if err = json.Unmarshal(body, &demoResponse); err != nil {
			return err
		}

		demoResponse.FunctionId = uid.String()

		if err != nil {
			return err
		}

		modifiedBody, err := json.Marshal(demoResponse)

		if err != nil {
			return err
		}

		response.Body = io.NopCloser(bytes.NewBuffer(modifiedBody))

		return nil

	}

	// start request proxying
	proxy.ServeHTTP(w, r)

}

// getParameters retrieves the input from incoming request and transform them into data.DemoParameterSet
func (d DemoHandler) getParameters(r *http.Request) (*data.DemoParameterSet, error) {
	switch r.Method {
	case http.MethodGet:

		values, err := ParseQuery(r.URL.RawQuery)

		//values, err := url.ParseQuery(rawQuery)
		if err != nil {
			// handle error: failed to parse query string
			return nil, err
		}
		if !values.Has(data.FUNCTIONSTR) || !values.Has(data.NUMOFVARIABLES) || !values.Has(data.VARAIBLES) || !values.Has(data.VALUES) || !values.Has(data.INTERVAL) {
			return nil, errors.New("missing parameters")
		}

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
		contentType := r.Header.Get("Content-Type")

		switch contentType {
		case "application/x-www-form-urlencoded":
			if err := r.ParseForm(); err != nil {
				return nil, err
			}
			values := r.PostForm
			if !values.Has(data.FUNCTIONSTR) || !values.Has(data.NUMOFVARIABLES) || !values.Has(data.VARAIBLES) || !values.Has(data.VALUES) || !values.Has(data.INTERVAL) {
				return nil, errors.New("missing parameters")
			}

			r.Body = io.NopCloser(strings.NewReader(values.Encode()))
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

		case "application/json":
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
			return nil, errors.New(fmt.Sprintf("Content-type %s not allow", contentType))
		}
	default:
		return nil, errors.New("method not allowed")
	}
}
