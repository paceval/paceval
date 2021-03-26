//---------------------------------------------------------------------------
// Copyright 1997-2014. Version 1.x Joerg Koenning - All rights reserved.
// Copyright 2015-2021. Version 2.x, 3.x, 4.x 2015-2021 paceval.[Registered Trade Mark]
//                                            All rights reserved.
// Author(s) : paceval., see http://www.paceval.com
// File      : paceval_main.cpp
//---------------------------------------------------------------------------
 
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
extern "C" bool pacevalLibrary_Initialize(const char* initString_in);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
bool (*pacevalLibrary_Free)();
#else
extern "C" bool pacevalLibrary_Free();
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
PACEVAL_HANDLE (*pacevalLibrary_CreateComputation)(const char* functionString_in,
        unsigned long numberOfVariables_in,
        const char* variables_in,
        bool useInterval_in,
        paceval_callbackStatusType* paceval_callbackStatus_in);
#else
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
extern "C" int pacevalLibrary_ldConvertFloatToString(char* destinationString_in,
        long double float_in);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
int (*pacevalLibrary_dConvertFloatToString)(char* destinationString_in,
        double float_in);
#else
extern "C" int pacevalLibrary_dConvertFloatToString(char* destinationString_in,
        double float_in);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
int (*pacevalLibrary_fConvertFloatToString)(char* destinationString_in,
        float float_in);
#else
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
bool (*pacevalLibrary_DeleteComputation)(PACEVAL_HANDLE handle_pacevalComputation_in);
#else
extern "C" bool pacevalLibrary_DeleteComputation(PACEVAL_HANDLE handle_pacevalComputation_in);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
long double(*pacevalLibrary_ldGetComputationResult)(PACEVAL_HANDLE handle_pacevalComputation_in,
        long double values_in[],
        long double* trustedMinResult_out,
        long double* trustedMaxResult_out);
#else
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
extern "C" bool pacevalLibrary_fGetMultipleComputationsResults(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfpacevalComputations_in,
        float values_in[],
        float* results_out,
        float* trustedMinResults_out,
        float* trustedMaxResults_out,
        int* errorTypes_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
bool (*pacevalLibrary_GetIsError)(PACEVAL_HANDLE handle_pacevalComputation_in);
#else
extern "C" bool pacevalLibrary_GetIsError(PACEVAL_HANDLE handle_pacevalComputation_in);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
int (*pacevalLibrary_GetErrorInformation)(PACEVAL_HANDLE handle_pacevalComputation_in,
        char* lastError_strOperator_out,
        long* lastError_ePosition_out);
#else
extern "C" int pacevalLibrary_GetErrorInformation(PACEVAL_HANDLE handle_pacevalComputation_in,
        char* lastError_strOperator_out,
        long* lastError_ePosition_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
int (*pacevalLibrary_CreateErrorInformationText)(PACEVAL_HANDLE handle_pacevalComputation_in,
        char* lastError_strMessage_out,
        char* lastError_strDetails_out);
#else
extern "C" int pacevalLibrary_CreateErrorInformationText(PACEVAL_HANDLE handle_pacevalComputation_in,
        char* lastError_strMessage_out,
        char* lastError_strDetails_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
int (*pacevalLibrary_GetErrorTypeMessage)(int errorType_in,
        char* errorType_strMessage_out);
#else
extern "C" int pacevalLibrary_GetErrorTypeMessage(int errorType_in,
        char* errorType_strMessage_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
int (*pacevalLibrary_GetComputationVersionString)(PACEVAL_HANDLE handle_pacevalComputation_in,
        char* paceval_strVersion_out);
#else
extern "C" int pacevalLibrary_GetComputationVersionString(PACEVAL_HANDLE handle_pacevalComputation_in,
        char* paceval_strVersion_out);
#endif //defined(paceval_use_dll)

#if defined(paceval_use_dll) && (paceval_use_dll == 1)
bool (*pacevalLibrary_SetCallbackUserFunction)(unsigned int numberUserFunction_in,
        const char* singleFunctionString_in,
        paceval_callbackUserFunctionType* paceval_callbackUserFunction_in);
#else
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
    return true;
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
