<?php

// PHP example 1

$paceval_ffi = FFI::cdef("
     bool pacevalLibrary_Initialize(const char* initString_in);
     bool pacevalLibrary_Free();
     void* pacevalLibrary_CreateComputation(const char* functionString_in, unsigned long numberOfVariables_in,
     const char* variables_in, bool useInterval_in, void* paceval_callbackStatus_in);
     double pacevalLibrary_dGetComputationResult(void* handle_pacevalComputation_in, double values_in[],
     double* trustedMinResult_out, double* trustedMaxResult_out);
     bool pacevalLibrary_DeleteComputation(void* handle_pacevalComputation_in);
     ",
     "/usr/bin/libpacevalARM64_sharedLIB.so"); // you can exchange the ARM64-library, e.g. to the x64-library

// call paceval-library functions to create a computation-object in memory, run a computation
// with trusted intervals and delete the computation-object from memory when we are done
$success = (bool) $paceval_ffi->pacevalLibrary_Initialize(null);

$valuesVariablesArray = FFI::new("double[2]");
$valuesVariablesArray[0] = 0.5;
$valuesVariablesArray[1] = 2.0;
$trustedMinResult = FFI::new("double");
$trustedMaxResult = FFI::new("double");

$handle_pacevalComputation = $paceval_ffi->pacevalLibrary_CreateComputation("-sin(x*cos(x))^(1/y)", 2, "x y", true, null);

$result = $paceval_ffi->pacevalLibrary_dGetComputationResult($handle_pacevalComputation, $valuesVariablesArray,
     FFI::addr($trustedMinResult), FFI::addr($trustedMaxResult));
var_dump($result); //-0.65180178245228
var_dump($trustedMinResult); //-0.65180178245231
var_dump($trustedMaxResult); //-0.65180178245225

$success = (bool) $paceval_ffi->pacevalLibrary_DeleteComputation($handle_pacevalComputation);
$success = (bool) $paceval_ffi->pacevalLibrary_Free();
?>