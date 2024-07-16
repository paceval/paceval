//---------------------------------------------------------------------------
// Copyright ©1994-2024. Version 1.x, 2.x, 3.x, 4.x ©1994-2024
//       Joerg Koenning & paceval.[Registered Trade Mark] All rights reserved.
// Author(s) : paceval., see http://www.paceval.com
// File      : paceval_main.cpp
// License   : paceval source code GNU Affero General Public License (AGPL)
//---------------------------------------------------------------------------

/**
 * @file paceval_main.cpp
 * @brief the paceval. application programming interface - for documentation please go to https://paceval.com/api/
 */
//---------------------------------------------------------------------------
#if defined(_MSC_VER)
#endif //#if defined(_MSC_VER)


#include <stdarg.h>
#include "../source_public/inc/paceval_main.h"

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
#include <windows.h>

#if !defined(_WIN64)
HINSTANCE handle_paceval_DLL = 0;
#else
HMODULE  handle_paceval_DLL = 0;
bool paceval_WIN64_i = true;
#endif //#if !defined(_WIN64)
#endif //defined(paceval_use_dll)


#if defined(paceval_use_dll) && (paceval_use_dll == 1)
bool (*pacevalLibrary_Initialize)(const char* initString_in);
#else
/**
 * Foreign function interface (FFI) version of paceval_InitializeLibrary() (Windows):
 * initializes the paceval-library - you must call pacevalLibrary_Initialize() before you use paceval-API function calls in your code - if the function succeeds, the return value is TRUE, otherwise it is FALSE
 * @param initString_in specifies a string that can be used for additional parameterization of the library, e.g. a string for licensing (annotation: if the string is not used, NULL can be passed)
 */
extern "C" bool pacevalLibrary_Initialize(const char* initString_in);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
bool (*pacevalLibrary_Free)();
#else
/**
 * Foreign function interface (FFI) version of paceval_FreeLibrary() (Windows):
 * frees the paceval.-library - you must call pacevalLibrary_Free() at the end of your application - if the function succeeds, the return value is TRUE, otherwise it is FALSE
 */
extern "C" bool pacevalLibrary_Free();
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
PACEVAL_HANDLE (*pacevalLibrary_CreateComputation)(const char* functionString_in,
        unsigned long numberOfVariables_in,
        const char* variables_in,
        bool useInterval_in,
        paceval_callbackStatusType* paceval_callbackStatus_in);
#else
/**
 * Foreign function interface (FFI) version of paceval_CreateComputation() (Windows):
 * creates a paceval_cComputation object for a mathematical function and its variables - the return value is the HANDLE of the created paceval_cComputation object (pacevalLibrary_GetIsError() should be called to check whether an error has occurred)
 * @param functionString_in points to a null-terminated string to be used as the function to work with
 * @param numberOfVariables_in specifies the number of variables to work with (e.g. if the variables are "xValue yValue zValue" or "x y z" numberOfVariables_in must be set to 3)
 * @param variables_in points to a null-terminated string specifying the names of the working variables (generally the variables must be separated by a blank, e.g. the variables xValue, yValue, zValue must be set with "xValue yValue zValue" or the variables x, y, z must be set with "x y z")
 * @param useInterval_in enables or disables the Trusted Interval Computation, TINC (paceval specific) putting bounds on rounding errors and measurement errors of the computation system to yield reliable results
 * @param paceval_callbackStatus_in a user-defined callback function to give status information of the paceval_cComputation object, see paceval_main.h
 */
extern "C" PACEVAL_HANDLE pacevalLibrary_CreateComputation(const char* functionString_in,
        unsigned long numberOfVariables_in,
        const char* variables_in,
        bool useInterval_in,
        paceval_callbackStatusType* paceval_callbackStatus_in);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
bool (*pacevalLibrary_CreateMultipleComputations)(PACEVAL_HANDLE handle_pacevalComputations_out[],
        const char* functionStrings_in[],
        unsigned long numberOfpacevalComputations_in,
        unsigned long numberOfVariables_in,
        const char* variables_in,
        bool useInterval_in,
        paceval_callbackStatusType* paceval_callbackStatus_in);
#else
/**
 * Foreign function interface (FFI) version of paceval_CreateMultipleComputations() (Windows):
 * creates paceval_cComputation objects for multiple mathematical functions and one set of variables in a single step - if the function succeeds, the return value is TRUE and handle_pacevalComputations_out contains the paceval_cComputation objects (each of these objects can be used individually, e.g. with pacevalLibrary_dGetComputationResult(), pacevalLibrary_dGetMultipleComputationsResults(), pacevalLibrary_dmathv() or pacevalLibrary_dmathvi() and must be deleted with pacevalLibrary_DeleteComputation())
 * @param functionStrings_in points to an array of null-terminated strings to be used as the functions to work with for the created paceval_cComputation objects
 * @param numberOfpacevalComputations_in specifies the number of paceval_cComputation objects to create (e.g. if the functions to work with are "sin(x)" and "cos(x)" numberOfpacevalComputations_in must be set to 2)
 * @param numberOfVariables_in specifies the number of variables to work with (e.g. if the variables are "xValue yValue zValue" or "x y z" numberOfVariables_in must be set to 3)
 * @param variables_in points to a null-terminated string specifying the names of the working variables (generally the variables must be separated by a blank, e.g. the variables xValue, yValue, zValue must be set with "xValue yValue zValue" or the variables x, y, z must be set with "x y z")
 * @param useInterval_in enables or disables the Trusted Interval Computation, TINC (paceval specific) putting bounds on rounding errors and measurement errors of the computation system to yield reliable results
 * @param paceval_callbackStatus_in a user-defined callback function to give status information of the paceval_cComputation objects, see paceval_main.h
 */
extern "C" bool pacevalLibrary_CreateMultipleComputations(PACEVAL_HANDLE handle_pacevalComputations_out[],
        const char* functionStrings_in[],
        unsigned long numberOfpacevalComputations_in,
        unsigned long numberOfVariables_in,
        const char* variables_in,
        bool useInterval_in,
        paceval_callbackStatusType* paceval_callbackStatus_in);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
int (*pacevalLibrary_ldConvertFloatToString)(char* destinationString_in,
        long double float_in);
#else
/**
 * Foreign function interface (FFI) version of paceval_ldConvertFloatToString() (Windows):
 * converts a floating point number with precision long double to a string - if the function succeeds, the return value is >0 and gives the precision of the conversion, otherwise the return value is <0
 * @param destinationString_in points to the buffer that will receive the string of the coverted floating point number (annotation: in case of an error the buffer is not specified)
 * @param float_in the floating point number with precision long double to convert
 */
extern "C" int pacevalLibrary_ldConvertFloatToString(char* destinationString_in,
        long double float_in);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
int (*pacevalLibrary_dConvertFloatToString)(char* destinationString_in,
        double float_in);
#else
/**
 * Foreign function interface (FFI) version of paceval_dConvertFloatToString() (Windows):
 * converts a floating point number with precision double to a string - if the function succeeds, the return value is >0 and gives the precision of the conversion, otherwise the return value is <0
 * @param destinationString_in points to the buffer that will receive the string of the coverted floating point number (annotation: in case of an error the buffer is not specified)
 * @param float_in the floating point number with precision double to convert
 */
extern "C" int pacevalLibrary_dConvertFloatToString(char* destinationString_in,
        double float_in);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
int (*pacevalLibrary_fConvertFloatToString)(char* destinationString_in,
        float float_in);
#else
/**
 * Foreign function interface (FFI) version of paceval_fConvertFloatToString() (Windows):
 * converts a floating point number with precision float to a string - if the function succeeds, the return value is >0 and gives the precision of the conversion, otherwise the return value is <0
 * @param destinationString_in points to the buffer that will receive the string of the coverted floating point number (annotation: in case of an error the buffer is not specified)
 * @param float_in the floating point number with precision float to convert
 */
extern "C" int pacevalLibrary_fConvertFloatToString(char* destinationString_in,
        float float_in);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
long double (*pacevalLibrary_ldConvertStringToFloat)(const char* sourceString_in,
        int* errorType_out,
        long* errPosition_out,
        bool useInterval_in,
        long double* trustedMinResult_out,
        long double* trustedMaxResult_out);
#else
/**
 * Foreign function interface (FFI) version of paceval_ldConvertStringToFloat() (Windows):
 * converts a string to a floating point number with precision long double (in case a caluclation is given in the string the result is converted) - if the function succeeds, the return value is the result of the conversion (annotation: in case of an error the return value is not specified)
 * @param sourceString_in the string to convert
 * @param errorType_out points to the buffer that will receive the paceval_cComputation object error, see also paceval_eErrorTypes or pacevalLibrary_GetErrorInformation()
 * @param errPosition_out position in the string where the error occurred
 * @param useInterval_in enables or disables the Trusted Interval Computation, TINC (paceval specific) for the conversion
 * @param trustedMinResult_out if Trusted Interval Computation was enabled this retrieves the minimum/lower interval limit of the conversion (annotation: in case of an error the value is not specified)
 * @param trustedMaxResult_out if Trusted Interval Computation was enabled this retrieves the maximum/upper interval limit of the conversion (annotation: in case of an error the value is not specified)
 */
extern "C" long double pacevalLibrary_ldConvertStringToFloat(const char* sourceString_in,
        int* errorType_out,
        long* errPosition_out,
        bool useInterval_in,
        long double* trustedMinResult_out,
        long double* trustedMaxResult_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
double (*pacevalLibrary_dConvertStringToFloat)(const char* sourceString_in,
        int* errorType_out,
        long* errPosition_out,
        bool useInterval_in,
        double* trustedMinResult_out,
        double* trustedMaxResult_out);
#else
/**
 * Foreign function interface (FFI) version of paceval_dConvertStringToFloat() (Windows):
 * converts a string to a floating point number with precision double (in case a caluclation is given in the string the result is converted) - if the function succeeds, the return value is the result of the conversion (annotation: in case of an error the return value is not specified)
 * @param sourceString_in the string to convert
 * @param errorType_out points to the buffer that will receive the paceval_cComputation object error, see also paceval_eErrorTypes or pacevalLibrary_GetErrorInformation()
 * @param errPosition_out position in the string where the error occurred
 * @param useInterval_in enables or disables the Trusted Interval Computation, TINC (paceval specific) for the conversion
 * @param trustedMinResult_out if Trusted Interval Computation was enabled this retrieves the minimum/lower interval limit of the conversion (annotation: in case of an error the value is not specified)
 * @param trustedMaxResult_out if Trusted Interval Computation was enabled this retrieves the maximum/upper interval limit of the conversion (annotation: in case of an error the value is not specified)
 */
extern "C" double pacevalLibrary_dConvertStringToFloat(const char* sourceString_in,
        int* errorType_out,
        long* errPosition_out,
        bool useInterval_in,
        double* trustedMinResult_out,
        double* trustedMaxResult_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
float (*pacevalLibrary_fConvertStringToFloat)(const char* sourceString_in,
        int* errorType_out,
        long* errPosition_out,
        bool useInterval_in,
        float* trustedMinResult_out,
        float* trustedMaxResult_out);
#else
/**
 * Foreign function interface (FFI) version of paceval_fConvertStringToFloat() (Windows):
 * converts a string to a floating point number with precision float (in case a caluclation is given in the string the result is converted) - if the function succeeds, the return value is the result of the conversion (annotation: in case of an error the return value is not specified)
 * @param sourceString_in the string to convert
 * @param errorType_out points to the buffer that will receive the paceval_cComputation object error, see also paceval_eErrorTypes or pacevalLibrary_GetErrorInformation()
 * @param errPosition_out position in the string where the error occurred
 * @param useInterval_in enables or disables the Trusted Interval Computation, TINC (paceval specific) for the conversion
 * @param trustedMinResult_out if Trusted Interval Computation was enabled this retrieves the minimum/lower interval limit of the conversion (annotation: in case of an error the value is not specified)
 * @param trustedMaxResult_out if Trusted Interval Computation was enabled this retrieves the maximum/upper interval limit of the conversion (annotation: in case of an error the value is not specified)
 */
extern "C" float pacevalLibrary_fConvertStringToFloat(const char* sourceString_in,
        int* errorType_out,
        long* errPosition_out,
        bool useInterval_in,
        float* trustedMinResult_out,
        float* trustedMaxResult_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
long double (*pacevalLibrary_ldmathv)(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
                                      int* errorType_out,
                                      const char* functionString_in,
                                      unsigned long numberOfVariables_in,
                                      const char* variables_in,
                                      long double values_in[]);
#else
/**
 * Foreign function interface (FFI) version of paceval_ldmathv() (Windows):
 * a convenience function to get results of computations in a single step with precision long double - if the function succeeds, the return value is the result of the computation (pacevalLibrary_GetIsError() should be called to check whether an error has occurred and to get more information about the error, call pacevalLibrary_GetErrorInformation()) (annotation: in case of an error the return value is not specified)
 * @param handle_pacevalComputation_out_in pointer to a paceval_cComputation object (if handle_pacevalComputation_out_in is not NULL this buffer will retrieve the created paceval_cComputation object and can be used again and this will improve the performance -> in this case the paceval_cComputation object will not be deleted and you must call pacevalLibrary_DeleteComputation())
 * @param errorType_out points to the buffer that will receive the paceval_cComputation object error, see also paceval_eErrorTypes or pacevalLibrary_GetErrorInformation()
 * @param functionString_in points to a null-terminated string to be used as the function to work with
 * @param numberOfVariables_in specifies the number of variables to work with (e.g. if the variables are "xValue yValue zValue" or "x y z" numberOfVariables_in must be set to 3)
 * @param variables_in points to a null-terminated string specifying the names of the working variables (generally the variables must be separated by a blank, e.g. the variables xValue, yValue, zValue must be set with "xValue yValue zValue" or the variables x, y, z must be set with "x y z")
 * @param values_in array of long double defining the values of the variables
 */
extern "C" long double pacevalLibrary_ldmathv(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
        int* errorType_out,
        const char* functionString_in,
        unsigned long numberOfVariables_in,
        const char* variables_in,
        long double values_in[]);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
double (*pacevalLibrary_dmathv)(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
                                int* errorType_out,
                                const char* functionString_in,
                                unsigned long numberOfVariables_in,
                                const char* variables_in,
                                double values_in[]);
#else
/**
 * Foreign function interface (FFI) version of paceval_dmathv() (Windows):
 * a convenience function to get results of computations in a single step with precision double - if the function succeeds, the return value is the result of the computation (pacevalLibrary_GetIsError() should be called to check whether an error has occurred and to get more information about the error, call pacevalLibrary_GetErrorInformation()) (annotation: in case of an error the return value is not specified)
 * @param handle_pacevalComputation_out_in pointer to a paceval_cComputation object (if handle_pacevalComputation_out_in is not NULL this buffer will retrieve the created paceval_cComputation object and can be used again and this will improve the performance -> in this case the paceval_cComputation object will not be deleted and you must call pacevalLibrary_DeleteComputation())
 * @param errorType_out points to the buffer that will receive the paceval_cComputation object error, see also paceval_eErrorTypes or pacevalLibrary_GetErrorInformation()
 * @param functionString_in points to a null-terminated string to be used as the function to work with
 * @param numberOfVariables_in specifies the number of variables to work with (e.g. if the variables are "xValue yValue zValue" or "x y z" numberOfVariables_in must be set to 3)
 * @param variables_in points to a null-terminated string specifying the names of the working variables (generally the variables must be separated by a blank, e.g. the variables xValue, yValue, zValue must be set with "xValue yValue zValue" or the variables x, y, z must be set with "x y z")
 * @param values_in array of double defining the values of the variables
 */
extern "C" double pacevalLibrary_dmathv(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
                                        int* errorType_out,
                                        const char* functionString_in,
                                        unsigned long numberOfVariables_in,
                                        const char* variables_in,
                                        double values_in[]);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
float (*pacevalLibrary_fmathv)(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
                               int* errorType_out,
                               const char* functionString_in,
                               unsigned long numberOfVariables_in,
                               const char* variables_in,
                               float values_in[]);
#else
/**
 * Foreign function interface (FFI) version of paceval_fmathv() (Windows):
 * a convenience function to get results of computations in a single step with precision float - if the function succeeds, the return value is the result of the computation (pacevalLibrary_GetIsError() should be called to check whether an error has occurred and to get more information about the error, call pacevalLibrary_GetErrorInformation()) (annotation: in case of an error the return value is not specified)
 * @param handle_pacevalComputation_out_in pointer to a paceval_cComputation object (if handle_pacevalComputation_out_in is not NULL this buffer will retrieve the created paceval_cComputation object and can be used again and this will improve the performance -> in this case the paceval_cComputation object will not be deleted and you must call pacevalLibrary_DeleteComputation())
 * @param errorType_out points to the buffer that will receive the paceval_cComputation object error, see also paceval_eErrorTypes or pacevalLibrary_GetErrorInformation()
 * @param functionString_in points to a null-terminated string to be used as the function to work with
 * @param numberOfVariables_in specifies the number of variables to work with (e.g. if the variables are "xValue yValue zValue" or "x y z" numberOfVariables_in must be set to 3)
 * @param variables_in points to a null-terminated string specifying the names of the working variables (generally the variables must be separated by a blank, e.g. the variables xValue, yValue, zValue must be set with "xValue yValue zValue" or the variables x, y, z must be set with "x y z")
 * @param values_in array of float defining the values of the variables
 */
extern "C" float pacevalLibrary_fmathv(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
                                       int* errorType_out,
                                       const char* functionString_in,
                                       unsigned long numberOfVariables_in,
                                       const char* variables_in,
                                       float values_in[]);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
long double (*pacevalLibrary_ldmathvi)(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
                                       int* errorType_out,
                                       long double* trustedMinResult_out,
                                       long double* trustedMaxResult_out,
                                       const char* functionString_in,
                                       unsigned long numberOfVariables_in,
                                       const char* variables_in,
                                       long double values_in[]);
#else
/**
 * Foreign function interface (FFI) version of paceval_ldmathvi() (Windows):
 * a convenience function to get results of computations in a single step with precision long double and with Trusted Interval Computation, TINC (paceval specific) - if the function succeeds, the return value is the result of the computation (pacevalLibrary_GetIsError() should be called to check whether an error has occurred and to get more information about the error, call pacevalLibrary_GetErrorInformation()) (annotation: in case of an error the return value is not specified)
 * @param handle_pacevalComputation_out_in pointer to a paceval_cComputation object (if handle_pacevalComputation_out_in is not NULL this buffer will retrieve the created paceval_cComputation object and can be used again and this will improve the performance -> in this case the paceval_cComputation object will not be deleted and you must call pacevalLibrary_DeleteComputation())
 * @param errorType_out points to the buffer that will receive the paceval_cComputation object error, see also paceval_eErrorTypes or pacevalLibrary_GetErrorInformation()
 * @param trustedMinResult_out this buffer retrieves the minimum/lower interval limit of the computation (annotation: In case of an error the value is not specified)
 * @param trustedMaxResult_out this buffer retrieves the maximum/upper limit of the computation (annotation: In case of an error the value is not specified)
 * @param functionString_in points to a null-terminated string to be used as the function to work with
 * @param numberOfVariables_in specifies the number of variables to work with (e.g. if the variables are "xValue yValue zValue" or "x y z" numberOfVariables_in must be set to 3)
 * @param variables_in points to a null-terminated string specifying the names of the working variables (generally the variables must be separated by a blank, e.g. the variables xValue, yValue, zValue must be set with "xValue yValue zValue" or the variables x, y, z must be set with "x y z")
 * @param values_in array of long double defining the values of the variables
 */
extern "C" long double pacevalLibrary_ldmathvi(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
        int* errorType_out,
        long double* trustedMinResult_out,
        long double* trustedMaxResult_out,
        const char* functionString_in,
        unsigned long numberOfVariables_in,
        const char* variables_in,
        long double values_in[]);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
double (*pacevalLibrary_dmathvi)(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
                                 int* errorType_out,
                                 double* trustedMinResult_out,
                                 double* trustedMaxResult_out,
                                 const char* functionString_in,
                                 unsigned long numberOfVariables_in,
                                 const char* variables_in,
                                 double values_in[]);
#else
/**
 * Foreign function interface (FFI) version of paceval_dmathvi() (Windows):
 * a convenience function to get results of computations in a single step with precision double and with Trusted Interval Computation, TINC (paceval specific) - if the function succeeds, the return value is the result of the computation (pacevalLibrary_GetIsError() should be called to check whether an error has occurred and to get more information about the error, call pacevalLibrary_GetErrorInformation()) (annotation: in case of an error the return value is not specified)
 * @param handle_pacevalComputation_out_in pointer to a paceval_cComputation object (if handle_pacevalComputation_out_in is not NULL this buffer will retrieve the created paceval_cComputation object and can be used again and this will improve the performance -> in this case the paceval_cComputation object will not be deleted and you must call pacevalLibrary_DeleteComputation())
 * @param errorType_out points to the buffer that will receive the paceval_cComputation object error, see also paceval_eErrorTypes or pacevalLibrary_GetErrorInformation()
 * @param trustedMinResult_out this buffer retrieves the minimum/lower interval limit of the computation (annotation: In case of an error the value is not specified)
 * @param trustedMaxResult_out this buffer retrieves the maximum/upper limit of the computation (annotation: In case of an error the value is not specified)
 * @param functionString_in points to a null-terminated string to be used as the function to work with
 * @param numberOfVariables_in specifies the number of variables to work with (e.g. if the variables are "xValue yValue zValue" or "x y z" numberOfVariables_in must be set to 3)
 * @param variables_in points to a null-terminated string specifying the names of the working variables (generally the variables must be separated by a blank, e.g. the variables xValue, yValue, zValue must be set with "xValue yValue zValue" or the variables x, y, z must be set with "x y z")
 * @param values_in array of double defining the values of the variables
 */
extern "C" double pacevalLibrary_dmathvi(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
        int* errorType_out,
        double* trustedMinResult_out,
        double* trustedMaxResult_out,
        const char* functionString_in,
        unsigned long numberOfVariables_in,
        const char* variables_in,
        double values_in[]);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
float (*pacevalLibrary_fmathvi)(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
                                int* errorType_out,
                                float* trustedMinResult_out,
                                float* trustedMaxResult_out,
                                const char* functionString_in,
                                unsigned long numberOfVariables_in,
                                const char* variables_in,
                                float values_in[]);
#else
/**
 * Foreign function interface (FFI) version of paceval_fmathvi() (Windows):
 * a convenience function to get results of computations in a single step with precision float and with Trusted Interval Computation, TINC (paceval specific) - if the function succeeds, the return value is the result of the computation (pacevalLibrary_GetIsError() should be called to check whether an error has occurred and to get more information about the error, call pacevalLibrary_GetErrorInformation()) (annotation: in case of an error the return value is not specified)
 * @param handle_pacevalComputation_out_in pointer to a paceval_cComputation object (if handle_pacevalComputation_out_in is not NULL this buffer will retrieve the created paceval_cComputation object and can be used again and this will improve the performance -> in this case the paceval_cComputation object will not be deleted and you must call pacevalLibrary_DeleteComputation())
 * @param errorType_out points to the buffer that will receive the paceval_cComputation object error, see also paceval_eErrorTypes or pacevalLibrary_GetErrorInformation()
 * @param trustedMinResult_out this buffer retrieves the minimum/lower interval limit of the computation (annotation: In case of an error the value is not specified)
 * @param trustedMaxResult_out this buffer retrieves the maximum/upper limit of the computation (annotation: In case of an error the value is not specified)
 * @param functionString_in points to a null-terminated string to be used as the function to work with
 * @param numberOfVariables_in specifies the number of variables to work with (e.g. if the variables are "xValue yValue zValue" or "x y z" numberOfVariables_in must be set to 3)
 * @param variables_in points to a null-terminated string specifying the names of the working variables (generally the variables must be separated by a blank, e.g. the variables xValue, yValue, zValue must be set with "xValue yValue zValue" or the variables x, y, z must be set with "x y z")
 * @param values_in array of float defining the values of the variables
 */
extern "C" float pacevalLibrary_fmathvi(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
                                        int* errorType_out,
                                        float* trustedMinResult_out,
                                        float* trustedMaxResult_out,
                                        const char* functionString_in,
                                        unsigned long numberOfVariables_in,
                                        const char* variables_in,
                                        float values_in[]);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
bool (*pacevalLibrary_ExistComputation)(PACEVAL_HANDLE handle_pacevalComputation_in);
#else
/**
 * Foreign function interface (FFI) version of paceval_ExistComputation() (Windows):
 * determines whether a particular paceval_cComputation object has been created - if the object exists, the return value is TRUE. If the specified HANDLE is invalid or the object does not exist, the return value is FALSE
 * @param handle_pacevalComputation_in identifies the paceval_cComputation object to be questioned
 */
extern "C" bool pacevalLibrary_ExistComputation(PACEVAL_HANDLE handle_pacevalComputation_in);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
bool (*pacevalLibrary_DeleteComputation)(PACEVAL_HANDLE handle_pacevalComputation_in);
#else
/**
 * Foreign function interface (FFI) version of paceval_DeleteComputation() (Windows):
 * deletes a paceval_cComputation object - if the function succeeds, the return value is TRUE (if the given HANDLE is not valid the return value is FALSE)
 * @param handle_pacevalComputation_in identifies the paceval_cComputation object to delete
 */
extern "C" bool pacevalLibrary_DeleteComputation(PACEVAL_HANDLE handle_pacevalComputation_in);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
long double(*pacevalLibrary_ldGetComputationResult)(PACEVAL_HANDLE handle_pacevalComputation_in,
        long double values_in[],
        long double* trustedMinResult_out,
        long double* trustedMaxResult_out);
#else
/**
 * Foreign function interface (FFI) version of paceval_ldGetComputationResult() (Windows):
 * performs a calculation with precision long double on a paceval_cComputation object with the variables declared by pacevalLibrary_CreateComputation() and with a set of values for those variables - if the function succeeds, the return value is the result of the computation (pacevalLibrary_GetIsError() should be called to check whether an error has occurred and to get more information about the error, call pacevalLibrary_GetErrorInformation()) (annotation: in case of an error the return value is not specified)
 * @param handle_pacevalComputation_in identifies the paceval_cComputation object
 * @param values_in array of long double defining the values of the variables
 * @param trustedMinResult_out this buffer retrieves the minimum/lower interval limit of the computation (annotation: In case of an error the value is not specified)
 * @param trustedMaxResult_out this buffer retrieves the maximum/upper limit of the computation (annotation: In case of an error the value is not specified)
 */
extern "C" long double pacevalLibrary_ldGetComputationResult(PACEVAL_HANDLE handle_pacevalComputation_in,
        long double values_in[],
        long double* trustedMinResult_out,
        long double* trustedMaxResult_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
double(*pacevalLibrary_dGetComputationResult)(PACEVAL_HANDLE handle_pacevalComputation_in,
        double values_in[],
        double* trustedMinResult_out,
        double* trustedMaxResult_out);
#else
/**
 * Foreign function interface (FFI) version of paceval_dGetComputationResult() (Windows):
 * performs a calculation with precision double on a paceval_cComputation object with the variables declared by pacevalLibrary_CreateComputation() and with a set of values for those variables - if the function succeeds, the return value is the result of the computation (pacevalLibrary_GetIsError() should be called to check whether an error has occurred and to get more information about the error, call pacevalLibrary_GetErrorInformation()) (annotation: in case of an error the return value is not specified)
 * @param handle_pacevalComputation_in identifies the paceval_cComputation object
 * @param values_in array of double defining the values of the variables
 * @param trustedMinResult_out this buffer retrieves the minimum/lower interval limit of the computation (annotation: In case of an error the value is not specified)
 * @param trustedMaxResult_out this buffer retrieves the maximum/upper limit of the computation (annotation: In case of an error the value is not specified)
 */
extern "C" double pacevalLibrary_dGetComputationResult(PACEVAL_HANDLE handle_pacevalComputation_in,
        double values_in[],
        double* trustedMinResult_out,
        double* trustedMaxResult_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
float(*pacevalLibrary_fGetComputationResult)(PACEVAL_HANDLE handle_pacevalComputation_in,
        float values_in[],
        float* trustedMinResult_out,
        float* trustedMaxResult_out);
#else
/**
 * Foreign function interface (FFI) version of paceval_fGetComputationResult() (Windows):
 * performs a calculation with precision float on a paceval_cComputation object with the variables declared by pacevalLibrary_CreateComputation() and with a set of values for those variables - if the function succeeds, the return value is the result of the computation (pacevalLibrary_GetIsError() should be called to check whether an error has occurred and to get more information about the error, call pacevalLibrary_GetErrorInformation()) (annotation: in case of an error the return value is not specified)
 * @param handle_pacevalComputation_in identifies the paceval_cComputation object
 * @param values_in array of float defining the values of the variables
 * @param trustedMinResult_out this buffer retrieves the minimum/lower interval limit of the computation (annotation: In case of an error the value is not specified)
 * @param trustedMaxResult_out this buffer retrieves the maximum/upper limit of the computation (annotation: In case of an error the value is not specified)
 */
extern "C" float pacevalLibrary_fGetComputationResult(PACEVAL_HANDLE handle_pacevalComputation_in,
        float values_in[],
        float* trustedMinResult_out,
        float* trustedMaxResult_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
bool(*pacevalLibrary_ldGetComputationResultExt)(PACEVAL_HANDLE handle_pacevalComputation_in,
        long double values_in[],
        unsigned long numberOfCalculations_in,
        long double* results_out,
        long double* trustedMinResults_out,
        long double* trustedMaxResults_out,
        int* errorTypes_out);
#else
/**
 * Foreign function interface (FFI) version of paceval_ldGetComputationResultExt() (Windows):
 * performs multiple calculations with precision long double in parallel on a single paceval_cComputation with the variables declared by pacevalLibrary_CreateComputation() and with multiple sets of values for those variables - the return value indicates paceval_cComputation object errors and you should check the array errorTypes_out in this case
 * @param values_in array of long double defining the multiple values of the variables
 * @param numberOfCalculations_in specifies the number of different calculations you want to run and this number specifies the size of the array values_in, e.g. if the number of variables declared is 50 and the number of calculations is 1000 the size of the array values_in must be 50*1000 (the order of the array values_in must be variable values for the first calculation, then variable values for the second calculation and so on)
 * @param results_out pointer to an array for the results of the computation with the multiple values of the variables (annotation: in case of an error the values are not specified)
 * @param trustedMinResults_out pointer to an array for the minimum/lower interval limits (annotation: in case of an error the values are not specified)
 * @param trustedMaxResults_out pointer to an array for the maximum/upper interval limits (annotation: in case of an error the values are not specified)
 * @param errorTypes_out pointer to an array of the paceval_cComputation object errors, see also paceval_eErrorTypes or pacevalLibrary_GetErrorInformation()
 */
extern "C" bool pacevalLibrary_ldGetComputationResultExt(PACEVAL_HANDLE handle_pacevalComputation_in,
        long double values_in[],
        unsigned long numberOfCalculations_in,
        long double* results_out,
        long double* trustedMinResults_out,
        long double* trustedMaxResults_out,
        int* errorTypes_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
bool(*pacevalLibrary_dGetComputationResultExt)(PACEVAL_HANDLE handle_pacevalComputation_in,
        double values_in[],
        unsigned long numberOfCalculations_in,
        double* results_out,
        double* trustedMinResults_out,
        double* trustedMaxResults_out,
        int* errorTypes_out);
#else
/**
 * Foreign function interface (FFI) version of paceval_dGetComputationResultExt() (Windows):
 * performs multiple calculations with precision double in parallel on a single paceval_cComputation with the variables declared by pacevalLibrary_CreateComputation() and with multiple sets of values for those variables - the return value indicates paceval_cComputation object errors and you should check the array errorTypes_out in this case
 * @param values_in array of double defining the multiple values of the variables
 * @param numberOfCalculations_in specifies the number of different calculations you want to run and this number specifies the size of the array values_in, e.g. if the number of variables declared is 50 and the number of calculations is 1000 the size of the array values_in must be 50*1000 (the order of the array values_in must be variable values for the first calculation, then variable values for the second calculation and so on)
 * @param results_out pointer to an array for the results of the computation with the multiple values of the variables (annotation: in case of an error the values are not specified)
 * @param trustedMinResults_out pointer to an array for the minimum/lower interval limits (annotation: in case of an error the values are not specified)
 * @param trustedMaxResults_out pointer to an array for the maximum/upper interval limits (annotation: in case of an error the values are not specified)
 * @param errorTypes_out pointer to an array of the paceval_cComputation object errors, see also paceval_eErrorTypes or pacevalLibrary_GetErrorInformation()
 */
extern "C" bool pacevalLibrary_dGetComputationResultExt(PACEVAL_HANDLE handle_pacevalComputation_in,
        double values_in[],
        unsigned long numberOfCalculations_in,
        double* results_out,
        double* trustedMinResults_out,
        double* trustedMaxResults_out,
        int* errorTypes_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
bool(*pacevalLibrary_fGetComputationResultExt)(PACEVAL_HANDLE handle_pacevalComputation_in,
        float values_in[],
        unsigned long numberOfCalculations_in,
        float* results_out,
        float* trustedMinResults_out,
        float* trustedMaxResults_out,
        int* errorTypes_out);
#else
/**
 * Foreign function interface (FFI) version of paceval_fGetComputationResultExt() (Windows):
 * performs multiple calculations with precision float in parallel on a single paceval_cComputation with the variables declared by pacevalLibrary_CreateComputation() and with multiple sets of values for those variables - the return value indicates paceval_cComputation object errors and you should check the array errorTypes_out in this case
 * @param values_in array of float defining the multiple values of the variables
 * @param numberOfCalculations_in specifies the number of different calculations you want to run and this number specifies the size of the array values_in, e.g. if the number of variables declared is 50 and the number of calculations is 1000 the size of the array values_in must be 50*1000 (the order of the array values_in must be variable values for the first calculation, then variable values for the second calculation and so on)
 * @param results_out pointer to an array for the results of the computation with the multiple values of the variables (annotation: in case of an error the values are not specified)
 * @param trustedMinResults_out pointer to an array for the minimum/lower interval limits (annotation: in case of an error the values are not specified)
 * @param trustedMaxResults_out pointer to an array for the maximum/upper interval limits (annotation: in case of an error the values are not specified)
 * @param errorTypes_out pointer to an array of the paceval_cComputation object errors, see also paceval_eErrorTypes or pacevalLibrary_GetErrorInformation()
 */
extern "C" bool pacevalLibrary_fGetComputationResultExt(PACEVAL_HANDLE handle_pacevalComputation_in,
        float values_in[],
        unsigned long numberOfCalculations_in,
        float* results_out,
        float* trustedMinResults_out,
        float* trustedMaxResults_out,
        int* errorTypes_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
bool(*pacevalLibrary_ldGetMultipleComputationsResults)(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        long double values_in[],
        long double* results_out,
        long double* trustedMinResults_out,
        long double* trustedMaxResults_out,
        int* errorTypes_out);
#else
/**
 * Foreign function interface (FFI) version of paceval_ldGetMultipleComputationsResults() (Windows):
 * performs multiple calculations with precision long double in parallel on multiple paceval_cComputation objects using the variables declared by pacevalLibrary_CreateComputation() and with the same set of values for these variables - the return value indicates paceval_cComputation object errors and you should check the array errorTypes_out in this case
 * @param handle_pacevalComputations_in array of the paceval_cComputation objects
 * @param numberOfpacevalComputations_in specifies the number of the paceval_cComputation objects
 * @param values_in array of long double defining the values of the variables
 * @param results_out pointer to an array for the results of the multiple computations (annotation: in case of an error the values are not specified)
 * @param trustedMinResults_out pointer to an array for the minimum/lower interval limits (annotation: in case of an error the values are not specified)
 * @param trustedMaxResults_out pointer to an array for the maximum/upper interval limits (annotation: in case of an error the values are not specified)
 * @param errorTypes_out pointer to an array of the paceval_cComputation object errors, see also paceval_eErrorTypes or pacevalLibrary_GetErrorInformation()
 */
extern "C" bool pacevalLibrary_ldGetMultipleComputationsResults(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        long double values_in[],
        long double* results_out,
        long double* trustedMinResults_out,
        long double* trustedMaxResults_out,
        int* errorTypes_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
bool(*pacevalLibrary_dGetMultipleComputationsResults)(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        double values_in[],
        double* results_out,
        double* trustedMinResults_out,
        double* trustedMaxResults_out,
        int* errorTypes_out);
#else
/**
 * Foreign function interface (FFI) version of paceval_dGetMultipleComputationsResults() (Windows):
 * performs multiple calculations with precision double in parallel on multiple paceval_cComputation objects using the variables declared by pacevalLibrary_CreateComputation() and with the same set of values for these variables - the return value indicates paceval_cComputation object errors and you should check the array errorTypes_out in this case
 * @param handle_pacevalComputations_in array of the paceval_cComputation objects
 * @param numberOfpacevalComputations_in specifies the number of the paceval_cComputation objects
 * @param values_in array of double defining the values of the variables
 * @param results_out pointer to an array for the results of the multiple computations (annotation: in case of an error the values are not specified)
 * @param trustedMinResults_out pointer to an array for the minimum/lower interval limits (annotation: in case of an error the values are not specified)
 * @param trustedMaxResults_out pointer to an array for the maximum/upper interval limits (annotation: in case of an error the values are not specified)
 * @param errorTypes_out pointer to an array of the paceval_cComputation object errors, see also paceval_eErrorTypes or pacevalLibrary_GetErrorInformation()
 */
extern "C" bool pacevalLibrary_dGetMultipleComputationsResults(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        double values_in[],
        double* results_out,
        double* trustedMinResults_out,
        double* trustedMaxResults_out,
        int* errorTypes_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
bool(*pacevalLibrary_fGetMultipleComputationsResults)(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        float values_in[],
        float* results_out,
        float* trustedMinResults_out,
        float* trustedMaxResults_out,
        int* errorTypes_out);
#else
/**
 * Foreign function interface (FFI) version of paceval_fGetMultipleComputationsResults() (Windows):
 * performs multiple calculations with precision float in parallel on multiple paceval_cComputation objects using the variables declared by pacevalLibrary_CreateComputation() and with the same set of values for these variables - the return value indicates paceval_cComputation object errors and you should check the array errorTypes_out in this case
 * @param handle_pacevalComputations_in array of the paceval_cComputation objects
 * @param numberOfpacevalComputations_in specifies the number of the paceval_cComputation objects
 * @param values_in array of float defining the values of the variables
 * @param results_out pointer to an array for the results of the multiple computations (annotation: in case of an error the values are not specified)
 * @param trustedMinResults_out pointer to an array for the minimum/lower interval limits (annotation: in case of an error the values are not specified)
 * @param trustedMaxResults_out pointer to an array for the maximum/upper interval limits (annotation: in case of an error the values are not specified)
 * @param errorTypes_out pointer to an array of the paceval_cComputation object errors, see also paceval_eErrorTypes or pacevalLibrary_GetErrorInformation()
 */
extern "C" bool pacevalLibrary_fGetMultipleComputationsResults(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        float values_in[],
        float* results_out,
        float* trustedMinResults_out,
        float* trustedMaxResults_out,
        int* errorTypes_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
bool(*pacevalLibrary_ldGetMultipleComputationsResultsExt)(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        long double values_in[],
        unsigned long numberOfCalculations_in,
        long double* results_out,
        long double* trustedMinResults_out,
        long double* trustedMaxResults_out,
        int* errorTypes_out);
#else
/**
 * Foreign function interface (FFI) version of paceval_ldGetMultipleComputationsResultsExt() (Windows):
 * performs multiple calculations with precision long double in parallel on multiple paceval_cComputation objects using the variables declared by pacevalLibrary_CreateComputation() and with multiple sets of values for those variables - the return value indicates paceval_cComputation object errors and you should check the array errorTypes_out in this case
 * @param handle_pacevalComputations_in array of the paceval_cComputation objects
 * @param numberOfpacevalComputations_in specifies the number of the paceval_cComputation objects
 * @param values_in array of long double defining the values of the variables
 * @param numberOfCalculations_in specifies the number of different calculations you want to run and this number specifies the size of the array values_in, e.g. if the number of variables declared is 50 and the number of calculations is 1000 the size of the array values_in must be 50*1000 (the order of the array values_in must be variable values for the first calculation, then variable values for the second calculation and so on)
 * @param results_out pointer to an array for the results of the multiple computations (annotation: in case of an error the values are not specified)
 * @param trustedMinResults_out pointer to an array for the minimum/lower interval limits (annotation: in case of an error the values are not specified)
 * @param trustedMaxResults_out pointer to an array for the maximum/upper interval limits (annotation: in case of an error the values are not specified)
 * @param errorTypes_out pointer to an array of the paceval_cComputation object errors, see also paceval_eErrorTypes or pacevalLibrary_GetErrorInformation()
 */
extern "C" bool pacevalLibrary_ldGetMultipleComputationsResultsExt(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        long double values_in[],
        unsigned long numberOfCalculations_in,
        long double* results_out,
        long double* trustedMinResults_out,
        long double* trustedMaxResults_out,
        int* errorTypes_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
bool(*pacevalLibrary_dGetMultipleComputationsResultsExt)(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        double values_in[],
        unsigned long numberOfCalculations_in,
        double* results_out,
        double* trustedMinResults_out,
        double* trustedMaxResults_out,
        int* errorTypes_out);
#else
/**
 * Foreign function interface (FFI) version of paceval_dGetMultipleComputationsResultsExt() (Windows):
 * performs multiple calculations with precision double in parallel on multiple paceval_cComputation objects using the variables declared by pacevalLibrary_CreateComputation() and with multiple sets of values for those variables - the return value indicates paceval_cComputation object errors and you should check the array errorTypes_out in this case
 * @param handle_pacevalComputations_in array of the paceval_cComputation objects
 * @param numberOfpacevalComputations_in specifies the number of the paceval_cComputation objects
 * @param values_in array of double defining the values of the variables
 * @param numberOfCalculations_in specifies the number of different calculations you want to run and this number specifies the size of the array values_in, e.g. if the number of variables declared is 50 and the number of calculations is 1000 the size of the array values_in must be 50*1000 (the order of the array values_in must be variable values for the first calculation, then variable values for the second calculation and so on)
 * @param results_out pointer to an array for the results of the multiple computations (annotation: in case of an error the values are not specified)
 * @param trustedMinResults_out pointer to an array for the minimum/lower interval limits (annotation: in case of an error the values are not specified)
 * @param trustedMaxResults_out pointer to an array for the maximum/upper interval limits (annotation: in case of an error the values are not specified)
 * @param errorTypes_out pointer to an array of the paceval_cComputation object errors, see also paceval_eErrorTypes or pacevalLibrary_GetErrorInformation()
 */
extern "C" bool pacevalLibrary_dGetMultipleComputationsResultsExt(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        double values_in[],
        unsigned long numberOfCalculations_in,
        double* results_out,
        double* trustedMinResults_out,
        double* trustedMaxResults_out,
        int* errorTypes_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
bool(*pacevalLibrary_fGetMultipleComputationsResultsExt)(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        float values_in[],
        unsigned long numberOfCalculations_in,
        float* results_out,
        float* trustedMinResults_out,
        float* trustedMaxResults_out,
        int* errorTypes_out);
#else
/**
 * Foreign function interface (FFI) version of paceval_fGetMultipleComputationsResultsExt() (Windows):
 * performs multiple calculations with precision float in parallel on multiple paceval_cComputation objects using the variables declared by pacevalLibrary_CreateComputation() and with multiple sets of values for those variables - the return value indicates paceval_cComputation object errors and you should check the array errorTypes_out in this case
 * @param handle_pacevalComputations_in array of the paceval_cComputation objects
 * @param numberOfpacevalComputations_in specifies the number of the paceval_cComputation objects
 * @param values_in array of float defining the values of the variables
 * @param numberOfCalculations_in specifies the number of different calculations you want to run and this number specifies the size of the array values_in, e.g. if the number of variables declared is 50 and the number of calculations is 1000 the size of the array values_in must be 50*1000 (the order of the array values_in must be variable values for the first calculation, then variable values for the second calculation and so on)
 * @param results_out pointer to an array for the results of the multiple computations (annotation: in case of an error the values are not specified)
 * @param trustedMinResults_out pointer to an array for the minimum/lower interval limits (annotation: in case of an error the values are not specified)
 * @param trustedMaxResults_out pointer to an array for the maximum/upper interval limits (annotation: in case of an error the values are not specified)
 * @param errorTypes_out pointer to an array of the paceval_cComputation object errors, see also paceval_eErrorTypes or pacevalLibrary_GetErrorInformation()
 */
extern "C" bool pacevalLibrary_fGetMultipleComputationsResultsExt(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        float values_in[],
        unsigned long numberOfCalculations_in,
        float* results_out,
        float* trustedMinResults_out,
        float* trustedMaxResults_out,
        int* errorTypes_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
bool (*pacevalLibrary_GetIsError)(PACEVAL_HANDLE handle_pacevalComputation_in);
#else
/**
 * Foreign function interface (FFI) version of paceval_GetIsError() (Windows):
 * determines whether an error has occurred and to get more information about the error, call pacevalLibrary_GetErrorInformation() - if an error has occurred, the return value is TRUE, otherwise it is FALSE
 * @param handle_pacevalComputation_in identifies the paceval_cComputation object
 */
extern "C" bool pacevalLibrary_GetIsError(PACEVAL_HANDLE handle_pacevalComputation_in);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
int (*pacevalLibrary_GetErrorInformation)(PACEVAL_HANDLE handle_pacevalComputation_in,
        char* lastError_strOperator_out,
        long* lastError_ePosition_out);
#else
/**
 * Foreign function interface (FFI) version of paceval_GetErrorInformation() (Windows):
 * returns the paceval_cComputation object error type value: possible errors are analysis and computation errors (errors during the analysis should be checked after creation of the object like pacevalLibrary_CreateComputation() while errors during the computation should be checked after a calculation, e.g. pacevalLibrary_GetComputationResult()) - the return value is the paceval_cComputation object error, see also paceval_eErrorTypes and you can retrieve further information for the error type via pacevalLibrary_CreateErrorInformationText(), e.g. to present this to the user:
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
 * @param handle_pacevalComputation_in identifies the paceval_cComputation object
 * @param lastError_strOperator_out buffer to get the operator causing the error (annotation: maximum size of the retrieved null-terminated string is 255 per "#define PACEVAL_MAXERR 255", see paceval_main.h)
 * @param lastError_ePosition_out position in the function where the error occurred
 */
extern "C" int pacevalLibrary_GetErrorInformation(PACEVAL_HANDLE handle_pacevalComputation_in,
        char* lastError_strOperator_out,
        long* lastError_ePosition_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
int (*pacevalLibrary_CreateErrorInformationText)(PACEVAL_HANDLE handle_pacevalComputation_in,
        char* lastError_strMessage_out,
        char* lastError_strDetails_out);
#else
/**
 * Foreign function interface (FFI) version of paceval_CreateErrorInformationText() (Windows):
 * a helper function to create error information in text from a paceval_cComputation and it can be used to provide more information to the user - the return value is maximum length of lastError_strMessage_out and lastError_strDetails_out
 * @param handle_pacevalComputation_in identifies the paceval_cComputation object
 * @param lastError_strMessage_out buffer to get message describing the error (annotation: maximum size of the retrieved null-terminated string is 255 per "#define PACEVAL_MAXERR 255", see paceval_main.h)
 * @param lastError_strDetails_out buffer to get details like error type as a number, the operator and the position in the function (annotation: maximum size of the retrieved null-terminated string is 255 per "#define PACEVAL_MAXERR 255", see paceval_main.h)
 */
extern "C" int pacevalLibrary_CreateErrorInformationText(PACEVAL_HANDLE handle_pacevalComputation_in,
        char* lastError_strMessage_out,
        char* lastError_strDetails_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
int (*pacevalLibrary_GetErrorTypeMessage)(int errorType_in,
        char* errorType_strMessage_out);
#else
/**
 * Foreign function interface (FFI) version of paceval_GetErrorTypeMessage() (Windows):
 * a helper function to create an error message in text from an error type and It can be used to provide more information to the user - the return value is the length of lastError_strMessage_out
 * @param errorType_in specifies the the error type value
 * @param errorType_strMessage_out buffer to get message describing the error (annotation: maximum size of the retrieved null-terminated string is 255 per "#define PACEVAL_MAXERR 255", see paceval_main.h)
 */
extern "C" int pacevalLibrary_GetErrorTypeMessage(int errorType_in,
        char* errorType_strMessage_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
int (*pacevalLibrary_GetComputationVersionString)(PACEVAL_HANDLE handle_pacevalComputation_in,
        char* paceval_strVersion_out);
#else
/**
 * Foreign function interface (FFI) version of paceval_GetComputationVersionString() (Windows):
 * returns the version string including the version number of the paceval_cComputation object - the return value is the length of the version string
 * @param handle_pacevalComputation_in identifies the paceval_cComputation object
 * @param paceval_strVersion_out points to the buffer that will receive the string (set paceval_strVersion_in to NULL to receive the length of the version string)
 */
extern "C" int pacevalLibrary_GetComputationVersionString(PACEVAL_HANDLE handle_pacevalComputation_in,
        char* paceval_strVersion_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
bool (*pacevalLibrary_SetCallbackUserFunction)(unsigned int numberUserFunction_in,
        const char* singleFunctionString_in,
        paceval_callbackUserFunctionType* paceval_callbackUserFunction_in);
#else
/**
 * Foreign function interface (FFI) version of paceval_SetCallbackUserFunction() (Windows):
 * allows the definition of up to 1000 custom user functions. Depending on your requirements, you could a) add mathematical functions that enable new functions or b) add faster mathematical functions that are not as accurate as those used by paceval - if the function succeeds, the return value is TRUE, otherwise it is FALSE
 * @param numberUserFunction_in specifies the number of the user function to set the single function for, e.g. 1
 * @param singleFunctionString_in points to a null-terminated string specifying the user-defined single function, e.g. "my_function1"
 * @param paceval_callbackUserFunction_in a user-defined callback function to handle the computation for the specific single function, see paceval_main.h
 */
extern "C" bool pacevalLibrary_SetCallbackUserFunction(unsigned int numberUserFunction_in,
        const char* singleFunctionString_in,
        paceval_callbackUserFunctionType* paceval_callbackUserFunction_in);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
unsigned long (*pacevalLibrary_CreateXMLFromParameters)(char* paceval_strXML_out,
        const char* functionString_in,
        unsigned long numberOfVariables_in,
        const char* variables_in,
        const char* valuesString_in,
        bool useInterval_in);
#else
/**
 * Foreign function interface (FFI) version of paceval_CreateXMLFromParameters() (Windows):
 * a helper function to create XML data representing a paceval_cComputation object and you can use it to store data representing a computation to a file system or to transmit it via a network or channel - the return value is the size of the XML data (in case of an error the return value is 0)
 * @param paceval_strXML_out pointer to a buffer for the XML data (set paceval_strXML_out to NULL to receive the length of the version string)
 * @param functionString_in points to a null-terminated string representing the function
 * @param numberOfVariables_in specifies the number of variables
 * @param variables_in points to a null-terminated string specifying the names of the variables in one string seperated by blanks
 * @param valuesString_in specifies the values for the variables in one string seperated by semicolons (;)
 * @param useInterval_in specifies whether Trusted Interval Computation is enabled or not
 */
extern "C" unsigned long pacevalLibrary_CreateXMLFromParameters(char* paceval_strXML_out,
        const char* functionString_in,
        unsigned long numberOfVariables_in,
        const char* variables_in,
        const char* valuesString_in,
        bool useInterval_in);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
int (*pacevalLibrary_ReadParametersFromXML)(const char* paceval_strXML_in,
        unsigned long* functionStringLength_out,
        unsigned long* variablesStringLength_out,
        unsigned long* numberOfVariables_out,
        unsigned long* valuesStringLength_out,
        char* functionString_out,
        char* variables_out,
        char* valuesString_out,
        bool* useInterval_out);
#else
/**
 * Foreign function interface (FFI) version of paceval_ReadParametersFromXML() (Windows):
 * a helper function to read XML data representing a paceval_cComputation object and you can use it to read data representing a computation from a file system or to receive it via a network or channel - in case of an error the return value is <0
 * @param paceval_strXML_in pointer to the XML data
 * @param functionStringLength_out the length of the function string
 * @param variablesStringLength_out the length of the variable names in one string
 * @param numberOfVariables_out the number of variables
 * @param valuesStringLength_out the length of the values seperated by blanks in one string
 * @param functionString_out points to the buffer for the function string (set functionString_out to NULL to receive the length at first with functionStringLength_out)
 * @param variables_out points to the buffer for the variable names in one string (set variables_out to NULL to receive the length at first with variablesStringLength_out)
 * @param valuesString_out points to the buffer for the values seperated by semicolons (;) in one string (set valuesString_out to NULL to receive the length at first with valuesStringLength_out)
 * @param useInterval_out points to the buffer specifying whether Trusted Interval Computation is enabled or not
 */
extern "C" int pacevalLibrary_ReadParametersFromXML(const char* paceval_strXML_in,
        unsigned long* functionStringLength_out,
        unsigned long* variablesStringLength_out,
        unsigned long* numberOfVariables_out,
        unsigned long* valuesStringLength_out,
        char* functionString_out,
        char* variables_out,
        char* valuesString_out,
        bool* useInterval_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
unsigned long (*pacevalLibrary_GetComputationInformationXML)(PACEVAL_HANDLE handle_pacevalComputation_in,
        char* paceval_strXML_out);
#else
/**
 * Foreign function interface (FFI) version of paceval_GetComputationInformationXML() (Windows):
 * a helper function for getting data from a paceval_cComputation object, such as the number of cores in the system, the number of threads used or the cache hits in the computations with that particular paceval_cComputation object - the return value is the size of the XML data (in case of an error the return value is 0)
 * @param handle_pacevalComputation_in identifies the paceval_cComputation object
 * @param paceval_strXML_out pointer to a buffer for the XML data (set paceval_strXML_out to NULL to receive the length of the version string)
 */
extern "C" unsigned long pacevalLibrary_GetComputationInformationXML(PACEVAL_HANDLE handle_pacevalComputation_in,
        char* paceval_strXML_out);
#endif //defined(paceval_use_dll)

extern "C" bool paceval_InitializeLibrary(const char* initString_in)
{
#if defined(paceval_use_dll) && (paceval_use_dll == 1)
#ifdef UNICODE
#if !defined(_WIN64)
    handle_paceval_DLL = LoadLibrary((LPCWSTR)L"paceval_win32.dll");
    if ((unsigned)handle_paceval_DLL <= HINSTANCE_ERROR)
    {
#else
    handle_paceval_DLL = LoadLibrary((LPCWSTR)L"paceval_win64i.dll");
    if (handle_paceval_DLL == NULL)
    {
        paceval_WIN64_i = false;
        handle_paceval_DLL = LoadLibrary((LPCWSTR)L"paceval_win64.dll");
    }
    if (handle_paceval_DLL == NULL)
    {
#endif //#if !defined(_WIN64)
#else
#if !defined(_WIN64)
    handle_paceval_DLL = LoadLibrary("paceval_win32.dll");
    if((unsigned)handle_paceval_DLL <= HINSTANCE_ERROR)
    {
#else
    handle_paceval_DLL = LoadLibrary("paceval_win64i.dll");
    if (handle_paceval_DLL == NULL)
    {
        paceval_WIN64_i = false;
        handle_paceval_DLL = LoadLibrary("paceval_win64.dll");
    }
    if (handle_paceval_DLL == NULL)
    {
#endif //#if !defined(_WIN64)
#endif //#if defined(UNICODE)
#ifdef UNICODE
#if !defined(_WIN64)
        MessageBox(NULL, (LPCWSTR)L"'paceval_win32.dll' not found", (LPCWSTR)L"Library Error", MB_OK | MB_ICONERROR);
#else
        MessageBox(NULL, (LPCWSTR)L"neither 'paceval_win64i.dll' nor 'paceval_win64.dll' was found", (LPCWSTR)L"Library Error", MB_OK | MB_ICONERROR);
#endif //#if !defined(_WIN64)
#else
#if !defined(_WIN64)
        MessageBox(NULL, "'paceval_win32.dll' not found", "Library Error", MB_OK | MB_ICONERROR);
#else
        MessageBox(NULL, "neither 'paceval_win64i.dll' nor 'paceval_win64.dll' was found", "Library Error", MB_OK | MB_ICONERROR);
#endif //#if !defined(_WIN64)
#endif //#if defined(UNICODE)
        return false;
    }

    pacevalLibrary_Initialize = (bool(*)(const char *))
                                GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_Initialize");
    if (pacevalLibrary_Initialize == NULL)
        pacevalLibrary_Initialize = (bool(*)(const char *))
                                    GetProcAddress(handle_paceval_DLL, "pacevalLibrary_Initialize");

    pacevalLibrary_Free = (bool(*)())
                          GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_Free");
    if (pacevalLibrary_Free == NULL)
        pacevalLibrary_Free = (bool(*)())
                              GetProcAddress(handle_paceval_DLL, "pacevalLibrary_Free");

    pacevalLibrary_CreateComputation = (void*(*)(const char *, unsigned long, const char *, bool, bool (*)(const void *, const paceval_eStatusTypes, const int)))
                                       GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_CreateComputation");
    if (pacevalLibrary_CreateComputation == NULL)
        pacevalLibrary_CreateComputation = (void*(*)(const char *, unsigned long, const char *, bool, bool(*)(const void *, const paceval_eStatusTypes, const int)))
                                           GetProcAddress(handle_paceval_DLL, "pacevalLibrary_CreateComputation");
    pacevalLibrary_CreateMultipleComputations = (bool(*)(void **,const char **, unsigned long, unsigned long, const char *, bool, bool (*)(const void *, const paceval_eStatusTypes, const int)))
            GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_CreateMultipleComputations");
    if (pacevalLibrary_CreateMultipleComputations == NULL)
        pacevalLibrary_CreateMultipleComputations = (bool(*)(void **,const char **, unsigned long, unsigned long, const char *, bool, bool (*)(const void *, const paceval_eStatusTypes, const int)))
                GetProcAddress(handle_paceval_DLL, "pacevalLibrary_CreateMultipleComputations");

    pacevalLibrary_ExistComputation = (bool(*)(void *))
                                      GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_ExistComputation");
    if (pacevalLibrary_ExistComputation == NULL)
        pacevalLibrary_ExistComputation = (bool(*)(void *))
                                          GetProcAddress(handle_paceval_DLL, "pacevalLibrary_ExistComputation");

    pacevalLibrary_DeleteComputation = (bool(*)(void *))
                                       GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_DeleteComputation");
    if (pacevalLibrary_DeleteComputation == NULL)
        pacevalLibrary_DeleteComputation = (bool(*)(void *))
                                           GetProcAddress(handle_paceval_DLL, "pacevalLibrary_DeleteComputation");

    pacevalLibrary_ldConvertFloatToString = (int(*)(char *, long double))
                                            GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_ldConvertFloatToString");
    if (pacevalLibrary_ldConvertFloatToString == NULL)
        pacevalLibrary_ldConvertFloatToString = (int(*)(char *, long double))
                                                GetProcAddress(handle_paceval_DLL, "pacevalLibrary_ldConvertFloatToString");
    pacevalLibrary_dConvertFloatToString = (int(*)(char *, double))
                                           GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_dConvertFloatToString");
    if (pacevalLibrary_dConvertFloatToString == NULL)
        pacevalLibrary_dConvertFloatToString = (int(*)(char *, double))
                                               GetProcAddress(handle_paceval_DLL, "pacevalLibrary_dConvertFloatToString");
    pacevalLibrary_fConvertFloatToString = (int(*)(char *, float))
                                           GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_fConvertFloatToString");
    if (pacevalLibrary_fConvertFloatToString == NULL)
        pacevalLibrary_fConvertFloatToString = (int(*)(char *, float))
                                               GetProcAddress(handle_paceval_DLL, "pacevalLibrary_fConvertFloatToString");

    pacevalLibrary_ldConvertStringToFloat = (long double(*)(const char *, int *, long *, bool, long double *, long double *))
                                            GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_ldConvertStringToFloat");
    if (pacevalLibrary_ldConvertStringToFloat == NULL)
        pacevalLibrary_ldConvertStringToFloat = (long double(*)(const char *, int *, long *, bool, long double *, long double *))
                                                GetProcAddress(handle_paceval_DLL, "pacevalLibrary_ldConvertStringToFloat");
    pacevalLibrary_dConvertStringToFloat = (double(*)(const char *, int *, long *, bool, double *, double *))
                                           GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_dConvertStringToFloat");
    if (pacevalLibrary_dConvertStringToFloat == NULL)
        pacevalLibrary_dConvertStringToFloat = (double(*)(const char *, int *, long *, bool, double *, double *))
                                               GetProcAddress(handle_paceval_DLL, "pacevalLibrary_dConvertStringToFloat");
    pacevalLibrary_fConvertStringToFloat = (float(*)(const char *, int *, long *, bool, float *, float *))
                                           GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_fConvertStringToFloat");
    if (pacevalLibrary_fConvertStringToFloat == NULL)
        pacevalLibrary_fConvertStringToFloat = (float(*)(const char *, int *, long *, bool, float *, float *))
                                               GetProcAddress(handle_paceval_DLL, "pacevalLibrary_fConvertStringToFloat");

    pacevalLibrary_ldmathv = (long double(*)(void * *, int *, const char *, unsigned long, const char *, long double *))
                             GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_ldmathv");
    if (pacevalLibrary_ldmathv == NULL)
        pacevalLibrary_ldmathv = (long double(*)(void * *, int *, const char *, unsigned long, const char *, long double *))
                                 GetProcAddress(handle_paceval_DLL, "pacevalLibrary_ldmathv");
    pacevalLibrary_dmathv = (double(*)(void * *, int *, const char *, unsigned long, const char *, double *))
                            GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_dmathv");
    if (pacevalLibrary_dmathv == NULL)
        pacevalLibrary_dmathv = (double(*)(void * *, int *, const char *, unsigned long, const char *, double *))
                                GetProcAddress(handle_paceval_DLL, "pacevalLibrary_dmathv");
    pacevalLibrary_fmathv = (float(*)(void * *, int *, const char *, unsigned long, const char *, float *))
                            GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_fmathv");
    if (pacevalLibrary_fmathv == NULL)
        pacevalLibrary_fmathv = (float(*)(void * *, int *, const char *, unsigned long, const char *, float *))
                                GetProcAddress(handle_paceval_DLL, "pacevalLibrary_fmathv");

    pacevalLibrary_ldmathvi = (long double(*)(void * *, int *, long double *, long double *, const char *, unsigned long, const char *, long double *))
                              GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_ldmathvi");
    if (pacevalLibrary_ldmathvi == NULL)
        pacevalLibrary_ldmathvi = (long double(*)(void * *, int *, long double *, long double *, const char *, unsigned long, const char *, long double *))
                                  GetProcAddress(handle_paceval_DLL, "pacevalLibrary_ldmathvi");
    pacevalLibrary_dmathvi = (double(*)(void * *, int *, double *, double *, const char *, unsigned long, const char *, double *))
                             GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_dmathvi");
    if (pacevalLibrary_dmathvi == NULL)
        pacevalLibrary_dmathvi = (double(*)(void * *, int *, double *, double *, const char *, unsigned long, const char *, double *))
                                 GetProcAddress(handle_paceval_DLL, "pacevalLibrary_dmathvi");
    pacevalLibrary_fmathvi = (float(*)(void * *, int *, float *, float *, const char *, unsigned long, const char *, float *))
                             GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_fmathvi");
    if (pacevalLibrary_fmathvi == NULL)
        pacevalLibrary_fmathvi = (float(*)(void * *, int *, float *, float *, const char *, unsigned long, const char *, float *))
                                 GetProcAddress(handle_paceval_DLL, "pacevalLibrary_fmathvi");

    pacevalLibrary_ldGetComputationResult = (long double(*)(void *, long double *, long double *, long double *))
                                            GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_ldGetComputationResult");
    if (pacevalLibrary_ldGetComputationResult == NULL)
        pacevalLibrary_ldGetComputationResult = (long double(*)(void *, long double *, long double *, long double *))
                                                GetProcAddress(handle_paceval_DLL, "pacevalLibrary_ldGetComputationResult");
    pacevalLibrary_dGetComputationResult = (double(*)(void *, double *, double *, double *))
                                           GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_dGetComputationResult");
    if (pacevalLibrary_dGetComputationResult == NULL)
        pacevalLibrary_dGetComputationResult = (double(*)(void *, double *, double *, double *))
                                               GetProcAddress(handle_paceval_DLL, "pacevalLibrary_dGetComputationResult");
    pacevalLibrary_fGetComputationResult = (float(*)(void *, float *, float *, float *))
                                           GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_fGetComputationResult");
    if (pacevalLibrary_fGetComputationResult == NULL)
        pacevalLibrary_fGetComputationResult = (float(*)(void *, float *, float *, float *))
                                               GetProcAddress(handle_paceval_DLL, "pacevalLibrary_fGetComputationResult");

    pacevalLibrary_ldGetComputationResultExt = (bool(*)(void *, long double *, unsigned long, long double *, long double *, long double *, int *))
            GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_ldGetComputationResultExt");
    if (pacevalLibrary_ldGetComputationResultExt == NULL)
        pacevalLibrary_ldGetComputationResultExt = (bool(*)(void *, long double *, unsigned long, long double *, long double *, long double *, int *))
                GetProcAddress(handle_paceval_DLL, "pacevalLibrary_ldGetComputationResultExt");
    pacevalLibrary_dGetComputationResultExt = (bool(*)(void *, double *, unsigned long, double *, double *, double *, int *))
            GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_dGetComputationResultExt");
    if (pacevalLibrary_dGetComputationResultExt == NULL)
        pacevalLibrary_dGetComputationResultExt = (bool(*)(void *, double *, unsigned long, double *, double *, double *, int *))
                GetProcAddress(handle_paceval_DLL, "pacevalLibrary_dGetComputationResultExt");
    pacevalLibrary_fGetComputationResultExt = (bool(*)(void *, float *, unsigned long, float *, float *, float *, int *))
            GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_fGetComputationResultExt");
    if (pacevalLibrary_fGetComputationResultExt == NULL)
        pacevalLibrary_fGetComputationResultExt = (bool(*)(void *, float *, unsigned long, float *, float *, float *, int *))
                GetProcAddress(handle_paceval_DLL, "pacevalLibrary_fGetComputationResultExt");

    pacevalLibrary_ldGetMultipleComputationsResults = (bool(*)(void * *, unsigned long, long double *, long double *, long double *, long double *, int *))
            GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_ldGetMultipleComputationsResults");
    if (pacevalLibrary_ldGetMultipleComputationsResults == NULL)
        pacevalLibrary_ldGetMultipleComputationsResults = (bool(*)(void * *, unsigned long, long double *, long double *, long double *, long double *, int *))
                GetProcAddress(handle_paceval_DLL, "pacevalLibrary_ldGetMultipleComputationsResults");
    pacevalLibrary_dGetMultipleComputationsResults = (bool(*)(void * *, unsigned long, double *, double *, double *, double *, int *))
            GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_dGetMultipleComputationsResults");
    if (pacevalLibrary_dGetMultipleComputationsResults == NULL)
        pacevalLibrary_dGetMultipleComputationsResults = (bool(*)(void * *, unsigned long, double *, double *, double *, double *, int *))
                GetProcAddress(handle_paceval_DLL, "pacevalLibrary_dGetMultipleComputationsResults");
    pacevalLibrary_fGetMultipleComputationsResults = (bool(*)(void * *, unsigned long, float *, float *, float *, float *, int *))
            GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_fGetMultipleComputationsResults");
    if (pacevalLibrary_fGetMultipleComputationsResults == NULL)
        pacevalLibrary_fGetMultipleComputationsResults = (bool(*)(void * *, unsigned long, float *, float *, float *, float *, int *))
                GetProcAddress(handle_paceval_DLL, "pacevalLibrary_fGetMultipleComputationsResults");

    pacevalLibrary_ldGetMultipleComputationsResultsExt = (bool(*)(void * *, unsigned long, long double *, unsigned long, long double *, long double *, long double *, int *))
            GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_ldGetMultipleComputationsResultsExt");
    if (pacevalLibrary_ldGetMultipleComputationsResultsExt == NULL)
        pacevalLibrary_ldGetMultipleComputationsResultsExt = (bool(*)(void * *, unsigned long, long double *, unsigned long, long double *, long double *, long double *, int *))
                GetProcAddress(handle_paceval_DLL, "pacevalLibrary_ldGetMultipleComputationsResultsExt");
    pacevalLibrary_dGetMultipleComputationsResultsExt = (bool(*)(void * *, unsigned long, double *, unsigned long, double *, double *, double *, int *))
            GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_dGetMultipleComputationsResultsExt");
    if (pacevalLibrary_dGetMultipleComputationsResultsExt == NULL)
        pacevalLibrary_dGetMultipleComputationsResultsExt = (bool(*)(void * *, unsigned long, double *, unsigned long, double *, double *, double *, int *))
                GetProcAddress(handle_paceval_DLL, "pacevalLibrary_dGetMultipleComputationsResultsExt");
    pacevalLibrary_fGetMultipleComputationsResultsExt = (bool(*)(void * *, unsigned long, float *, unsigned long, float *, float *, float *, int *))
            GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_fGetMultipleComputationsResultsExt");
    if (pacevalLibrary_fGetMultipleComputationsResultsExt == NULL)
        pacevalLibrary_fGetMultipleComputationsResultsExt = (bool(*)(void * *, unsigned long, float *, unsigned long, float *, float *, float *, int *))
                GetProcAddress(handle_paceval_DLL, "pacevalLibrary_fGetMultipleComputationsResultsExt");

    pacevalLibrary_GetIsError = (bool(*)(void *))
                                GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_GetIsError");
    if (pacevalLibrary_GetIsError == NULL)
        pacevalLibrary_GetIsError = (bool(*)(void *))
                                    GetProcAddress(handle_paceval_DLL, "pacevalLibrary_GetIsError");
    pacevalLibrary_GetErrorInformation = (int(*)(void *, char *, long *))
                                         GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_GetErrorInformation");
    if (pacevalLibrary_GetErrorInformation == NULL)
        pacevalLibrary_GetErrorInformation = (int(*)(void *, char *, long *))
                                             GetProcAddress(handle_paceval_DLL, "pacevalLibrary_GetErrorInformation");
    pacevalLibrary_CreateErrorInformationText = (int(*)(void *, char *, char *))
            GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_CreateErrorInformationText");
    if (pacevalLibrary_CreateErrorInformationText == NULL)
        pacevalLibrary_CreateErrorInformationText = (int(*)(void *, char *, char *))
                GetProcAddress(handle_paceval_DLL, "pacevalLibrary_CreateErrorInformationText");
    pacevalLibrary_GetErrorTypeMessage = (int(*)(int, char *))
                                         GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_GetErrorTypeMessage");
    if (pacevalLibrary_GetErrorTypeMessage == NULL)
        pacevalLibrary_GetErrorTypeMessage = (int(*)(int, char *))
                                             GetProcAddress(handle_paceval_DLL, "pacevalLibrary_GetErrorTypeMessage");

    pacevalLibrary_GetComputationVersionString = (int(*)(void *, char *))
            GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_GetComputationVersionString");
    if (pacevalLibrary_GetComputationVersionString == NULL)
        pacevalLibrary_GetComputationVersionString = (int(*)(void *, char *))
                GetProcAddress(handle_paceval_DLL, "pacevalLibrary_GetComputationVersionString");

    pacevalLibrary_SetCallbackUserFunction = (bool(*)(unsigned int, const char *, bool (*)(const int, const long double *, long double *, const double *, double *, const float *, float *)))
            GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_SetCallbackUserFunction");
    if (pacevalLibrary_SetCallbackUserFunction == NULL)
        pacevalLibrary_SetCallbackUserFunction = (bool(*)(unsigned int, const char *, bool(*)(const int, const long double *, long double *, const double *, double *, const float *, float *)))
                GetProcAddress(handle_paceval_DLL, "pacevalLibrary_SetCallbackUserFunction");

    pacevalLibrary_CreateXMLFromParameters = (unsigned long(*)(char *, const char *, unsigned long, const char *, const char *, bool))
            GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_CreateXMLFromParameters");
    if (pacevalLibrary_CreateXMLFromParameters == NULL)
        pacevalLibrary_CreateXMLFromParameters = (unsigned long(*)(char *, const char *, unsigned long, const char *, const char *, bool))
                GetProcAddress(handle_paceval_DLL, "pacevalLibrary_CreateXMLFromParameters");
    pacevalLibrary_ReadParametersFromXML = (int(*)(const char *, unsigned long *, unsigned long *, unsigned long *, unsigned long *, char *, char *, char *, bool *))
                                           GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_ReadParametersFromXML");
    if (pacevalLibrary_ReadParametersFromXML == NULL)
        pacevalLibrary_ReadParametersFromXML = (int(*)(const char *, unsigned long *, unsigned long *, unsigned long *, unsigned long *, char *, char *, char *, bool *))
                                               GetProcAddress(handle_paceval_DLL, "pacevalLibrary_ReadParametersFromXML");

    pacevalLibrary_GetComputationInformationXML = (unsigned long(*)(void *, char *))
            GetProcAddress(handle_paceval_DLL, "_pacevalLibrary_GetComputationInformationXML");
    if (pacevalLibrary_GetComputationInformationXML == NULL)
        pacevalLibrary_GetComputationInformationXML = (unsigned long(*)(void *, char *))
                GetProcAddress(handle_paceval_DLL, "pacevalLibrary_GetComputationInformationXML");

    if ((pacevalLibrary_Initialize == NULL)
            || (pacevalLibrary_Free == NULL)
            || (pacevalLibrary_CreateComputation == NULL)
            || (pacevalLibrary_ExistComputation == NULL)
            || (pacevalLibrary_CreateMultipleComputations == NULL)
            || (pacevalLibrary_DeleteComputation == NULL)
            || (pacevalLibrary_ldConvertFloatToString == NULL)
            || (pacevalLibrary_dConvertFloatToString == NULL)
            || (pacevalLibrary_fConvertFloatToString == NULL)
            || (pacevalLibrary_ldConvertStringToFloat == NULL)
            || (pacevalLibrary_dConvertStringToFloat == NULL)
            || (pacevalLibrary_fConvertStringToFloat == NULL)
            || (pacevalLibrary_ldmathv == NULL)
            || (pacevalLibrary_dmathv == NULL)
            || (pacevalLibrary_fmathv == NULL)
            || (pacevalLibrary_ldmathvi == NULL)
            || (pacevalLibrary_dmathvi == NULL)
            || (pacevalLibrary_fmathvi == NULL)
            || (pacevalLibrary_ldGetComputationResult == NULL)
            || (pacevalLibrary_dGetComputationResult == NULL)
            || (pacevalLibrary_fGetComputationResult == NULL)
            || (pacevalLibrary_ldGetComputationResultExt == NULL)
            || (pacevalLibrary_dGetComputationResultExt == NULL)
            || (pacevalLibrary_fGetComputationResultExt == NULL)
            || (pacevalLibrary_ldGetMultipleComputationsResults == NULL)
            || (pacevalLibrary_dGetMultipleComputationsResults == NULL)
            || (pacevalLibrary_fGetMultipleComputationsResults == NULL)
            || (pacevalLibrary_ldGetMultipleComputationsResultsExt == NULL)
            || (pacevalLibrary_dGetMultipleComputationsResultsExt == NULL)
            || (pacevalLibrary_fGetMultipleComputationsResultsExt == NULL)
            || (pacevalLibrary_GetIsError == NULL)
            || (pacevalLibrary_GetErrorInformation == NULL)
            || (pacevalLibrary_CreateErrorInformationText == NULL)
            || (pacevalLibrary_GetErrorTypeMessage == NULL)
            || (pacevalLibrary_GetComputationVersionString == NULL)
            || (pacevalLibrary_SetCallbackUserFunction == NULL)
            || (pacevalLibrary_CreateXMLFromParameters == NULL)
            || (pacevalLibrary_ReadParametersFromXML == NULL)
            || (pacevalLibrary_GetComputationInformationXML == NULL))
    {
#ifdef UNICODE
#if !defined(_WIN64)
        MessageBox(NULL, (LPCWSTR)L"'paceval_win32.dll' is not correct", (LPCWSTR)L"Library Error", MB_OK | MB_ICONERROR);
#else
        if (paceval_WIN64_i == true)
            MessageBox(NULL, (LPCWSTR)L"'paceval_win64i.dll' is not correct", (LPCWSTR)L"Library Error", MB_OK | MB_ICONERROR);
        else
            MessageBox(NULL, (LPCWSTR)L"'paceval_win64.dll' is not correct", (LPCWSTR)L"Library Error", MB_OK | MB_ICONERROR);
#endif //#if !defined(_WIN64)
#else
#if !defined(_WIN64)
        MessageBox(NULL, "'paceval_win32.dll' is not correct", "Library Error", MB_OK | MB_ICONERROR);
#else
        if (paceval_WIN64_i == true)
            MessageBox(NULL, "'paceval_win64i.dll' is not correct", "Library Error", MB_OK | MB_ICONERROR);
        else
            MessageBox(NULL, "'paceval_win64.dll' is not correct", "Library Error", MB_OK | MB_ICONERROR);
#endif //#if !defined(_WIN64)
#endif //#if defined(UNICODE)
        FreeLibrary(handle_paceval_DLL);
        handle_paceval_DLL = 0;
        return false;
    }
#endif //defined(paceval_use_dll)

    return pacevalLibrary_Initialize(initString_in/*, sizeof(long double)*/);
}

extern "C" bool paceval_FreeLibrary()
{
#if defined(paceval_use_dll) && (paceval_use_dll == 1)
#if !defined(_WIN64)
    if ((unsigned)handle_paceval_DLL > HINSTANCE_ERROR)
#else
    if (handle_paceval_DLL != NULL)
#endif //#if !defined(_WIN64)
    {
        bool retVal;

        retVal = pacevalLibrary_Free();

        FreeLibrary(handle_paceval_DLL);
        handle_paceval_DLL = 0;

        return retVal;
    }
    else
        return false;
#else
    {
        bool retVal;

        retVal = pacevalLibrary_Free();
        return retVal;
    }
#endif //defined(paceval_use_dll)
}

extern "C" PACEVAL_HANDLE paceval_CreateComputation(const char* functionString_in,
        unsigned long numberOfVariables_in,
        const char* variables_in,
        bool useInterval_in,
        paceval_callbackStatusType* paceval_callbackStatus_in)
{
    return pacevalLibrary_CreateComputation(functionString_in,
                                            numberOfVariables_in,
                                            variables_in,
                                            useInterval_in,
                                            paceval_callbackStatus_in);
}

extern "C" bool paceval_CreateMultipleComputations(PACEVAL_HANDLE handle_pacevalComputations_out[],
        const char* functionStrings_in[],
        unsigned long numberOfpacevalComputations_in,
        unsigned long numberOfVariables_in,
        const char* variables_in,
        bool useInterval_in,
        paceval_callbackStatusType* paceval_callbackStatus_in)
{
    return pacevalLibrary_CreateMultipleComputations(handle_pacevalComputations_out,
            functionStrings_in,
            numberOfpacevalComputations_in,
            numberOfVariables_in,
            variables_in,
            useInterval_in,
            paceval_callbackStatus_in);
}

extern "C" bool paceval_ExistComputation(PACEVAL_HANDLE handle_pacevalComputation_in)
{
    return pacevalLibrary_ExistComputation(handle_pacevalComputation_in);
}

extern "C" bool paceval_DeleteComputation(PACEVAL_HANDLE handle_pacevalComputation_in)
{
    return pacevalLibrary_DeleteComputation(handle_pacevalComputation_in);
}

extern "C" int paceval_ldConvertFloatToString(char* destinationString_out,
        long double float_in)
{
    return pacevalLibrary_ldConvertFloatToString(destinationString_out,
            float_in);
}

extern "C" int paceval_dConvertFloatToString(char* destinationString_out,
        double float_in)
{
    return pacevalLibrary_dConvertFloatToString(destinationString_out,
            float_in);
}

extern "C" int paceval_fConvertFloatToString(char* destinationString_out,
        float float_in)
{
    return pacevalLibrary_fConvertFloatToString(destinationString_out,
            float_in);
}

extern "C" long double paceval_ldConvertStringToFloat(const char* sourceString_in,
        int* errorType_out,
        long* errPosition_out,
        bool useInterval_in,
        long double* trustedMinResult_out,
        long double* trustedMaxResult_out)
{
    return pacevalLibrary_ldConvertStringToFloat(sourceString_in,
            errorType_out, errPosition_out,
            useInterval_in, trustedMinResult_out, trustedMaxResult_out);
}

extern "C" double paceval_dConvertStringToFloat(const char* sourceString_in,
        int* errorType_out,
        long* errPosition_out,
        bool useInterval_in,
        double* trustedMinResult_out,
        double* trustedMaxResult_out)
{
    return pacevalLibrary_dConvertStringToFloat(sourceString_in,
            errorType_out, errPosition_out,
            useInterval_in, trustedMinResult_out, trustedMaxResult_out);
}

extern "C" float paceval_fConvertStringToFloat(const char* sourceString_in,
        int* errorType_out,
        long* errPosition,
        bool useInterval_in,
        float* trustedMinResult_out,
        float* trustedMaxResult_out)
{
    return pacevalLibrary_fConvertStringToFloat(sourceString_in,
            errorType_out, errPosition,
            useInterval_in, trustedMinResult_out, trustedMaxResult_out);
}

extern "C" long double paceval_ldmathv(PACEVAL_HANDLE* handle_pacevalComputation_in,
                                       int* errorType_out,
                                       const char* functionString_in,
                                       unsigned long numberOfVariables_in,
                                       const char* variables_in, ...)
{
    long double* valuesVariablesArray;
    va_list argumentList;
    long double ldResult;

    va_start(argumentList, variables_in);
    valuesVariablesArray = new long double[numberOfVariables_in];

    for (unsigned long iCount = 0; iCount < numberOfVariables_in; iCount++)
    {
        valuesVariablesArray[iCount] = va_arg(argumentList, long double);
    }
    va_end(argumentList);

    ldResult = pacevalLibrary_ldmathv(handle_pacevalComputation_in,
                                      errorType_out, functionString_in,
                                      numberOfVariables_in, variables_in,
                                      valuesVariablesArray);

    delete[] valuesVariablesArray;
    return ldResult;
}

extern "C" double paceval_dmathv(PACEVAL_HANDLE* handle_pacevalComputation_in,
                                 int* errorType_out,
                                 const char* functionString_in,
                                 unsigned long numberOfVariables_in,
                                 const char* variables_in, ...)
{
    double* valuesVariablesArray;
    va_list argumentList;
    double dResult;

    va_start(argumentList, variables_in);
    valuesVariablesArray = new double[numberOfVariables_in];

    for (unsigned long iCount = 0; iCount < numberOfVariables_in; iCount++)
    {
        valuesVariablesArray[iCount] = va_arg(argumentList, double);
    }
    va_end(argumentList);

    dResult = pacevalLibrary_dmathv(handle_pacevalComputation_in,
                                    errorType_out, functionString_in,
                                    numberOfVariables_in, variables_in,
                                    valuesVariablesArray);

    delete[] valuesVariablesArray;
    return dResult;
}

extern "C" float paceval_fmathv(PACEVAL_HANDLE* handle_pacevalComputation_in,
                                int* errorType_out,
                                const char* functionString_in,
                                unsigned long numberOfVariables_in,
                                const char* variables_in, ...)
{
    float* valuesVariablesArray;
    va_list argumentList;
    float fResult;

    va_start(argumentList, variables_in);
    valuesVariablesArray = new float[numberOfVariables_in];

    for (unsigned long iCount = 0; iCount < numberOfVariables_in; iCount++)
    {
        valuesVariablesArray[iCount] = va_arg(argumentList, double); //e.g. GNUC:'float' is promoted to 'double' when passed through '...'
    }
    va_end(argumentList);

    fResult = pacevalLibrary_fmathv(handle_pacevalComputation_in,
                                    errorType_out, functionString_in,
                                    numberOfVariables_in, variables_in,
                                    valuesVariablesArray);

    delete[] valuesVariablesArray;
    return fResult;
}

extern "C" long double paceval_ldmathvi(PACEVAL_HANDLE* handle_pacevalComputation_in,
                                        int* errorType_out,
                                        long double* trustedMinResult_out,
                                        long double* trustedMaxResult_out,
                                        const char* functionString_in,
                                        unsigned long numberOfVariables_in,
                                        const char* variables_in, ...)
{
    long double* valuesVariablesArray;
    va_list argumentList;
    long double ldResult;

    va_start(argumentList, variables_in);
    valuesVariablesArray = new long double[numberOfVariables_in];

    for (unsigned long iCount = 0; iCount < numberOfVariables_in; iCount++)
    {
        valuesVariablesArray[iCount] = va_arg(argumentList, long double);
    }
    va_end(argumentList);

    ldResult = pacevalLibrary_ldmathvi(handle_pacevalComputation_in,
                                       errorType_out, trustedMinResult_out,
                                       trustedMaxResult_out,
                                       functionString_in,
                                       numberOfVariables_in, variables_in,
                                       valuesVariablesArray);

    delete[] valuesVariablesArray;
    return ldResult;
}

extern "C" double paceval_dmathvi(PACEVAL_HANDLE* handle_pacevalComputation_in,
                                  int* errorType_out,
                                  double* trustedMinResult_out,
                                  double* trustedMaxResult_out,
                                  const char* functionString_in,
                                  unsigned long numberOfVariables_in,
                                  const char* variables_in, ...)
{
    double* valuesVariablesArray;
    va_list argumentList;
    double dResult;

    va_start(argumentList, variables_in);
    valuesVariablesArray = new double[numberOfVariables_in];

    for (unsigned long iCount = 0; iCount < numberOfVariables_in; iCount++)
    {
        valuesVariablesArray[iCount] = va_arg(argumentList, double);
    }
    va_end(argumentList);

    dResult = pacevalLibrary_dmathvi(handle_pacevalComputation_in,
                                     errorType_out, trustedMinResult_out,
                                     trustedMaxResult_out,
                                     functionString_in,
                                     numberOfVariables_in, variables_in,
                                     valuesVariablesArray);

    delete[] valuesVariablesArray;
    return dResult;
}

extern "C" float paceval_fmathvi(PACEVAL_HANDLE* handle_pacevalComputation_in,
                                 int* errorType_out,
                                 float* trustedMinResult_out,
                                 float* trustedMaxResult_out,
                                 const char* functionString_in,
                                 unsigned long numberOfVariables_in,
                                 const char* variables_in, ...)
{
    float* valuesVariablesArray;
    va_list argumentList;
    float fResult;

    va_start(argumentList, variables_in);
    valuesVariablesArray = new float[numberOfVariables_in];

    for (unsigned long iCount = 0; iCount < numberOfVariables_in; iCount++)
    {
        valuesVariablesArray[iCount] = va_arg(argumentList, double); //e.g. GNUC:'float' is promoted to 'double' when passed through '...'
    }
    va_end(argumentList);

    fResult = pacevalLibrary_fmathvi(handle_pacevalComputation_in,
                                     errorType_out, trustedMinResult_out,
                                     trustedMaxResult_out,
                                     functionString_in,
                                     numberOfVariables_in, variables_in,
                                     valuesVariablesArray);

    delete[] valuesVariablesArray;
    return fResult;
}

extern "C" long double paceval_ldGetComputationResult(PACEVAL_HANDLE handle_pacevalComputation_in,
        long double values_in[],
        long double* trustedMinResult_out,
        long double* trustedMaxResult_out)
{
    return pacevalLibrary_ldGetComputationResult(handle_pacevalComputation_in,
            values_in,
            trustedMinResult_out, trustedMaxResult_out);
}

extern "C" double paceval_dGetComputationResult(PACEVAL_HANDLE handle_pacevalComputation_in,
        double values_in[],
        double* trustedMinResult_out,
        double* trustedMaxResult_out)
{
    return pacevalLibrary_dGetComputationResult(handle_pacevalComputation_in,
            values_in,
            trustedMinResult_out, trustedMaxResult_out);
}

extern "C" float paceval_fGetComputationResult(PACEVAL_HANDLE handle_pacevalComputation_in,
        float values_in[],
        float* trustedMinResult_out,
        float* trustedMaxResult_out)
{
    return pacevalLibrary_fGetComputationResult(handle_pacevalComputation_in,
            values_in,
            trustedMinResult_out, trustedMaxResult_out);
}

extern "C" bool paceval_ldGetComputationResultExt(PACEVAL_HANDLE handle_pacevalComputation_in,
        long double values_in[],
        unsigned long numberOfCalculations_in,
        long double* results_out,
        long double* trustedMinResults_out,
        long double* trustedMaxResults_out,
        int* errorTypes_out)
{
    return pacevalLibrary_ldGetComputationResultExt(handle_pacevalComputation_in,
            values_in, numberOfCalculations_in,
            results_out, trustedMinResults_out, trustedMaxResults_out,
            errorTypes_out);
}

extern "C" bool paceval_dGetComputationResultExt(PACEVAL_HANDLE handle_pacevalComputation_in,
        double values_in[],
        unsigned long numberOfCalculations_in,
        double* results_out,
        double* trustedMinResults_out,
        double* trustedMaxResults_out,
        int* errorTypes_out)
{
    return pacevalLibrary_dGetComputationResultExt(handle_pacevalComputation_in,
            values_in, numberOfCalculations_in,
            results_out, trustedMinResults_out, trustedMaxResults_out,
            errorTypes_out);
}

extern "C" bool paceval_fGetComputationResultExt(PACEVAL_HANDLE handle_pacevalComputation_in,
        float values_in[],
        unsigned long numberOfCalculations_in,
        float* results_out,
        float* trustedMinResults_out,
        float* trustedMaxResults_out,
        int* errorTypes_out)
{
    return pacevalLibrary_fGetComputationResultExt(handle_pacevalComputation_in,
            values_in, numberOfCalculations_in,
            results_out, trustedMinResults_out, trustedMaxResults_out,
            errorTypes_out);
}

extern "C" bool paceval_ldGetMultipleComputationsResults(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        long double values_in[],
        long double* results_out,
        long double* trustedMinResults_out,
        long double* trustedMaxResults_out,
        int* errorTypes_out)
{
    return pacevalLibrary_ldGetMultipleComputationsResults(handle_pacevalComputations_in,
            numberOfpacevalComputations_in, values_in,
            results_out, trustedMinResults_out, trustedMaxResults_out,
            errorTypes_out);
}

extern "C" bool paceval_dGetMultipleComputationsResults(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        double values_in[],
        double* results_out,
        double* trustedMinResults_out,
        double* trustedMaxResults_out,
        int* errorTypes_out)
{
    return pacevalLibrary_dGetMultipleComputationsResults(handle_pacevalComputations_in,
            numberOfpacevalComputations_in, values_in,
            results_out, trustedMinResults_out, trustedMaxResults_out,
            errorTypes_out);
}

extern "C" bool paceval_fGetMultipleComputationsResults(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        float values_in[],
        float* results_out,
        float* trustedMinResults_out,
        float* trustedMaxResults_out,
        int* errorTypes_out)
{
    return pacevalLibrary_fGetMultipleComputationsResults(handle_pacevalComputations_in,
            numberOfpacevalComputations_in, values_in,
            results_out, trustedMinResults_out, trustedMaxResults_out,
            errorTypes_out);
}

extern "C" bool paceval_ldGetMultipleComputationsResultsExt(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        long double values_in[],
        unsigned long numberOfCalculations_in,
        long double* results_out,
        long double* trustedMinResults_out,
        long double* trustedMaxResults_out,
        int* errorTypes_out)
{
    return pacevalLibrary_ldGetMultipleComputationsResultsExt(handle_pacevalComputations_in,
            numberOfpacevalComputations_in, values_in, numberOfCalculations_in,
            results_out, trustedMinResults_out, trustedMaxResults_out,
            errorTypes_out);
}

extern "C" bool paceval_dGetMultipleComputationsResultsExt(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        double values_in[],
        unsigned long numberOfCalculations_in,
        double* results_out,
        double* trustedMinResults_out,
        double* trustedMaxResults_out,
        int* errorTypes_out)
{
    return pacevalLibrary_dGetMultipleComputationsResultsExt(handle_pacevalComputations_in,
            numberOfpacevalComputations_in, values_in, numberOfCalculations_in,
            results_out, trustedMinResults_out, trustedMaxResults_out,
            errorTypes_out);
}

extern "C" bool paceval_fGetMultipleComputationsResultsExt(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        float values_in[],
        unsigned long numberOfCalculations_in,
        float* results_out,
        float* trustedMinResults_out,
        float* trustedMaxResults_out,
        int* errorTypes_out)
{
    return pacevalLibrary_fGetMultipleComputationsResultsExt(handle_pacevalComputations_in,
            numberOfpacevalComputations_in, values_in, numberOfCalculations_in,
            results_out, trustedMinResults_out, trustedMaxResults_out,
            errorTypes_out);
}

extern "C" bool paceval_GetIsError(PACEVAL_HANDLE handle_pacevalComputation_in)
{
    return pacevalLibrary_GetIsError(handle_pacevalComputation_in);
}

extern "C" int paceval_GetErrorInformation(PACEVAL_HANDLE handle_pacevalComputation_in,
        char* lastError_strOperator_out,
        long* lastError_ePosition_out)
{
    return pacevalLibrary_GetErrorInformation(handle_pacevalComputation_in,
            lastError_strOperator_out,
            lastError_ePosition_out);
}

extern "C" int paceval_CreateErrorInformationText(PACEVAL_HANDLE handle_pacevalComputation_in,
        char* lastError_strMessage_out,
        char* lastError_strDetails_out)
{
    return pacevalLibrary_CreateErrorInformationText(handle_pacevalComputation_in,
            lastError_strMessage_out,
            lastError_strDetails_out);
}

extern "C" int paceval_GetErrorTypeMessage(int errorType_in,
        char* errorType_strMessage_out)
{
    return pacevalLibrary_GetErrorTypeMessage(errorType_in,
            errorType_strMessage_out);
}

extern "C" int paceval_GetComputationVersionString(PACEVAL_HANDLE handle_pacevalComputation_in,
        char* paceval_strVersion_out)
{
    return pacevalLibrary_GetComputationVersionString(handle_pacevalComputation_in,
            paceval_strVersion_out);
}

extern "C" bool paceval_SetCallbackUserFunction(unsigned int numberUserFunction_in,
        const char* singleFunctionString_in,
        paceval_callbackUserFunctionType* paceval_callbackUserFunction_in)
{
    return pacevalLibrary_SetCallbackUserFunction(numberUserFunction_in,
            singleFunctionString_in,
            paceval_callbackUserFunction_in);
}

extern "C" unsigned long paceval_CreateXMLFromParameters(char* paceval_strXML_out,
        const char* functionString_in,
        unsigned long numberOfVariables_in,
        const char* variables_in,
        const char* valuesString_in,
        bool useInterval_in)
{
    return pacevalLibrary_CreateXMLFromParameters(paceval_strXML_out,
            functionString_in, numberOfVariables_in, variables_in, valuesString_in,
            useInterval_in);
}

extern "C" int paceval_ReadParametersFromXML(const char* paceval_strXML_in,
        unsigned long* functionStringLength_out,
        unsigned long* variablesStringLength_out,
        unsigned long* numberOfVariables_out,
        unsigned long* valuesStringLength_out,
        char* functionString_out,
        char* variables_out,
        char* valuesString_out,
        bool* useInterval_out)
{
    return pacevalLibrary_ReadParametersFromXML(paceval_strXML_in, functionStringLength_out,
            variablesStringLength_out, numberOfVariables_out, valuesStringLength_out,
            functionString_out, variables_out, valuesString_out, useInterval_out);
}

extern "C" unsigned long paceval_GetComputationInformationXML(PACEVAL_HANDLE handle_pacevalComputation_in,
        char* paceval_strXML_out)
{
    return pacevalLibrary_GetComputationInformationXML(handle_pacevalComputation_in,
            paceval_strXML_out);
}
