package data

// constants and struct used by another packages

const (
	FUNCTIONSTR               = "functionString"
	NUMOFVARIABLES            = "numberOfVariables"
	VARAIBLES                 = "variables"
	INTERVAL                  = "interval"
	HANDLEPACEVALCOMPUTATION  = "handle_pacevalComputation"
	HANDLEPACEVALCOMPUTATIONS = "handle_pacevalComputations"

	NUMOFCOMPUTATIONS = "numberOfpacevalComputations"

	VALUES = "values"

	DEFAULTNAMESPACE = "default"
)

type ParameterSet struct {
	FunctionStr    string `json:"functionString,omitempty"`
	NumOfVariables string `json:"numberOfVariables,omitempty"`
	Variables      string `json:"variables,omitempty"`
	Interval       string `json:"interval,omitempty"`
}

type DemoParameterSet struct {
	ParameterSet
	Values string `json:"values,omitempty"`
}

type DemoServiceResponse struct {
	FunctionId    string  `json:"handle_pacevalComputation,omitempty"`
	Result        string  `json:"result,omitempty"`
	IntervalMin   string  `json:"interval-min-result,omitempty"`
	IntervalMax   string  `json:"interval-max-result,omitempty"`
	ErrorTypeNum  int     `json:"error-type-number,omitempty"`
	ErrorPosition string  `json:"error-position,omitempty"`
	ErrorType     string  `json:"error-type,omitempty"`
	ErrorMessage  string  `json:"error-message,omitempty"`
	TimeCalculate string  `json:"time-calculate,omitempty"`
	Version       float32 `json:"version-number,omitempty"`
}

type HandlePacevalComputationObject struct {
	HandleCreateComputation string `json:"handle_pacevalComputation,omitempty"`
}
