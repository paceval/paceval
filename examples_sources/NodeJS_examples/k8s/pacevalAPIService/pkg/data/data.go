package data

// constants and struct used by another packages

const (
	FUNCTIONSTR               = "functionString"
	NUMOFVARIABLES            = "numberOfVariables"
	VARAIBLES                 = "variables"
	INTERVAL                  = "interval"
	HANDLEPACEVALCOMPUTATION  = "handle_pacevalComputation"
	HANDLEPACEVALCOMPUTATIONS = "handle_pacevalComputations"

	NUMOFPACEVALCOMPUTATIONS = "numberOfpacevalComputations"
	NUMOFCALCULATIONS        = "numberOfCalculations"

	NUMOFCOMPUTATIONS = "numberOfpacevalComputations"

	VALUES = "values"

	DEFAULTNAMESPACE = "default"

	NOTREADY_ENDPOINT = "NotReady"

	PACEVAL_ERR_COMPUTATION_WRONGLY_USED_PARAMETERS = 155

	PACEVAL_VERSION = 4.04
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

type FunctionNotReadyResponse struct {
	FunctionId      string  `json:"handle_pacevalComputation"`
	HasError        bool    `json:"hasError"`
	FunctionTenChar string  `json:"function-10chars"`
	FunctionLength  int     `json:"function-length"`
	ErrorTypeNum    int     `json:"error-type-number"`
	ErrorPosition   string  `json:"error-position"`
	ErrorType       string  `json:"error-type"`
	ErrorMessage    string  `json:"error-message"`
	TimeCalculate   string  `json:"time-calculate"`
	Version         float32 `json:"version-number"`
}

type ComputationResult struct {
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

type ComputationResultSpecial struct {
	*ComputationResult
	ErrorPosition int `json:"error-position"`
}

type ComputationResultExt struct {
	NumOfCalculation int      `json:"number-of-multiple-values"`
	FunctionId       string   `json:"handle_pacevalComputation"`
	HasError         bool     `json:"hasError"`
	Results          []string `json:"results"`
	IntervalMins     []string `json:"interval-min-results"`
	IntervalMaxs     []string `json:"interval-max-results"`
	ErrorTypeNums    []int    `json:"error-type-numbers"`
	TimeCalculate    string   `json:"time-calculate"`
	Version          float32  `json:"version-number"`
}
type MultipleComputationResult struct {
	NumOfComputations int      `json:"number-of-multiple-computations"`
	FunctionIds       []string `json:"handle_pacevalComputations"`
	HasError          bool     `json:"hasError"`
	Results           []string `json:"results"`
	IntervalMins      []string `json:"interval-min-results"`
	IntervalMaxs      []string `json:"interval-max-results"`
	ErrorTypeNums     []int    `json:"error-type-numbers"`
	TimeCalculate     string   `json:"time-calculate"`
	Version           float32  `json:"version-number"`
}

type MultipleComputationExtResult struct {
	NumOfComputations int      `json:"number-of-multiple-computations"`
	NumOfCalculation  int      `json:"number-of-multiple-values-per-computation"`
	FunctionIds       []string `json:"handle_pacevalComputations"`
	HasError          bool     `json:"hasError"`
	Results           []string `json:"results"`
	IntervalMins      []string `json:"interval-min-results"`
	IntervalMaxs      []string `json:"interval-max-results"`
	ErrorTypeNums     []int    `json:"error-type-numbers"`
	TimeCalculate     string   `json:"time-calculate"`
	Version           float32  `json:"version-number"`
}

type MultipleComputationRequestParam struct {
	ComputationIds    []string
	Values            []string
	NumOfComputations *int
	NumOfCalculations *int
}

type HandlePacevalComputationObject struct {
	HandleCreateComputation string `json:"handle_pacevalComputation,omitempty"`
}

type ServiceNotReadyError struct {
}

func (e ServiceNotReadyError) Error() string {
	return "computation is not ready"
}

type InvalidRequestError struct {
}

func (e InvalidRequestError) Error() string {
	return "incoming request is invalid"
}
