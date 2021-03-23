//---------------------------------------------------------------------------
// Copyright 1997-2014. Version 1.x Joerg Koenning - All rights reserved.
// Copyright 2015-2021. Version 2.x, 3.x, 4.x 2015-2021 paceval.[Registered Trade Mark]
//                                            All rights reserved.
// Author(s) : paceval., see http://www.paceval.com
// File      : paceval_main.h
//---------------------------------------------------------------------------

//---------------------------------------------------------------------------
#ifndef paceval_mainH
#define paceval_mainH

#define paceval_mainVersionString   "4"
#define paceval_subVersionString    "01"

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
    PACEVAL_ERR_BEGIN,
    PACEVAL_ERR_FATAL_BEGIN,
    PACEVAL_ERR_FATAL_INITIALIZE_LIBRARY_NOT_CALLED,
    PACEVAL_ERR_FATAL_NO_LICENSE,
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


//---------------------------------------------------------------------------
//  paceval_CreateComputation
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
PACEVAL_HANDLE paceval_CreateComputation(const char* functionString_in,
        unsigned long numberOfVariables_in,
        const char* variables_in,
        bool useInterval_in,
        paceval_callbackStatusType* paceval_callbackStatus_in);

//---------------------------------------------------------------------------
//  paceval_CreateMultipleComputations
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
bool paceval_CreateMultipleComputations(PACEVAL_HANDLE handle_pacevalComputations_out[],
                                        const char* functionStrings_in[],
                                        unsigned long numberOfpacevalComputations_in,
                                        unsigned long numberOfVariables_in,
                                        const char* variables_in,
                                        bool useInterval_in,
                                        paceval_callbackStatusType* paceval_callbackStatus_in);

//---------------------------------------------------------------------------
//  paceval_DeleteComputation
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
bool paceval_DeleteComputation(PACEVAL_HANDLE handle_pacevalComputation_in);

//---------------------------------------------------------------------------
//  paceval_ldConvertFloatToString
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
int paceval_ldConvertFloatToString(char* destinationString_out,
                                   long double float_in);

//---------------------------------------------------------------------------
//  paceval_dConvertFloatToString
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
int paceval_dConvertFloatToString(char* destinationString_out,
                                  double float_in);

//---------------------------------------------------------------------------
//  paceval_fConvertFloatToString
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
int paceval_fConvertFloatToString(char* destinationString_out,
                                  float float_in);

//---------------------------------------------------------------------------
//  paceval_ldConvertStringToFloat
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
long double paceval_ldConvertStringToFloat(const char* sourceString_in,
        int* errorType_out,
        long* errPosition_out,
        bool useInterval_in,
        long double* trustedMinResult_out,
        long double* trustedMaxResult_out);

//---------------------------------------------------------------------------
//  paceval_dConvertStringToFloat
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
double paceval_dConvertStringToFloat(const char* sourceString_in,
                                     int* errorType_out,
                                     long* errPosition_out,
                                     bool useInterval_in,
                                     double* trustedMinResult_out,
                                     double* trustedMaxResult_out);

//---------------------------------------------------------------------------
//  paceval_fConvertStringToFloat
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
float paceval_fConvertStringToFloat(const char* sourceString_in,
                                    int* errorType_out,
                                    long* errPosition_out,
                                    bool useInterval_in,
                                    float* trustedMinResult_out,
                                    float* trustedMaxResult_out);

//---------------------------------------------------------------------------
//  paceval_ldmathv
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
long double paceval_ldmathv(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
                            int* errorType_out,
                            const char* functionString_in,
                            unsigned long numberOfVariables_in,
                            const char* variables_in, ...);

//---------------------------------------------------------------------------
//  paceval_dmathv
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
double paceval_dmathv(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
                      int* errorType_out,
                      const char* functionString_in,
                      unsigned long numberOfVariables_in,
                      const char* variables_in, ...);

//---------------------------------------------------------------------------
//  paceval_fmathv
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
float paceval_fmathv(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
                     int* errorType_out,
                     const char* functionString_in,
                     unsigned long numberOfVariables_in,
                     const char* variables_in, ...);

//---------------------------------------------------------------------------
//  paceval_ldmathvi
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
long double paceval_ldmathvi(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
                             int* errorType_out,
                             long double* trustedMinResult_out,
                             long double* trustedMaxResult_out,
                             const char* functionString_in,
                             unsigned long numberOfVariables_in,
                             const char* variables_in, ...);

//---------------------------------------------------------------------------
//  paceval_dmathvi
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
double paceval_dmathvi(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
                       int* errorType_out,
                       double* trustedMinResult_out,
                       double* trustedMaxResult_out,
                       const char* functionString_in,
                       unsigned long numberOfVariables_in,
                       const char* variables_in, ...);

//---------------------------------------------------------------------------
//  paceval_fmathvi
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
float paceval_fmathvi(PACEVAL_HANDLE* handle_pacevalComputation_out_in,
                      int* errorType_out,
                      float* trustedMinResult_out,
                      float* trustedMaxResult_out,
                      const char* functionString_in,
                      unsigned long numberOfVariables_in,
                      const char* variables_in, ...);

//---------------------------------------------------------------------------
//  paceval_ldGetComputationResult
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
long double paceval_ldGetComputationResult(PACEVAL_HANDLE handle_pacevalComputation_in,
        long double values_in[],
        long double* trustedMinResult_out,
        long double* trustedMaxResult_out);

//---------------------------------------------------------------------------
//  paceval_dGetComputationResult
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
double paceval_dGetComputationResult(PACEVAL_HANDLE handle_pacevalComputation_in,
                                     double values_in[],
                                     double* trustedMinResult_out,
                                     double* trustedMaxResult_out);

//---------------------------------------------------------------------------
//  paceval_fGetComputationResult
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
float paceval_fGetComputationResult(PACEVAL_HANDLE handle_pacevalComputation_in,
                                    float values_in[],
                                    float* trustedMinResult_out,
                                    float* trustedMaxResult_out);

//---------------------------------------------------------------------------
//  paceval_ldGetComputationResultExt
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
bool paceval_ldGetComputationResultExt(PACEVAL_HANDLE handle_pacevalComputation_in,
                                       long double values_in[],
                                       unsigned long numberOfCalculations_in,
                                       long double* results_out,
                                       long double* trustedMinResults_out,
                                       long double* trustedMaxResults_out,
                                       int* errorType_out);

//---------------------------------------------------------------------------
//  paceval_dGetComputationResultExt
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
bool paceval_dGetComputationResultExt(PACEVAL_HANDLE handle_pacevalComputation_in,
                                      double values_in[],
                                      unsigned long numberOfCalculations_in,
                                      double* results_out,
                                      double* trustedMinResults_out,
                                      double* trustedMaxResults_out,
                                      int* errorType_out);

//---------------------------------------------------------------------------
//  paceval_fGetComputationResultExt
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
bool paceval_fGetComputationResultExt(PACEVAL_HANDLE handle_pacevalComputation_in,
                                      float values_in[],
                                      unsigned long numberOfCalculations_in,
                                      float* results_out,
                                      float* trustedMinResults_out,
                                      float* trustedMaxResults_out,
                                      int* errorType_out);

//---------------------------------------------------------------------------
//  paceval_ldGetMultipleComputationsResults
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
bool paceval_ldGetMultipleComputationsResults(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        long double values_in[],
        long double* results_out,
        long double* trustedMinResults_out,
        long double* trustedMaxResults_out,
        int* errorTypes_out);

//---------------------------------------------------------------------------
//  paceval_dGetMultipleComputationsResults
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
bool paceval_dGetMultipleComputationsResults(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        double values_in[],
        double* results_out,
        double* trustedMinResults_out,
        double* trustedMaxResults_out,
        int* errorTypes_out);

//---------------------------------------------------------------------------
//  paceval_fGetMultipleComputationsResults
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
bool paceval_fGetMultipleComputationsResults(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        float values_in[],
        float* results_out,
        float* trustedMinResults_out,
        float* trustedMaxResults_out,
        int* errorTypes_out);

//---------------------------------------------------------------------------
//  paceval_GetIsError
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
bool paceval_GetIsError(PACEVAL_HANDLE handle_pacevalComputation_in);

//---------------------------------------------------------------------------
//  paceval_GetErrorInformation
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
int paceval_GetErrorInformation(PACEVAL_HANDLE handle_pacevalComputation_in,
                                char *lastError_strOperator_out,
                                long* lastError_errPosition_out);

//---------------------------------------------------------------------------
//  paceval_CreateErrorInformationText
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
int paceval_CreateErrorInformationText(PACEVAL_HANDLE handle_pacevalComputation_in,
                                       char* lastError_strMessage_out,
                                       char* lastError_strDetails_out);

//---------------------------------------------------------------------------
//  paceval_GetErrorTypeMessage
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
int paceval_GetErrorTypeMessage(int errorType_in,
                                char* errorType_strMessage_out);

//---------------------------------------------------------------------------
//  paceval_GetComputationVersionString
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
int paceval_GetComputationVersionString(PACEVAL_HANDLE handle_pacevalComputation_in,
                                        char* paceval_strVersion_out);

//---------------------------------------------------------------------------
//  paceval_SetCallbackUserFunction
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
bool paceval_SetCallbackUserFunction(unsigned int numberUserFunction_in,
                                     const char* singleFunctionString_in,
                                     paceval_callbackUserFunctionType* paceval_callbackUserFunction_in);

//---------------------------------------------------------------------------
//  paceval_InitializeLibrary
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
bool paceval_InitializeLibrary(const char* initString_in);

//---------------------------------------------------------------------------
//  paceval_FreeLibrary
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
bool paceval_FreeLibrary();

//---------------------------------------------------------------------------
//  paceval_CreateXMLFromParameters
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
unsigned long paceval_CreateXMLFromParameters(char* paceval_strXML_out,
        const char* functionString_in,
        unsigned long numberOfVariables_in,
        const char* variables_in,
        const char* valuesString_in,
        bool useInterval_in);

//---------------------------------------------------------------------------
//  paceval_ReadParametersFromXML
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
int paceval_ReadParametersFromXML(const char* paceval_strXML_in,
                                  unsigned long* functionStringLength_out,
                                  unsigned long* variablesStringLength_out,
                                  unsigned long* numberOfVariables_out,
                                  unsigned long* valuesStringLength_out,
                                  char* functionString_out,
                                  char* variables_out,
                                  char* valuesString_out,
                                  bool* useInterval_out);

//---------------------------------------------------------------------------
//  paceval_GetComputationInformationXML
//  see  http://www.paceval.com/api
//---------------------------------------------------------------------------
unsigned long paceval_GetComputationInformationXML(PACEVAL_HANDLE handle_pacevalComputation_in,
        char* paceval_strXML_out);

#ifdef __cplusplus
}
#endif
//---------------------------------------------------------------------------
#endif //paceval_mainH
