//---------------------------------------------------------------------------
// Copyright ©1994-2024. Version 1.x, 2.x, 3.x, 4.x ©1994-2024
//       Joerg Koenning & paceval.[Registered Trade Mark] All rights reserved.
// Author(s) : paceval., see http://www.paceval.com
// File      : paceval_main.h
// License   : paceval source code GNU Affero General Public License (AGPL)
//---------------------------------------------------------------------------

/**
 * @file paceval_main.h
 * @brief the paceval. application programming interface - for documentation please go to https://paceval.com/api/
 */
//---------------------------------------------------------------------------
#ifndef paceval_mainH
#define paceval_mainH

#define paceval_mainVersionString   "4"
#define paceval_subVersionString    "25"

#define PACEVAL_MAXVER	255
#define PACEVAL_MAXERR	255
#define PACEVAL_HANDLE	void*

#if !defined(paceval_use_dll)
#if (defined(_MSC_VER) || defined(_WIN64) || defined(__BORLANDC__)) && !(defined(WINAPI_FAMILY) && WINAPI_FAMILY == WINAPI_FAMILY_PHONE_APP)
#define paceval_use_dll	            1
#else
#define paceval_use_dll	            0
#endif //#if defined(_MSC_VER) || defined(__BORLANDC__)
#endif //defined(paceval_use_dll)

#if defined(WINDOWS_UWP)
#define paceval_use_dll	            0
#endif
//---------------------------------------------------------------------------

#ifdef __cplusplus
extern "C" {
#endif

enum paceval_eErrorTypes
{
    PACEVAL_ERR_NO_ERROR = 0,
    PACEVAL_ERR_CREATION_NO_ERROR_BUT_BUSY = 1,
    PACEVAL_ERR_CREATION_OUT_OF_MEMORY = 5,
    PACEVAL_ERR_BEGIN,
    PACEVAL_ERR_FATAL_BEGIN,
    PACEVAL_ERR_FATAL_INITIALIZE_LIBRARY_NOT_CALLED = 10,
    PACEVAL_ERR_FATAL_NO_LICENSE = 11,
    PACEVAL_ERR_FATAL_CONNECTING_SERVER = 15,  //This is a placeholder for the error codes when using an external library, e.g. like curl
    PACEVAL_ERR_FATAL_PARAMETERS_SERVER = 16,  //This is a placeholder for the error codes when using an external library, e.g. like curl
    PACEVAL_ERR_FATAL_END,
    PACEVAL_ERR_ANALYSIS_BEGIN,
    PACEVAL_ERR_ANALYSIS_UNKNOWN_SIGN_OR_FUNCTION = 110,
    PACEVAL_ERR_ANALYSIS_BRACKETS = 111,
    PACEVAL_ERR_ANALYSIS_UNKNOWN_CONSTANT_OR_VARIABLE = 112,
    PACEVAL_ERR_ANALYSIS_COMMENT = 113,
    PACEVAL_ERR_ANALYSIS_NUMBER_OF_VARIABLES = 114,
    PACEVAL_ERR_ANALYSIS_MISPLACED_SIGN_CALCULATION = 115,
    PACEVAL_ERR_ANALYSIS_UNEXPECTED_END = 116,
    PACEVAL_ERR_ANALYSIS_WRONGLY_USED_FUNCTION = 117,
    PACEVAL_ERR_ANALYSIS_NO_USER_FUNCTION = 118,
    PACEVAL_ERR_ANALYSIS_UNKNOWN_CHARACTER = 119,
    PACEVAL_ERR_ANALYSIS_WRONGLY_USED_CONSTANT_OR_VALUE = 120,
    PACEVAL_ERR_ANALYSIS_MISSING_OPERATOR = 121,
    PACEVAL_ERR_ANALYSIS_OUT_OF_MEMORY = 122,
    PACEVAL_ERR_ANALYSIS_UNKNOWN_OBJECT_TYPE = 124,
    PACEVAL_ERR_ANALYSIS_MEMORY_CLEANUP = 126,
    PACEVAL_ERR_ANALYSIS_USER_ABORT = 127,
    PACEVAL_ERR_ANALYSIS_MATH_OS_NOT_SUPPORTED = 128,
    PACEVAL_ERR_ANALYSIS_NO_COMMUNITY_FEATURE = 130,
    PACEVAL_ERR_ANALYSIS_END,
    PACEVAL_ERR_COMPUTATION_BEGIN,
    PACEVAL_ERR_COMPUTATION_HANDLE_INVALID = 140,
    PACEVAL_ERR_COMPUTATION_MULTIPLICATION = 141,
    PACEVAL_ERR_COMPUTATION_DIVISION = 142,
    PACEVAL_ERR_COMPUTATION_FUNCTION = 143,
    PACEVAL_ERR_COMPUTATION_ADDITION = 144,
    PACEVAL_ERR_COMPUTATION_SUBTRACTION = 145,
    PACEVAL_ERR_COMPUTATION_UNSPECIFIED = 150,
    PACEVAL_ERR_COMPUTATION_INTERVAL_RESULT = 151,
    PACEVAL_ERR_COMPUTATION_USER_ABORT = 152,
    PACEVAL_ERR_COMPUTATION_RESULT = 153,
    PACEVAL_ERR_COMPUTATION_BUSY = 154,
    PACEVAL_ERR_COMPUTATION_USER_COMPILER_NOT_SUPPORTS_LONG_DOUBLE = 160,
    PACEVAL_ERR_COMPUTATION_PRECHECK_MULTIPLE = 161,
    PACEVAL_ERR_COMPUTATION_END,
    PACEVAL_ERR_END
}; //paceval_eErrorTypes

enum paceval_eStatusTypes
{
    PACEVAL_STATUS_NO_STATUS = 0,
    PACEVAL_STATUS_ANALYSIS_PROGRESS = 1,
    PACEVAL_STATUS_ANALYSIS_ERROR = 2
}; //paceval_eStatusTypes

enum paceval_eCalculationPrecisionTypes
{
    PACEVAL_CALCULATION_PRECISION_NO_PRECISION = 0,
    PACEVAL_CALCULATION_PRECISION_FLOAT = 4,
    PACEVAL_CALCULATION_PRECISION_DOUBLE = 8,
    PACEVAL_CALCULATION_PRECISION_LONG_DOUBLE = 10
}; //paceval_eCalculationPrecisionTypes

typedef bool paceval_callbackStatusType(const PACEVAL_HANDLE,
                                        const paceval_eStatusTypes,
                                        const int);

typedef bool paceval_callbackUserFunctionType(const int,
        const long double*,
        long double*,
        const double*,
        double*,
        const float*,
        float*);


/**
 * Creates a paceval.-Computation object for a mathematical function and its variables. You can also set whether calculations should be carried out with or without interval arithmetic.
 * The return value is the HANDLE of the created paceval-Computation object. paceval_GetIsError() should be called to check whether an error has occurred. To get more information about the error, call paceval_GetErrorInformation().
 * Annotation: The reference HANDLE returned when calling paceval_CreateComputation() is a token that uniquely represents the paceval.-Computation object managed by the paceval.-library. This token can then be used to carry out calculations and queries on the paceval.-Computation object without having to re-pass the possibly very long function.
 * @param functionString_in Points to a null-terminated string to be used as the function to work with.
 * @param numberOfVariables_in Specifies the number of variables to work with. E.g. if the variables are "xValue yValue zValue" or "x y z" numberOfVariables_in must be set to 3.
 * @param variables_in Points to a null-terminated string specifying the names of the working variables. Generally the variables must be separated by a blank. E.g. the variables xValue, yValue, zValue must be set with "xValue yValue zValue" or the variables x, y, z must be set with "x y z".
 * @param useInterval_in Enables or disables the Trusted Interval Computation, TINC (paceval. specific) putting bounds on rounding errors and measurement errors of the computation system to yield reliable results.
 * @param paceval_callbackStatus_in A user-defined callback function to give status information of the paceval.-Computation object.
 *
 * see  https://paceval.com/api/#paceval_CreateComputation for more information
 */
PACEVAL_HANDLE paceval_CreateComputation(const char* functionString_in,
        unsigned long numberOfVariables_in,
        const char* variables_in,
        bool useInterval_in,
        paceval_callbackStatusType* paceval_callbackStatus_in);

/**
 * Creates paceval.-Computation objects for multiple mathematical functions and one set of variables in a single step. This is useful for a set of functions with the same number of variables and the same names for the variables (e.g. for Artificial neural network functions or Decison trees).
 * If the function succeeds, the return value is true and handle_pacevalComputations_out[] contains the paceval-Computation objects.
 * Annotation: paceval_CreateMultipleComputations() is also very useful in a Kubernetes cluster environment. It simplifies the creation and usage of all sets of paceval.-Computation objects on the same worker node (e.g. with paceval_dGetMultipleComputationsResults()).
 * @param handle_pacevalComputations_out If paceval_CreateMultipleComputations() is succesful this retrieves the array of HANDLE of the created paceval-Computation objects.
 * @param functionStrings_in Points to an array of null-terminated strings to be used as the functions to work with for the created paceval-Computation objects.
 * @param numberOfpacevalComputations_in Specifies the number of paceval-Computation objects to create. E.g. if the functions to work with are "sin(x)" and "cos(x)" numberOfpacevalComputations_in must be set to 2.
 * @param numberOfVariables_in Specifies the number of variables to work with. E.g. if the variables are "xValue yValue zValue" or "x y z" numberOfVariables_in must be set to 3.
 * @param variables_in Points to a null-terminated string specifying the names of the working variables. Generally the variables must be separated by a blank. E.g. the variables xValue, yValue, zValue must be set with "xValue yValue zValue" or the variables x, y, z must be set with "x y z".
 * @param useInterval_in Enables or disables the Trusted Interval Computation, TINC (paceval. specific) putting bounds on rounding errors and measurement errors of the computation system to yield reliable results.
 * @param paceval_callbackStatus_in A user-defined callback function to give status information of the paceval.-Computation objects.
 *
 * see  https://paceval.com/api/#paceval_CreateMultipleComputations for more information
 */
bool paceval_CreateMultipleComputations(PACEVAL_HANDLE handle_pacevalComputations_out[],
                                        const char* functionStrings_in[],
                                        unsigned long numberOfpacevalComputations_in,
                                        unsigned long numberOfVariables_in,
                                        const char* variables_in,
                                        bool useInterval_in,
                                        paceval_callbackStatusType* paceval_callbackStatus_in);

/**
 * Determines whether a particular paceval.-Computation object has been created.
 * If the object exists, the return value is true. If the specified HANDLE is invalid or the object does not exist, the return value is false.
 * @param handle_pacevalComputation_in Identifies the paceval.-Computation object to be questioned.
 *
 * see  https://paceval.com/api/#paceval_ExistComputation for more information
 */
bool paceval_ExistComputation(PACEVAL_HANDLE handle_pacevalComputation_in);

/**
 * Deletes a paceval.-Computation object.
 * If the function succeeds, the return value is true. If the given HANDLE is not valid the return value is false.
 * @param handle_pacevalComputation_in Identifies the paceval.-Computation object to delete.
 *
 * see  https://paceval.com/api/#paceval_DeleteComputation for more information
 */
bool paceval_DeleteComputation(PACEVAL_HANDLE handle_pacevalComputation_in);

/**
 * Converts a floating point number (long double) to a string.
 * If the function succeeds, the return value is >0 and gives the precision of the conversion. Otherwise the return value is <0.
 * @param destinationString_out Points to the buffer that will receive the string of the coverted floating point number. Annotation: In case of an error the buffer is not specified.
 * @param float_in The floating point number to convert.
 *
 * see  https://paceval.com/api/#paceval_dConvertFloatToString for more information
 */
int paceval_ldConvertFloatToString(char* destinationString_out,
                                   long double float_in);

/**
 * Converts a floating point number (double) to a string.
 * If the function succeeds, the return value is >0 and gives the precision of the conversion. Otherwise the return value is <0.
 * @param destinationString_out Points to the buffer that will receive the string of the coverted floating point number. Annotation: In case of an error the buffer is not specified.
 * @param float_in The floating point number to convert.
 *
 * see  https://paceval.com/api/#paceval_dConvertFloatToString for more information
 */
int paceval_dConvertFloatToString(char* destinationString_out,
                                  double float_in);

/**
 * Converts a floating point number (float) to a string.
 * If the function succeeds, the return value is >0 and gives the precision of the conversion. Otherwise the return value is <0.
 * @param destinationString_out Points to the buffer that will receive the string of the coverted floating point number. Annotation: In case of an error the buffer is not specified.
 * @param float_in The floating point number to convert.
 *
 * see  https://paceval.com/api/#paceval_dConvertFloatToString for more information
 */
int paceval_fConvertFloatToString(char* destinationString_out,
                                  float float_in);

/**
 * Converts a to a string to a floating point number (long double). In case a caluclation is given in the string the result is converted.
 * If the function succeeds, the return value is the result of the conversion. Annotation: In case of an error the return value is not specified.
 * @param sourceString_in The string to convert.
 * @param errorType_out Points to the buffer that will receive the paceval.-Computation object error, see also paceval_eErrorTypes in paceval_main.h or paceval_GetErrorInformation().
 * @param errPosition_out Position in the string where the error occurred.
 * @param useInterval_in Enables or disables the Trusted Interval Computation, TINC (paceval. specific) for the conversion.
 * @param trustedMinResult_out If Trusted Interval Computation was enabled this retrieves the minimum/lower interval limit of the conversion. Annotation: In case of an error the value is not specified.
 * @param trustedMaxResult_out If Trusted Interval Computation was enabled this retrieves the maximum/upper interval limit of the conversion. Annotation: In case of an error the value is not specified.
 *
 * see  https://paceval.com/api/#paceval_dConvertStringToFloat for more information
 */
long double paceval_ldConvertStringToFloat(const char* sourceString_in,
        int* errorType_out,
        long* errPosition_out,
        bool useInterval_in,
        long double* trustedMinResult_out,
        long double* trustedMaxResult_out);

/**
 * Converts a to a string to a floating point number (double). In case a caluclation is given in the string the result is converted.
 * If the function succeeds, the return value is the result of the conversion. Annotation: In case of an error the return value is not specified.
 * @param sourceString_in The string to convert.
 * @param errorType_out Points to the buffer that will receive the paceval.-Computation object error, see also paceval_eErrorTypes in paceval_main.h or paceval_GetErrorInformation().
 * @param errPosition_out Position in the string where the error occurred.
 * @param useInterval_in Enables or disables the Trusted Interval Computation, TINC (paceval. specific) for the conversion.
 * @param trustedMinResult_out If Trusted Interval Computation was enabled this retrieves the minimum/lower interval limit of the conversion. Annotation: In case of an error the value is not specified.
 * @param trustedMaxResult_out If Trusted Interval Computation was enabled this retrieves the maximum/upper interval limit of the conversion. Annotation: In case of an error the value is not specified.
 *
 * see  https://paceval.com/api/#paceval_dConvertStringToFloat for more information
 */
double paceval_dConvertStringToFloat(const char* sourceString_in,
                                     int* errorType_out,
                                     long* errPosition_out,
                                     bool useInterval_in,
                                     double* trustedMinResult_out,
                                     double* trustedMaxResult_out);

/**
 * Converts a to a string to a floating point number (float). In case a caluclation is given in the string the result is converted.
 * If the function succeeds, the return value is the result of the conversion. Annotation: In case of an error the return value is not specified.
 * @param sourceString_in The string to convert.
 * @param errorType_out Points to the buffer that will receive the paceval.-Computation object error, see also paceval_eErrorTypes in paceval_main.h or paceval_GetErrorInformation().
 * @param errPosition_out Position in the string where the error occurred.
 * @param useInterval_in Enables or disables the Trusted Interval Computation, TINC (paceval. specific) for the conversion.
 * @param trustedMinResult_out If Trusted Interval Computation was enabled this retrieves the minimum/lower interval limit of the conversion. Annotation: In case of an error the value is not specified.
 * @param trustedMaxResult_out If Trusted Interval Computation was enabled this retrieves the maximum/upper interval limit of the conversion. Annotation: In case of an error the value is not specified.
 *
 * see  https://paceval.com/api/#paceval_dConvertStringToFloat for more information
 */
float paceval_fConvertStringToFloat(const char* sourceString_in,
                                    int* errorType_out,
                                    long* errPosition_out,
                                    bool useInterval_in,
                                    float* trustedMinResult_out,
                                    float* trustedMaxResult_out);

/**
 * A convenience function to get results (long double) of computations in a single step.
 * If the function succeeds, the return value is the result of the computation. paceval_GetIsError() should be called to check whether an error has occurred. To get more information about the error, call paceval_GetErrorInformation(). Annotation: In case of an error the return value is not specified.
 * @param handle_pacevalComputation_out_in Pointer to a paceval.-Computation object. If handle_pacevalComputation_out_in is not NULL this buffer will retrieve the created paceval.-Computation object and can be used again. This will improve the performance. In this case the paceval.-Computation object will not be deleted and you must call paceval_DeleteComputation().
 * @param errorType_out Points to the buffer that will receive the paceval.-Computation object error, see also paceval_eErrorTypes in paceval_main.h or paceval_GetErrorInformation().
 * @param functionString_in Points to a null-terminated string to be used as the function to work with.
 * @param numberOfVariables_in Specifies the number of variables to work with. E.g. if the variables are "xValue yValue zValue" or "x y z" numberOfVariables_in must be set to 3.
 * @param variables_in Points to a null-terminated string specifying the names of the working variables. Generally the variables must be separated by a blank. E.g. the variables xValue, yValue, zValue must be set with "xValue yValue zValue" or the variables x, y, z must be set with "x y z".
 * @param ... Parameters comma seperated will be interpreted as long double values for the variables.
 *
 * see  https://paceval.com/api/#paceval_dmathv for more information
 */
long double paceval_ldmathv(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
                            int* errorType_out,
                            const char* functionString_in,
                            unsigned long numberOfVariables_in,
                            const char* variables_in, ...);

/**
 * A convenience function to get results (double) of computations in a single step.
 * If the function succeeds, the return value is the result of the computation. paceval_GetIsError() should be called to check whether an error has occurred. To get more information about the error, call paceval_GetErrorInformation(). Annotation: In case of an error the return value is not specified.
 * @param handle_pacevalComputation_out_in Pointer to a paceval.-Computation object. If handle_pacevalComputation_out_in is not NULL this buffer will retrieve the created paceval.-Computation object and can be used again. This will improve the performance. In this case the paceval.-Computation object will not be deleted and you must call paceval_DeleteComputation().
 * @param errorType_out Points to the buffer that will receive the paceval.-Computation object error, see also paceval_eErrorTypes in paceval_main.h or paceval_GetErrorInformation().
 * @param functionString_in Points to a null-terminated string to be used as the function to work with.
 * @param numberOfVariables_in Specifies the number of variables to work with. E.g. if the variables are "xValue yValue zValue" or "x y z" numberOfVariables_in must be set to 3.
 * @param variables_in Points to a null-terminated string specifying the names of the working variables. Generally the variables must be separated by a blank. E.g. the variables xValue, yValue, zValue must be set with "xValue yValue zValue" or the variables x, y, z must be set with "x y z".
 * @param ... Parameters comma seperated will be interpreted as double values for the variables.
 *
 * see  https://paceval.com/api/#paceval_dmathv for more information
 */
double paceval_dmathv(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
                      int* errorType_out,
                      const char* functionString_in,
                      unsigned long numberOfVariables_in,
                      const char* variables_in, ...);

/**
 * A convenience function to get results (float) of computations in a single step.
 * If the function succeeds, the return value is the result of the computation. paceval_GetIsError() should be called to check whether an error has occurred. To get more information about the error, call paceval_GetErrorInformation(). Annotation: In case of an error the return value is not specified.
 * @param handle_pacevalComputation_out_in Pointer to a paceval.-Computation object. If handle_pacevalComputation_out_in is not NULL this buffer will retrieve the created paceval.-Computation object and can be used again. This will improve the performance. In this case the paceval.-Computation object will not be deleted and you must call paceval_DeleteComputation().
 * @param errorType_out Points to the buffer that will receive the paceval.-Computation object error, see also paceval_eErrorTypes in paceval_main.h or paceval_GetErrorInformation().
 * @param functionString_in Points to a null-terminated string to be used as the function to work with.
 * @param numberOfVariables_in Specifies the number of variables to work with. E.g. if the variables are "xValue yValue zValue" or "x y z" numberOfVariables_in must be set to 3.
 * @param variables_in Points to a null-terminated string specifying the names of the working variables. Generally the variables must be separated by a blank. E.g. the variables xValue, yValue, zValue must be set with "xValue yValue zValue" or the variables x, y, z must be set with "x y z".
 * @param ... Parameters comma seperated will be interpreted as float values for the variables.
 *
 * see  https://paceval.com/api/#paceval_dmathv for more information
 */
float paceval_fmathv(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
                     int* errorType_out,
                     const char* functionString_in,
                     unsigned long numberOfVariables_in,
                     const char* variables_in, ...);

/**
 * A convenience function to get results (long double) of computations in a single step with Trusted Interval Computation, TINC (paceval. specific).
 * If the function succeeds, the return value is the result of the computation. paceval_GetIsError() should be called to check whether an error has occurred. To get more information about the error, call paceval_GetErrorInformation(). Annotation: In case of an error the return value is not specified.
 * @param handle_pacevalComputation_out_in Pointer to a paceval.-Computation object. If handle_pacevalComputation_out_in is not NULL this buffer will retrieve the created paceval.-Computation object and can be used again. This will improve the performance. In this case the paceval.-Computation object will not be deleted and you must call paceval_DeleteComputation().
 * @param errorType_out Points to the buffer that will receive the paceval.-Computation object error, see also paceval_eErrorTypes in paceval_main.h or paceval_GetErrorInformation().
 * @param trustedMinResult_out This buffer retrieves the minimum/lower interval limit of the computation. Annotation: In case of an error the value is not specified.
 * @param trustedMaxResult_out This buffer retrieves the maximum/upper interval limit of the computation. Annotation: In case of an error the value is not specified.
 * @param functionString_in Points to a null-terminated string to be used as the function to work with.
 * @param numberOfVariables_in Specifies the number of variables to work with. E.g. if the variables are "xValue yValue zValue" or "x y z" numberOfVariables_in must be set to 3.
 * @param variables_in Points to a null-terminated string specifying the names of the working variables. Generally the variables must be separated by a blank. E.g. the variables xValue, yValue, zValue must be set with "xValue yValue zValue" or the variables x, y, z must be set with "x y z".
 * @param ... Parameters comma seperated will be interpreted as long double values for the variables.
 *
 * see  https://paceval.com/api/#paceval_dmathvi for more information
 */
long double paceval_ldmathvi(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
                             int* errorType_out,
                             long double* trustedMinResult_out,
                             long double* trustedMaxResult_out,
                             const char* functionString_in,
                             unsigned long numberOfVariables_in,
                             const char* variables_in, ...);

/**
 * A convenience function to get results (double) of computations in a single step with Trusted Interval Computation, TINC (paceval. specific).
 * If the function succeeds, the return value is the result of the computation. paceval_GetIsError() should be called to check whether an error has occurred. To get more information about the error, call paceval_GetErrorInformation(). Annotation: In case of an error the return value is not specified.
 * @param handle_pacevalComputation_out_in Pointer to a paceval.-Computation object. If handle_pacevalComputation_out_in is not NULL this buffer will retrieve the created paceval.-Computation object and can be used again. This will improve the performance. In this case the paceval.-Computation object will not be deleted and you must call paceval_DeleteComputation().
 * @param errorType_out Points to the buffer that will receive the paceval.-Computation object error, see also paceval_eErrorTypes in paceval_main.h or paceval_GetErrorInformation().
 * @param trustedMinResult_out This buffer retrieves the minimum/lower interval limit of the computation. Annotation: In case of an error the value is not specified.
 * @param trustedMaxResult_out This buffer retrieves the maximum/upper interval limit of the computation. Annotation: In case of an error the value is not specified.
 * @param functionString_in Points to a null-terminated string to be used as the function to work with.
 * @param numberOfVariables_in Specifies the number of variables to work with. E.g. if the variables are "xValue yValue zValue" or "x y z" numberOfVariables_in must be set to 3.
 * @param variables_in Points to a null-terminated string specifying the names of the working variables. Generally the variables must be separated by a blank. E.g. the variables xValue, yValue, zValue must be set with "xValue yValue zValue" or the variables x, y, z must be set with "x y z".
 * @param ... Parameters comma seperated will be interpreted as double values for the variables.
 *
 * see  https://paceval.com/api/#paceval_dmathvi for more information
 */
double paceval_dmathvi(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
                       int* errorType_out,
                       double* trustedMinResult_out,
                       double* trustedMaxResult_out,
                       const char* functionString_in,
                       unsigned long numberOfVariables_in,
                       const char* variables_in, ...);

/**
 * A convenience function to get results (float) of computations in a single step with Trusted Interval Computation, TINC (paceval. specific).
 * If the function succeeds, the return value is the result of the computation. paceval_GetIsError() should be called to check whether an error has occurred. To get more information about the error, call paceval_GetErrorInformation(). Annotation: In case of an error the return value is not specified.
 * @param handle_pacevalComputation_out_in Pointer to a paceval.-Computation object. If handle_pacevalComputation_out_in is not NULL this buffer will retrieve the created paceval.-Computation object and can be used again. This will improve the performance. In this case the paceval.-Computation object will not be deleted and you must call paceval_DeleteComputation().
 * @param errorType_out Points to the buffer that will receive the paceval.-Computation object error, see also paceval_eErrorTypes in paceval_main.h or paceval_GetErrorInformation().
 * @param trustedMinResult_out This buffer retrieves the minimum/lower interval limit of the computation. Annotation: In case of an error the value is not specified.
 * @param trustedMaxResult_out This buffer retrieves the maximum/upper interval limit of the computation. Annotation: In case of an error the value is not specified.
 * @param functionString_in Points to a null-terminated string to be used as the function to work with.
 * @param numberOfVariables_in Specifies the number of variables to work with. E.g. if the variables are "xValue yValue zValue" or "x y z" numberOfVariables_in must be set to 3.
 * @param variables_in Points to a null-terminated string specifying the names of the working variables. Generally the variables must be separated by a blank. E.g. the variables xValue, yValue, zValue must be set with "xValue yValue zValue" or the variables x, y, z must be set with "x y z".
 * @param ... Parameters comma seperated will be interpreted as float values for the variables.
 *
 * see  https://paceval.com/api/#paceval_dmathvi for more information
 */
float paceval_fmathvi(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
                      int* errorType_out,
                      float* trustedMinResult_out,
                      float* trustedMaxResult_out,
                      const char* functionString_in,
                      unsigned long numberOfVariables_in,
                      const char* variables_in, ...);

/**
 * Performs a calculation (long double) on a paceval.-Computation object with the variables declared by paceval_CreateComputation() and with a set of values for those variables.
 * If the function succeeds, the return value is the result of the computation. paceval_GetIsError() should be called to check whether an error has occurred. To get more information about the error, call paceval_GetErrorInformation(). Annotation: In case of an error the return value is not specified.
 * @param handle_pacevalComputation_in Identifies the paceval.-Computation object.
 * @param values_in Array of long double defining the values of the variables.
 * @param trustedMinResult_out This buffer retrieves the minimum/lower interval limit of the computation. Annotation: In case of an error the value is not specified.
 * @param trustedMaxResult_out This buffer retrieves the maximum/upper interval limit of the computation. Annotation: In case of an error the value is not specified.
 *
 * see  https://paceval.com/api/#paceval_GetComputationResult for more information
 */
long double paceval_ldGetComputationResult(PACEVAL_HANDLE handle_pacevalComputation_in,
        long double values_in[],
        long double* trustedMinResult_out,
        long double* trustedMaxResult_out);

/**
 * Performs a calculation (double) on a paceval.-Computation object with the variables declared by paceval_CreateComputation() and with a set of values for those variables.
 * If the function succeeds, the return value is the result of the computation. paceval_GetIsError() should be called to check whether an error has occurred. To get more information about the error, call paceval_GetErrorInformation(). Annotation: In case of an error the return value is not specified.
 * @param handle_pacevalComputation_in Identifies the paceval.-Computation object.
 * @param values_in Array of double defining the values of the variables.
 * @param trustedMinResult_out This buffer retrieves the minimum/lower interval limit of the computation. Annotation: In case of an error the value is not specified.
 * @param trustedMaxResult_out This buffer retrieves the maximum/upper interval limit of the computation. Annotation: In case of an error the value is not specified.
 *
 * see  https://paceval.com/api/#paceval_GetComputationResult for more information
 */
double paceval_dGetComputationResult(PACEVAL_HANDLE handle_pacevalComputation_in,
                                     double values_in[],
                                     double* trustedMinResult_out,
                                     double* trustedMaxResult_out);

/**
 * Performs a calculation (float) on a paceval.-Computation object with the variables declared by paceval_CreateComputation() and with a set of values for those variables.
 * If the function succeeds, the return value is the result of the computation. paceval_GetIsError() should be called to check whether an error has occurred. To get more information about the error, call paceval_GetErrorInformation(). Annotation: In case of an error the return value is not specified.
 * @param handle_pacevalComputation_in Identifies the paceval.-Computation object.
 * @param values_in Array of float defining the values of the variables.
 * @param trustedMinResult_out This buffer retrieves the minimum/lower interval limit of the computation. Annotation: In case of an error the value is not specified.
 * @param trustedMaxResult_out This buffer retrieves the maximum/upper interval limit of the computation. Annotation: In case of an error the value is not specified.
 *
 * see  https://paceval.com/api/#paceval_GetComputationResult for more information
 */
float paceval_fGetComputationResult(PACEVAL_HANDLE handle_pacevalComputation_in,
                                    float values_in[],
                                    float* trustedMinResult_out,
                                    float* trustedMaxResult_out);

/**
 * Performs multiple calculations (long double) in parallel on a single paceval.-Computation object with the variables declared by paceval_CreateComputation() and with multiple sets of values for those variables. You should use paceval_dGetComputationResultExt() to get many results for a single computaton at once. This is useful for example when you plot 2D- or 3D-functions and graphics very fast.
 * The return value indicates paceval.-Computation object errors. You should check the array errorTypes_out in this case.
 * @param handle_pacevalComputation_in Identifies the paceval.-Computation object.
 * @param values_in Array of long double defining the multiple values of the variables.
 * @param numberOfCalculations_in Specifies the number of different calculations you want to run. This number specifies the size of the array values_in[]. E.g. if the number of variables declared is 50 and the number of calculations is 1000 the size of the array values_in[] must be 50*1000. The order of the array values_in[] must be variable values for the first calculation, then variable values for the second calculation and so on.
 * @param results_out Pointer to an array for the results of the computation with the multiple values of the variables. Annotation: In case of an error the values are not specified.
 * @param trustedMinResults_out Pointer to an array for the minimum/lower interval limits. Annotation: In case of an error the values are not specified.
 * @param trustedMaxResults_out Pointer to an array for the maximum/upper interval limits. Annotation: In case of an error the values are not specified.
 * @param errorTypes_out Pointer to an array of the paceval.-Computation object errors, see also paceval_eErrorTypes in paceval_main.h or paceval_GetErrorInformation().
 *
 * see  https://paceval.com/api/#paceval_dGetComputationResultExt for more information
 */
bool paceval_ldGetComputationResultExt(PACEVAL_HANDLE handle_pacevalComputation_in,
                                       long double values_in[],
                                       unsigned long numberOfCalculations_in,
                                       long double* results_out,
                                       long double* trustedMinResults_out,
                                       long double* trustedMaxResults_out,
                                       int* errorTypes_out);

/**
 * Performs multiple calculations (double) in parallel on a single paceval.-Computation object with the variables declared by paceval_CreateComputation() and with multiple sets of values for those variables. You should use paceval_dGetComputationResultExt() to get many results for a single computaton at once. This is useful for example when you plot 2D- or 3D-functions and graphics very fast.
 * The return value indicates paceval.-Computation object errors. You should check the array errorTypes_out in this case.
 * @param handle_pacevalComputation_in Identifies the paceval.-Computation object.
 * @param values_in Array of double defining the multiple values of the variables.
 * @param numberOfCalculations_in Specifies the number of different calculations you want to run. This number specifies the size of the array values_in[]. E.g. if the number of variables declared is 50 and the number of calculations is 1000 the size of the array values_in[] must be 50*1000. The order of the array values_in[] must be variable values for the first calculation, then variable values for the second calculation and so on.
 * @param results_out Pointer to an array for the results of the computation with the multiple values of the variables. Annotation: In case of an error the values are not specified.
 * @param trustedMinResults_out Pointer to an array for the minimum/lower interval limits. Annotation: In case of an error the values are not specified.
 * @param trustedMaxResults_out Pointer to an array for the maximum/upper interval limits. Annotation: In case of an error the values are not specified.
 * @param errorTypes_out Pointer to an array of the paceval.-Computation object errors, see also paceval_eErrorTypes in paceval_main.h or paceval_GetErrorInformation().
 *
 * see  https://paceval.com/api/#paceval_dGetComputationResultExt for more information
 */
bool paceval_dGetComputationResultExt(PACEVAL_HANDLE handle_pacevalComputation_in,
                                      double values_in[],
                                      unsigned long numberOfCalculations_in,
                                      double* results_out,
                                      double* trustedMinResults_out,
                                      double* trustedMaxResults_out,
                                      int* errorTypes_out);

/**
 * Performs multiple calculations (float) in parallel on a single paceval.-Computation object with the variables declared by paceval_CreateComputation() and with multiple sets of values for those variables. You should use paceval_dGetComputationResultExt() to get many results for a single computaton at once. This is useful for example when you plot 2D- or 3D-functions and graphics very fast.
 * The return value indicates paceval.-Computation object errors. You should check the array errorTypes_out in this case.
 * @param handle_pacevalComputation_in Identifies the paceval.-Computation object.
 * @param values_in Array of float defining the multiple values of the variables.
 * @param numberOfCalculations_in Specifies the number of different calculations you want to run. This number specifies the size of the array values_in[]. E.g. if the number of variables declared is 50 and the number of calculations is 1000 the size of the array values_in[] must be 50*1000. The order of the array values_in[] must be variable values for the first calculation, then variable values for the second calculation and so on.
 * @param results_out Pointer to an array for the results of the computation with the multiple values of the variables. Annotation: In case of an error the values are not specified.
 * @param trustedMinResults_out Pointer to an array for the minimum/lower interval limits. Annotation: In case of an error the values are not specified.
 * @param trustedMaxResults_out Pointer to an array for the maximum/upper interval limits. Annotation: In case of an error the values are not specified.
 * @param errorTypes_out Pointer to an array of the paceval.-Computation object errors, see also paceval_eErrorTypes in paceval_main.h or paceval_GetErrorInformation().
 *
 * see  https://paceval.com/api/#paceval_dGetComputationResultExt for more information
 */
bool paceval_fGetComputationResultExt(PACEVAL_HANDLE handle_pacevalComputation_in,
                                      float values_in[],
                                      unsigned long numberOfCalculations_in,
                                      float* results_out,
                                      float* trustedMinResults_out,
                                      float* trustedMaxResults_out,
                                      int* errorTypes_out);

/**
 * Performs multiple calculations (long double) in parallel on multiple paceval.-Computation objects using the variables declared by paceval_CreateComputation() and with the same set of values for these variables. You should use paceval_dGetMultipleComputationsResults() to get results for multiple computations at once (e.g. for Artificial neural network functions or Decision trees). Annotation: You must use the same number of variables and the same declared variables. To do so you can simply declare all variables in each of the the calls for paceval_CreateComputation(). There is no performance issue in case a variable is declared but not used by a paceval.-Computation object.
 * The return value indicates paceval.-Computation object errors. You should check the array errorTypes_out in this case.
 * @param handle_pacevalComputations_in Array of the paceval.-Computation objects.
 * @param numberOfpacevalComputations_in Specifies the number of the paceval.-Computation objects.
 * @param values_in Array of long double defining the values of the variables.
 * @param results_out Pointer to an array for the results of the multiple computations. Annotation: In case of an error the values are not specified.
 * @param trustedMinResults_out Pointer to an array for the minimum/lower interval limits. Annotation: In case of an error the values are not specified.
 * @param trustedMaxResults_out Pointer to an array for the maximum/upper interval limits. Annotation: In case of an error the value is not specified.
 * @param errorTypes_out Pointer to an array of the paceval.-Computation object errors, see also paceval_eErrorTypes in paceval_main.h or paceval_GetErrorInformation().
 *
 * see  https://paceval.com/api/#paceval_dGetMultipleComputationsResults for more information
 */
bool paceval_ldGetMultipleComputationsResults(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        long double values_in[],
        long double* results_out,
        long double* trustedMinResults_out,
        long double* trustedMaxResults_out,
        int* errorTypes_out);

/**
 * Performs multiple calculations (double) in parallel on multiple paceval.-Computation objects using the variables declared by paceval_CreateComputation() and with the same set of values for these variables. You should use paceval_dGetMultipleComputationsResults() to get results for multiple computations at once (e.g. for Artificial neural network functions or Decision trees). Annotation: You must use the same number of variables and the same declared variables. To do so you can simply declare all variables in each of the the calls for paceval_CreateComputation(). There is no performance issue in case a variable is declared but not used by a paceval.-Computation object.
 * The return value indicates paceval.-Computation object errors. You should check the array errorTypes_out in this case.
 * @param handle_pacevalComputations_in Array of the paceval.-Computation objects.
 * @param numberOfpacevalComputations_in Specifies the number of the paceval.-Computation objects.
 * @param values_in Array of double defining the values of the variables.
 * @param results_out Pointer to an array for the results of the multiple computations. Annotation: In case of an error the values are not specified.
 * @param trustedMinResults_out Pointer to an array for the minimum/lower interval limits. Annotation: In case of an error the values are not specified.
 * @param trustedMaxResults_out Pointer to an array for the maximum/upper interval limits. Annotation: In case of an error the value is not specified.
 * @param errorTypes_out Pointer to an array of the paceval.-Computation object errors, see also paceval_eErrorTypes in paceval_main.h or paceval_GetErrorInformation().
 *
 * see  https://paceval.com/api/#paceval_dGetMultipleComputationsResults for more information
 */
bool paceval_dGetMultipleComputationsResults(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        double values_in[],
        double* results_out,
        double* trustedMinResults_out,
        double* trustedMaxResults_out,
        int* errorTypes_out);

/**
 * Performs multiple calculations (float) in parallel on multiple paceval.-Computation objects using the variables declared by paceval_CreateComputation() and with the same set of values for these variables. You should use paceval_dGetMultipleComputationsResults() to get results for multiple computations at once (e.g. for Artificial neural network functions or Decision trees). Annotation: You must use the same number of variables and the same declared variables. To do so you can simply declare all variables in each of the the calls for paceval_CreateComputation(). There is no performance issue in case a variable is declared but not used by a paceval.-Computation object.
 * The return value indicates paceval.-Computation object errors. You should check the array errorTypes_out in this case.
 * @param handle_pacevalComputations_in Array of the paceval.-Computation objects.
 * @param numberOfpacevalComputations_in Specifies the number of the paceval.-Computation objects.
 * @param values_in Array of float defining the values of the variables.
 * @param results_out Pointer to an array for the results of the multiple computations. Annotation: In case of an error the values are not specified.
 * @param trustedMinResults_out Pointer to an array for the minimum/lower interval limits. Annotation: In case of an error the values are not specified.
 * @param trustedMaxResults_out Pointer to an array for the maximum/upper interval limits. Annotation: In case of an error the value is not specified.
 * @param errorTypes_out Pointer to an array of the paceval.-Computation object errors, see also paceval_eErrorTypes in paceval_main.h or paceval_GetErrorInformation().
 *
 * see  https://paceval.com/api/#paceval_dGetMultipleComputationsResults for more information
 */
bool paceval_fGetMultipleComputationsResults(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        float values_in[],
        float* results_out,
        float* trustedMinResults_out,
        float* trustedMaxResults_out,
        int* errorTypes_out);

/**
 * Performs multiple calculations (long double) in parallel on multiple paceval.-Computation objects using the variables declared by paceval_CreateComputation() and with multiple sets of values for those variables. You should use paceval_dGetMultipleComputationsResultsExt() to get results for multiple computations at the same time and to carry out as many different evaluations as possible at once (e.g. for artificial neural network functions or decision trees in which several functions with different variable values are calculated in one step for several objects at the same time to decide). Annotation: You must use the same number of variables and the same declared variables. To do so you can simply declare all variables in each of the the calls for paceval_CreateComputation(). There is no performance issue in case a variable is declared but not used by a paceval.-Computation object.
 * The return value indicates paceval.-Computation object errors. You should check the array errorTypes_out in this case.
 * @param handle_pacevalComputations_in Array of the paceval.-Computation objects.
 * @param numberOfpacevalComputations_in Specifies the number of the paceval.-Computation objects.
 * @param values_in Array of long double defining the values of the variables.
 * @param numberOfCalculations_in Specifies the number of different calculations you want to run. This number specifies the size of the array values_in[]. E.g. if the number of variables declared is 50 and the number of calculations is 1000 the size of the array values_in[] must be 50*1000. The order of the array values_in[] must be variable values for the first calculation, then variable values for the second calculation and so on.
 * @param results_out Pointer to an array for the results of the multiple computations. Annotation: In case of an error the values are not specified.
 * @param trustedMinResults_out Pointer to an array for the minimum/lower interval limits. Annotation: In case of an error the values are not specified.
 * @param trustedMaxResults_out Pointer to an array for the maximum/upper interval limits. Annotation: In case of an error the value is not specified.
 * @param errorTypes_out Pointer to an array of the paceval.-Computation object errors, see also paceval_eErrorTypes in paceval_main.h or paceval_GetErrorInformation().
 *
 * see  https://paceval.com/api/#paceval_dGetMultipleComputationsResultsExt for more information
 */
bool paceval_ldGetMultipleComputationsResultsExt(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        long double values_in[],
        unsigned long numberOfCalculations_in,
        long double* results_out,
        long double* trustedMinResults_out,
        long double* trustedMaxResults_out,
        int* errorTypes_out);

/**
 * Performs multiple calculations (double) in parallel on multiple paceval.-Computation objects using the variables declared by paceval_CreateComputation() and with multiple sets of values for those variables. You should use paceval_dGetMultipleComputationsResultsExt() to get results for multiple computations at the same time and to carry out as many different evaluations as possible at once (e.g. for artificial neural network functions or decision trees in which several functions with different variable values are calculated in one step for several objects at the same time to decide). Annotation: You must use the same number of variables and the same declared variables. To do so you can simply declare all variables in each of the the calls for paceval_CreateComputation(). There is no performance issue in case a variable is declared but not used by a paceval.-Computation object.
 * The return value indicates paceval.-Computation object errors. You should check the array errorTypes_out in this case.
 * @param handle_pacevalComputations_in Array of the paceval.-Computation objects.
 * @param numberOfpacevalComputations_in Specifies the number of the paceval.-Computation objects.
 * @param values_in Array of double defining the values of the variables.
 * @param numberOfCalculations_in Specifies the number of different calculations you want to run. This number specifies the size of the array values_in[]. E.g. if the number of variables declared is 50 and the number of calculations is 1000 the size of the array values_in[] must be 50*1000. The order of the array values_in[] must be variable values for the first calculation, then variable values for the second calculation and so on.
 * @param results_out Pointer to an array for the results of the multiple computations. Annotation: In case of an error the values are not specified.
 * @param trustedMinResults_out Pointer to an array for the minimum/lower interval limits. Annotation: In case of an error the values are not specified.
 * @param trustedMaxResults_out Pointer to an array for the maximum/upper interval limits. Annotation: In case of an error the value is not specified.
 * @param errorTypes_out Pointer to an array of the paceval.-Computation object errors, see also paceval_eErrorTypes in paceval_main.h or paceval_GetErrorInformation().
 *
 * see  https://paceval.com/api/#paceval_dGetMultipleComputationsResultsExt for more information
 */
bool paceval_dGetMultipleComputationsResultsExt(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        double values_in[],
        unsigned long numberOfCalculations_in,
        double* results_out,
        double* trustedMinResults_out,
        double* trustedMaxResults_out,
        int* errorTypes_out);

/**
 * Performs multiple calculations (float) in parallel on multiple paceval.-Computation objects using the variables declared by paceval_CreateComputation() and with multiple sets of values for those variables. You should use paceval_dGetMultipleComputationsResultsExt() to get results for multiple computations at the same time and to carry out as many different evaluations as possible at once (e.g. for artificial neural network functions or decision trees in which several functions with different variable values are calculated in one step for several objects at the same time to decide). Annotation: You must use the same number of variables and the same declared variables. To do so you can simply declare all variables in each of the the calls for paceval_CreateComputation(). There is no performance issue in case a variable is declared but not used by a paceval.-Computation object.
 * The return value indicates paceval.-Computation object errors. You should check the array errorTypes_out in this case.
 * @param handle_pacevalComputations_in Array of the paceval.-Computation objects.
 * @param numberOfpacevalComputations_in Specifies the number of the paceval.-Computation objects.
 * @param values_in Array of float defining the values of the variables.
 * @param numberOfCalculations_in Specifies the number of different calculations you want to run. This number specifies the size of the array values_in[]. E.g. if the number of variables declared is 50 and the number of calculations is 1000 the size of the array values_in[] must be 50*1000. The order of the array values_in[] must be variable values for the first calculation, then variable values for the second calculation and so on.
 * @param results_out Pointer to an array for the results of the multiple computations. Annotation: In case of an error the values are not specified.
 * @param trustedMinResults_out Pointer to an array for the minimum/lower interval limits. Annotation: In case of an error the values are not specified.
 * @param trustedMaxResults_out Pointer to an array for the maximum/upper interval limits. Annotation: In case of an error the value is not specified.
 * @param errorTypes_out Pointer to an array of the paceval.-Computation object errors, see also paceval_eErrorTypes in paceval_main.h or paceval_GetErrorInformation().
 *
 * see  https://paceval.com/api/#paceval_dGetMultipleComputationsResultsExt for more information
 */
bool paceval_fGetMultipleComputationsResultsExt(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        float values_in[],
        unsigned long numberOfCalculations_in,
        float* results_out,
        float* trustedMinResults_out,
        float* trustedMaxResults_out,
        int* errorTypes_out);

/**
 * Determines whether an error has occurred. To get more information about the error, call paceval_GetErrorInformation().
 * If an error has occurred, the return value is true. Otherwise it is false.
 * @param handle_pacevalComputation_in Identifies the paceval.-Computation object.
 *
 * see  https://paceval.com/api/#paceval_GetIsError for more information
 */
bool paceval_GetIsError(PACEVAL_HANDLE handle_pacevalComputation_in);

/**
 * The paceval_GetErrorInformation() function returns the paceval.-Computation object error type value. Possible errors are analysis and computation errors. Errors during the analysis should be checked after creation of the object like paceval_CreateComputation(). Errors during the computation should be checked after paceval_GetComputationResult().
 * The return value is the paceval.-Computation object error, see also paceval_eErrorTypes in paceval_main.h and below. You can retrieve further information for the error type via paceval_CreateErrorInformationText(), e.g. to present this to the user:
 * - PACEVAL_ERR_NO_ERROR = 0: No error occured for this computation object.
 * - PACEVAL_ERR_FATAL_INITIALIZE_LIBRARY_NOT_CALLED = 10: Initialization of paceval. with paceval_InitializeLibrary() is missing.
 * - PACEVAL_ERR_FATAL_NO_LICENSE = 11: Get in contact with us via info@paceval.com for a license.
 * - PACEVAL_ERR_FATAL_CONNECTING_SERVER = 15: This is a placeholder for the error codes when using an external library, e.g. like curl.
 * - PACEVAL_ERR_FATAL_PARAMETERS_SERVER = 16: This is a placeholder for the error codes when using an external library, e.g. like curl.
 * - PACEVAL_ERR_ANALYSIS_UNKNOWN_SIGN_OR_FUNCTION = 110: The function string contains an unknown sign or subfunction.
 * - PACEVAL_ERR_ANALYSIS_BRACKETS = 111: Incorrect brackets are set in the function string.
 * - PACEVAL_ERR_ANALYSIS_UNKNOWN_CONSTANT_OR_VARIABLE = 112: The function string contains an unknown constant factor or variable.
 * - PACEVAL_ERR_ANALYSIS_COMMENT = 113: An invalid comment in the function string.
 * - PACEVAL_ERR_ANALYSIS_NUMBER_OF_VARIABLES = 114: The specified number of variables is not the number of the declared variables.
 * - PACEVAL_ERR_ANALYSIS_MISPLACED_SIGN_CALCULATION = 115: An operator is set incorrectly in the function string.
 * - PACEVAL_ERR_ANALYSIS_UNEXPECTED_END = 116: An unexpected end in the function string.
 * - PACEVAL_ERR_ANALYSIS_WRONGLY_USED_FUNCTION = 117: A subfunction is set incorrectly in the function string.
 * - PACEVAL_ERR_ANALYSIS_NO_USER_FUNCTION = 118: No user function and no operations.
 * - PACEVAL_ERR_ANALYSIS_UNKNOWN_CHARACTER = 119: The function string contains an unknown character.
 * - PACEVAL_ERR_ANALYSIS_WRONGLY_USED_CONSTANT_OR_VALUE = 120: A constant factor or value is not correctly used.
 * - PACEVAL_ERR_ANALYSIS_MISSING_OPERATOR = 121: An operator is missing for operands.
 * - PACEVAL_ERR_ANALYSIS_OUT_OF_MEMORY = 122: Analysis out of memory.
 * - PACEVAL_ERR_ANALYSIS_UNKNOWN_OBJECT_TYPE = 124: An invalid object-type was passed.
 * - PACEVAL_ERR_ANALYSIS_MEMORY_CLEANUP = 126: An error has occured in the memory cleanup.
 * - PACEVAL_ERR_ANALYSIS_USER_ABORT = 127: The analysis was aborted by the user.
 * - PACEVAL_ERR_ANALYSIS_MATH_OS_NOT_SUPPORTED = 128: The operating system may not be supported due to known mathematical errors.
 * - PACEVAL_ERR_ANALYSIS_NO_COMMUNITY_FEATURE = 130: This feature is not supported in the free version of paceval.
 * - PACEVAL_ERR_COMPUTATION_HANDLE_INVALID = 140: An invalid handle was passed.
 * - PACEVAL_ERR_COMPUTATION_MULTIPLICATION = 141: A multiplication causes an error.
 * - PACEVAL_ERR_COMPUTATION_DIVISION = 142: A division causes an error.
 * - PACEVAL_ERR_COMPUTATION_FUNCTION = 143: The result of the calculation is not valid.
 * - PACEVAL_ERR_COMPUTATION_ADDITION = 144: An addition causes an error.
 * - PACEVAL_ERR_COMPUTATION_SUBTRACTION = 145: A subtraction causes an error.
 * - PACEVAL_ERR_COMPUTATION_UNSPECIFIED = 150: A not specified user-function causes an error.
 * - PACEVAL_ERR_COMPUTATION_INTERVAL_RESULT = 151: The interval result of the calculation is not trusted.
 * - PACEVAL_ERR_COMPUTATION_USER_ABORT = 152: The calculation was aborted by the user.
 * - PACEVAL_ERR_COMPUTATION_RESULT = 153: The result of the calculation is not trusted.
 * - PACEVAL_ERR_COMPUTATION_BUSY = 154: The referenced computation object is busy.
 * - PACEVAL_ERR_COMPUTATION_USER_COMPILER_NOT_SUPPORTS_LONG_DOUBLE = 160: Your compiler does not support long double floating-point data type.
 * - PACEVAL_ERR_COMPUTATION_PRECHECK_MULTIPLE = 161: Precheck failed for multiple operations, e.g. a handle may only occur once.
 *
 * @param handle_pacevalComputation_in Identifies the paceval.-Computation object.
 *
 * see  https://paceval.com/api/#paceval_GetErrorInformation for more information
 */
int paceval_GetErrorInformation(PACEVAL_HANDLE handle_pacevalComputation_in,
                                char *lastError_strOperator_out,
                                long* lastError_errPosition_out);

/**
 * The paceval_CreateErrorInformationText() is a helper function to create error information in text from a paceval.-Computation object. It can be used to provide more information to the user. For more details see paceval_GetIsError() and paceval_GetErrorInformation().
 * The return value is maximum length of lastError_strMessage_out and lastError_strDetails_out.
 * @param handle_pacevalComputation_in Identifies the paceval.-Computation object.
 * @param lastError_strMessage_out Buffer to get message describing the error. Annotation: Maximum size of the retrieved null-terminated string is 255 per “#define PACEVAL_MAXERR 255”, see paceval_main.h.
 * @param lastError_strDetails_out Buffer to get details like error type as a number, the operator and the position in the function. Annotation: Maximum size of the retrieved null-terminated string is 255 per “#define PACEVAL_MAXERR 255”, see paceval_main.h.
 *
 * see  https://paceval.com/api/#paceval_CreateErrorInformationText for more information
 */
int paceval_CreateErrorInformationText(PACEVAL_HANDLE handle_pacevalComputation_in,
                                       char* lastError_strMessage_out,
                                       char* lastError_strDetails_out);

/**
 * The paceval_GetErrorTypeMessage() is a helper function to create an error message in text from an error type. It can be used to provide more information to the user. For more details see paceval_GetIsError() and paceval_GetErrorInformation().
 * The return value is the length of lastError_strMessage_out.
 * @param errorType_in Specifies the the error type value.
 * @param errorType_strMessage_out Buffer to get message describing the error. Annotation: Maximum size of the retrieved null-terminated string is 255 per “#define PACEVAL_MAXERR 255”, see paceval_main.h.
 *
 * see  https://paceval.com/api/#paceval_GetErrorTypeMessage for more information
 */
int paceval_GetErrorTypeMessage(int errorType_in,
                                char* errorType_strMessage_out);

/**
 * Returns the version string including the version number of the paceval.-Computation object.
 * The return value is the length of the version string.
 * @param handle_pacevalComputation_in Identifies the paceval.-Computation object.
 * @param paceval_strVersion_out Points to the buffer that will receive the string. Set paceval_strVersion_in to NULL to receive the length of the version string.
 *
 * see  https://paceval.com/api/#paceval_GetComputationVersionString for more information
 */
int paceval_GetComputationVersionString(PACEVAL_HANDLE handle_pacevalComputation_in,
                                        char* paceval_strVersion_out);

/**
 * Allows the definition of up to 1000 custom user functions. Depending on your requirements, you could a) add mathematical functions that enable new functions, e.g. with Boost or b) add faster mathematical functions that are not as accurate as those used by paceval., e.g. math-neon.
 * If the function succeeds, the return value is true. Otherwise it is false.
 * @param numberUserFunction_in Specifies the number of the user function to set the single function for, e.g. 1.
 * @param singleFunctionString_in Points to a null-terminated string specifying the user-defined single function, e.g. "my_function1".
 * @param paceval_callbackUserFunction_in A user-defined callback function to handle the computation for the specific single function, see paceval_main.h.
 *
 * see  https://paceval.com/api/#paceval_SetCallbackUserFunction for more information
 */
bool paceval_SetCallbackUserFunction(unsigned int numberUserFunction_in,
                                     const char* singleFunctionString_in,
                                     paceval_callbackUserFunctionType* paceval_callbackUserFunction_in);

/**
 * You must call paceval_InitializeLibrary() before you use paceval.-API function calls in your code. Annotation: In case you use the standard Windows library version this loads and initializes the paceval_win32.dll for 32bit Windows-Applications (x86) or paceval_win64i.dll for 64bit Windows-Applications (x64).
 * If the function succeeds, the return value is true. Otherwise it is false.
 * @param initString_in This parameter is not used in the non-commercial version. Just pass NULL pointer (e.g. "paceval_InitializeLibrary(NULL);").
 *
 * see  https://paceval.com/api/#paceval_InitializeLibrary for more information
 */
bool paceval_InitializeLibrary(const char* initString_in);

/**
 * You must call paceval_FreeLibrary() at the end of your application. Annotation: In case you use the standard Windows library version this frees the paceval_win32.dll for 32bit Windows-Applications (x86) or paceval_win64i.dll for 64bit Windows-Applications (x64).
 * If the function succeeds, the return value is true. Otherwise it is false.
 *
 * see  https://paceval.com/api/#paceval_FreeLibrary for more information
 */
bool paceval_FreeLibrary();

/**
 * A helper function to create XML data representing a paceval.-Computation object. You can use it to store data representing a computation to a file system or to transmit it via a network or channel.
 * The return value is the size of the XML data. In case of an error the return value is 0.
 * @param paceval_strXML_out Pointer to a buffer for the XML data. Set paceval_strXML_out to NULL to receive the length of the version string.
 * @param functionString_in Points to a null-terminated string representing the function.
 * @param numberOfVariables_in Specifies the number of variables.
 * @param variables_in Points to a null-terminated string specifying the names of the variables in one string seperated by blanks.
 * @param valuesString_in Specifies the values for the variables in one string seperated by semicolons (;).
 * @param useInterval_in Specifies whether Trusted Interval Computation is enabled or not.
 *
 * see  https://paceval.com/api/#paceval_CreateXMLFromParameters for more information
 */
unsigned long paceval_CreateXMLFromParameters(char* paceval_strXML_out,
        const char* functionString_in,
        unsigned long numberOfVariables_in,
        const char* variables_in,
        const char* valuesString_in,
        bool useInterval_in);

/**
 * A helper function to read XML data representing a paceval.-Computation object. You can use it to read data representing a computation from a file system or to receive it via a network or channel.
 * In case of an error the return value is <0.
 * @param paceval_strXML_in Pointer to the XML data.
 * @param functionStringLength_out The length of the function string.
 * @param variablesStringLength_out The length of the variable names in one string.
 * @param numberOfVariables_out The number of variables.
 * @param valuesStringLength_out The length of the values seperated by blanks in one string.
 * @param functionString_out Points to the buffer for the function string. Set functionString_out to NULL to receive the length at first with functionStringLength_out.
 * @param variables_out Points to the buffer for the variable names in one string. Set variables_out to NULL to receive the length at first with variablesStringLength_out.
 * @param valuesString_out Points to the buffer for the values seperated by semicolons (;) in one string. Set valuesString_out to NULL to receive the length at first with valuesStringLength_out.
 * @param useInterval_out Points to the buffer specifying whether Trusted Interval Computation is enabled or not.
 *
 * see  https://paceval.com/api/#paceval_ReadParametersFromXML for more information
 */
int paceval_ReadParametersFromXML(const char* paceval_strXML_in,
                                  unsigned long* functionStringLength_out,
                                  unsigned long* variablesStringLength_out,
                                  unsigned long* numberOfVariables_out,
                                  unsigned long* valuesStringLength_out,
                                  char* functionString_out,
                                  char* variables_out,
                                  char* valuesString_out,
                                  bool* useInterval_out);

/**
 * A helper function for getting data from a paceval.-Computation object, such as the number of cores in the system, the number of threads used or the cache hits in the computations with that particular paceval.-Computation object.
 * The return value is the size of the XML data. In case of an error the return value is 0.
 * @param handle_pacevalComputation_in Identifies the paceval.-Computation object.
 * @param paceval_strXML_out Pointer to a buffer for the XML data. Set paceval_strXML_out to NULL to receive the length of the version string.
 *
 * see  https://paceval.com/api/#paceval_GetComputationInformationXML for more information
 */
unsigned long paceval_GetComputationInformationXML(PACEVAL_HANDLE handle_pacevalComputation_in,
        char* paceval_strXML_out);

#ifdef __cplusplus
}
#endif
//---------------------------------------------------------------------------
#endif //paceval_mainH
