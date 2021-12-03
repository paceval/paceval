<?php

// PHP example a simple mathematical engine, e.g. to offload battery-operated IoT devices

//EXAMPLE URL
// standard:
//   https://paceval-service.com/?call=paceval&functionString=-sin(x*cos(x))^(1/y)&numberOfVariables=2&variables=x;y&values=0.5;2
// interval:
//   https://paceval-service.com/?call=paceval&functionString=-sin(x*cos(x))^(1/y)&numberOfVariables=2&variables=x;y&values=0.5;2&interval=yes
// cURL:
//   curl -d "call=paceval&functionString=-sin(x*cos(x))^(1/y)&numberOfVariables=2&variables=x;y&values=0.5;2&interval=no" -X POST https://paceval-service.com/

// calculates the function with the specified variables and values and
// returns its result (optionally with upper and lower limit) in a JSON format

if (isset($_POST['call']))
{
    $call_str = $_POST["call"];
    $numberOfVariables = $_POST["numberOfVariables"];
    $variables_ar = explode(";", $_POST["variables"]);
    $variables_str = implode( " ", $variables_ar);
    $values_ar = explode(";", $_POST["values"]);
    $function_str = $_POST["functionString"];
    $interval_str = $_POST["interval"];
}
else
{
    $call_str = $_GET["call"];
    $numberOfVariables = $_GET["numberOfVariables"];
    $variables_ar = explode(";", $_GET["variables"]);
    $variables_str = implode( " ", $variables_ar);
    $values_ar = explode(";", $_GET["values"]);
    $function_str = $_GET["functionString"];
    $interval_str = $_GET["interval"];
}

if (($interval_str == "yes") || ($interval_str == "true"))
    $interval = true;

$paceval_ffi = FFI::cdef("
                         bool pacevalLibrary_Initialize(const char* initString_in);
                         bool pacevalLibrary_Free();
                         void* pacevalLibrary_CreateComputation(const char* functionString_in,
                         unsigned long numberOfVariables_in, const char* variables_in, bool useInterval_in, void* paceval_callbackStatus_in);
                         double pacevalLibrary_dmathv(void* handle_pacevalComputation_out_in, int *errorType_out,
                         const char* functionString_in, unsigned long numberOfVariables_in, const char* variables_in, double values_in[]);
                         bool pacevalLibrary_DeleteComputation(void* handle_pacevalComputation_in);
                         int pacevalLibrary_CreateErrorInformationText(void* handle_pacevalComputation_in, char* lastError_strMessage_out,
                         char* lastError_strDetails_out);
                         double pacevalLibrary_dGetComputationResult(void* handle_pacevalComputation_in, double values_in[],
                         double* trustedMinResult_out, double* trustedMaxResult_out);
                         bool pacevalLibrary_DeleteComputation(void* handle_pacevalComputation_in);
                         ",
                         "/usr/bin/libpaceval_linux_sharedLIB.so");

if ($numberOfVariables > 0)
{
    $valuesVariablesArray = FFI::new("double[$numberOfVariables]");
    for($iCount = 0; $iCount < $numberOfVariables; $iCount = $iCount + 1)
    {
        $valuesVariablesArray[$iCount] = $values_ar[$iCount];
    }
}
else
    $valuesVariablesArray = null;

if ($call_str == "paceval")
{
    $trustedMinResult = FFI::new("double");
    $trustedMaxResult = FFI::new("double");
    $result = FFI::new("double");
    $errorType = FFI::new("int");

    $success = (bool) $paceval_ffi->pacevalLibrary_Initialize(null);

    $timeCreate = microtime(true);
    $handle_pacevalComputation = $paceval_ffi->pacevalLibrary_CreateComputation($function_str, $numberOfVariables, $variables_str, $interval, null);
    $timeCreate = microtime(true) - $timeCreate;

    $timeCalculate = microtime(true);
    $result = $paceval_ffi->pacevalLibrary_dGetComputationResult($handle_pacevalComputation, $valuesVariablesArray,
              FFI::addr($trustedMinResult), FFI::addr($trustedMaxResult));
    $timeCalculate = microtime(true) - $timeCalculate;
    $return_arr["result"] = $result;

    if ($interval == true)
    {
        $return_arr["interval-min-result"] = $trustedMinResult->cdata;
        $return_arr["interval-max-result"] = $trustedMaxResult->cdata;
    }

    $functionLength = strlen($function_str);
    $function10chars = substr($function_str, 0, 10);
    if ($functionLength > 10)
    {
        $function10chars = $function10chars . "(...)";
    }
    $return_arr["function-10chars"] = $function10chars;
    $return_arr["function-length"] = $functionLength;

    $maxLengthStr = $paceval_ffi->pacevalLibrary_CreateErrorInformationText($handle_pacevalComputation, null, null);
    $errorMessage_str = FFI::new("char[$maxLengthStr]");
    $errorDetails_str = FFI::new("char[$maxLengthStr]");
    $maxLengthStr = $paceval_ffi->pacevalLibrary_CreateErrorInformationText($handle_pacevalComputation,
                    FFI::addr($errorMessage_str[0]), FFI::addr($errorDetails_str[0]));
    $errorMessage = FFI::string($errorMessage_str);
    $errorDetails = FFI::string($errorDetails_str);

    $return_arr["error-type"] = $errorType->cdata . " " . $errorDetails;
    $threadUsages = $paceval_ffi->pacevalLibrary_dmathv(null, FFI::addr($errorType), "paceval_NumberThreadUsages", 0, "", null);
    $return_arr["number-of-thread-usages"] = $threadUsages;
    $cacheHitsACC = $paceval_ffi->pacevalLibrary_dmathv(null, FFI::addr($errorType), "paceval_NumberCacheHitsACC", 0, "", null);
    $return_arr["number-of-cache-hits"] = $cacheHitsACC;
    $return_arr["time-create"] = number_format($timeCreate, 6, ".", ",") . "s";
    $return_arr["time-calculate"] = number_format($timeCalculate, 6, ".", ",") . "s";
    $return_arr["error-message"] = $errorMessage;
    $handle_pacevalComputation_ret = FFI::cast("unsigned long", $handle_pacevalComputation);
    $return_arr["handle-pacevalComputation"] = $handle_pacevalComputation_ret->cdata;

    echo json_encode($return_arr);

    $success = (bool)$paceval_ffi->pacevalLibrary_DeleteComputation($handle_pacevalComputation);
    $success = (bool)$paceval_ffi->pacevalLibrary_Free();
}
else
{
    echo "EXAMPLE</br>";
    echo "[1] standard: <a href='https://paceval-service.com/?call=paceval&functionString=-sin(x*cos(x))^(1/y)&numberOfVariables=2&variables=x;y&values=0.5;2&interval=no'>https://<b>paceval-service.com</b>/?<b>call</b>=paceval&<b>functionString</b>=-sin(x*cos(x))^(1/y)&<b>numberOfVariables</b>=2&<b>variables</b>=x;y&<b>values</b>=0.5;2&<b>interval</b>=no</a></br>";
    echo "[2] interval: <a href='https://paceval-service.com/?call=paceval&functionString=-sin(x*cos(x))^(1/y)&numberOfVariables=2&variables=x;y&values=0.5;2&interval=yes'>https://<b>paceval-service.com</b>/?<b>call</b>=paceval&<b>functionString</b>=-sin(x*cos(x))^(1/y)&<b>numberOfVariables</b>=2&<b>variables</b>=x;y&<b>values</b>=0.5;2&<b>interval</b>=yes</a></br>";
    echo "[3] cURL: <b>curl -d</b> \"call=paceval&functionString=-sin(x*cos(x))^(1/y)&numberOfVariables=2&variables=x;y&values=0.5;2&interval=no\" <b>-X POST</b> <a href='https://paceval-service.com/'>https://<b>paceval-service.com</b>/</a></br>";
    echo "REFERENCE</br>";
    echo "[4] paceval.: <a href='https://paceval.com/product-brief/'>https://<b>paceval</b>.com/product-brief/</a></br>";
}
?>