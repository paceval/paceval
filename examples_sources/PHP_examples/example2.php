<?php

// PHP example 2

$paceval_ffi = FFI::cdef("
     bool pacevalLibrary_Initialize(const char* initString_in);
     bool pacevalLibrary_Free();
     void* pacevalLibrary_CreateComputation(const char* functionString_in,
     unsigned long numberOfVariables_in, const char* variables_in, bool useInterval_in, void* paceval_callbackStatus_in);
     bool pacevalLibrary_dGetComputationResultExt(void* handle_pacevalComputation_in, double values_in[],
     unsigned long numberOfCalculations_in, double* results_out, double* trustedMinResults_out,
     double* trustedMaxResults_out, int* errorTypes_out);
     double pacevalLibrary_dmathv(void* handle_pacevalComputation_out_in, int *errorType_out,
     const char* functionString_in, unsigned long numberOfVariables_in, const char* variables_in, double values_in[]);
     bool pacevalLibrary_DeleteComputation(void* handle_pacevalComputation_in);
     ",
     "/usr/bin/libpacevalARM64_sharedLIB.so");

// call paceval-library functions to create a computation-object in memory,
// run 1.000.000 computations for x in [-10, 10] and y set to 0.5 without trusted interval computing
// finally delete the computation-object from memory
$success = (bool) $paceval_ffi->pacevalLibrary_Initialize(null);

$valuesVariablesArrayExt = FFI::new("double[1000000 * 2]");
$results = FFI::new("double[1000000]");
$errorTypes = FFI::new("int[1000000]");
$delta_x = 20.0/1000000;
$errorType = FFI::new("int");

$handle_pacevalComputation = $paceval_ffi->pacevalLibrary_CreateComputation("(sin(x)*cos(y)*x*y)+(x/((x^2+y^2)))", 2, "x y", false, null);

for($iCount = 0; $iCount < 1000000; $iCount = $iCount + 1)
{
     $valuesVariablesArrayExt[$iCount*2] = -10 + $delta_x * $iCount;
     $valuesVariablesArrayExt[$iCount*2 + 1] = 0.5;
}

$hasError = $paceval_ffi->pacevalLibrary_dGetComputationResultExt($handle_pacevalComputation,
$valuesVariablesArrayExt, 1000000, FFI::addr($results[0]), null, null, FFI::addr($errorTypes[0]));
var_dump($results[0]); //-2.4868678245251
var_dump($results[300000]); //-1.5744671915086
var_dump($results[700000]); //-1.0821594992009
var_dump($results[999999]); //-2.287287969116

$success = (bool) $paceval_ffi->pacevalLibrary_DeleteComputation($handle_pacevalComputation);

$threadUsages = $paceval_ffi->pacevalLibrary_dmathv(null, FFI::addr($errorType), "paceval_NumberThreadUsages", 0, "", null);
var_dump($threadUsages); //e.g. 12 threads

$success = (bool) $paceval_ffi->pacevalLibrary_Free();
?>