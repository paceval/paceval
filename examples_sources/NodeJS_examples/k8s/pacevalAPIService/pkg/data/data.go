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
	FunctionId    string  `json:"handle_pacevalComputation"`
	Result        string  `json:"result"`
	IntervalMin   string  `json:"interval-min-result"`
	IntervalMax   string  `json:"interval-max-result"`
	ErrorTypeNum  int     `json:"error-type-number"`
	ErrorPosition string  `json:"error-position"`
	ErrorType     string  `json:"error-type"`
	ErrorMessage  string  `json:"error-message"`
	TimeCalculate string  `json:"time-calculate"`
	Version       float32 `json:"version-number"`
}

type HandlePacevalComputationObject struct {
	HandleCreateComputation string `json:"handle_pacevalComputation,omitempty"`
}
