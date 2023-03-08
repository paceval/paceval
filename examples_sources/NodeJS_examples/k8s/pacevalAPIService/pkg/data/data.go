package data

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

type HandlePacevalComputationObject struct {
	HandleCreateComputation string `json:"handle_pacevalComputation,omitempty"`
}
