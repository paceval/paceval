package http

import (
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/data"
	"github.com/paceval/paceval/examples_sources/NodeJS_examples/k8s/pacevalAPIService/pkg/k8s"
	"github.com/rs/zerolog/log"
	"net/url"
	"os"
	"strings"
)

func ParseQuery(query string) (url.Values, error) {
	m := make(url.Values)
	err := parseQuery(m, query)
	return m, err
}

func parseQuery(m url.Values, query string) (err error) {
	for query != "" {
		var key string
		key, query, _ = strings.Cut(query, "&")

		if key == "" {
			continue
		}
		key, value, _ := strings.Cut(key, "=")
		key, err1 := url.QueryUnescape(key)
		if err1 != nil {
			if err == nil {
				err = err1
			}
			continue
		}
		value, err1 = url.PathUnescape(value)
		if err1 != nil {
			if err == nil {
				err = err1
			}
			continue
		}
		m[key] = append(m[key], value)
	}
	return err
}

func NewFunctionNotReadyResponse(id string, manager k8s.Manager) data.FunctionNotReadyResponse {
	functionStrTenChar, functionLength := getFunctionStr10Char(manager, id)

	return data.FunctionNotReadyResponse{
		FunctionId:      id,
		FunctionTenChar: functionStrTenChar,
		FunctionLength:  functionLength,
		ErrorTypeNum:    1,
		ErrorPosition:   "",
		ErrorType:       "[Busy #1, Operator '(not defined)', Position -1]",
		ErrorMessage:    "The referenced computation object is busy while the creation is in progress. Please wait and make another request to GetErrorInformation for the status (PACEVAL_ERR_CREATION_NO_ERROR_BUT_BUSY).",
		TimeCalculate:   "0s",
		Version:         4.04,
	}
}

func getFunctionStr10Char(manager k8s.Manager, id string) (string, int) {
	functionStr, err := manager.GetFunctionStr(id)

	functionLength := len(functionStr)

	if functionLength > 10 {
		functionStr = functionStr[:10]
	} else if strings.HasPrefix(functionStr, "redis") {
		address := os.Getenv("REDIS_ADDRESS")
		redisClient := data.NewRedis(address)
		functionStr, _ = redisClient.Get(functionStr)
		defer redisClient.CloseConnection()
	}

	if err != nil {
		log.Error().Msgf("Error get functionStr from id %s", id)
	}

	return functionStr, functionLength
}
