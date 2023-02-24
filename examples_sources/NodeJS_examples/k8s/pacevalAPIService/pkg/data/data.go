package data

const (
	FUNCTIONSTR              = "functionString"
	NUMOFVARIABLES           = "numberOfVariables"
	VARAIBLES                = "variables"
	INTERVAL                 = "interval"
	HANDLEPACEVALCOMPUTATION = "handle_pacevalComputation"
	DEFAULTNAMESPACE         = "default"
)

type ParameterSet struct {
	FunctionStr    string `json:"functionString,omitempty"`
	NumOfVariables string `json:"numberOfVariables,omitempty"`
	Variables      string `json:"variables,omitempty"`
	Interval       string `json:"interval,omitempty"`
}

type HandlePacevalComputationObject struct {
	HandleCreateComputation string `json:"handle_pacevalComputation,omitempty"`
}
