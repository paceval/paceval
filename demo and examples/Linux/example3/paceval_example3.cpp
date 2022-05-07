//---------------------------------------------------------------------------
// Copyright 1997-2014. Version 1.x Joerg Koenning - All rights reserved.
// Copyright 2015-2022. Version 2.x, 3.x, 4.x 2015-2022 paceval.[Registered Trade Mark]
//                                            All rights reserved.
// Author(s) : paceval., see http://www.paceval.com
// File      : paceval_example3.cpp
//---------------------------------------------------------------------------

//---------------------------------------------------------------------------
#if defined(_MSC_VER) //we don't use the Microsoft specific functions
#define _CRT_SECURE_NO_WARNINGS
#pragma warning(disable : 4996)
#endif //#if defined(_MSC_VER)

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

#if (defined(_WIN32) || defined(_WIN64))
#include <windows.h>
#endif

#include "../../system-independent/source_public/inc/paceval_main.h" //We include the paceval header

const char* CreateErrorMessage(char* messageBuffer, int pacevalErrorType, int lengthBuffer);
void CalculateAndPresentFloatExample3();
void CalculateAndPresentDoubleExample3();
void CalculateAndPresentLongDoubleExample3();
unsigned long GetOSCurrentTime();

char functionStr[] = "-sin(x*cos(x))^(1/y)";
//---------------------------------------------------------------------------

int main(int argc, char* argv[])
{
    int errType;
    char charBuffer500[500];

    if (paceval_InitializeLibrary(NULL) != true)
    {
        printf("\n\n paceval_InitializeLibrary() failed");
        return 0;
    }

    printf("\n| This demo application shows the capabilities of paceval. in terms of |");
    printf("\n| its features for multiple calculations. Please open the source code  |");
    printf("\n| file paceval_example3.cpp.                                           |");

    printf("\n\nFor this function: f(x,y)=%s", functionStr);
    printf("\neach time 100.000 calculations for the area x in [-10;10[.");

    printf("\n\n --- float ---------");
    CalculateAndPresentFloatExample3();
    printf("\n\n\n --- double --------");
    CalculateAndPresentDoubleExample3();

    printf("\n\n\n --- long double ---");
    //Check if compiler supports long double
    if (sizeof(long double) != sizeof(double))
    {
        CalculateAndPresentLongDoubleExample3();
    }
    else
    {
        if (paceval_fmathv(NULL, &errType, "paceval_LibrarySupportsLongDouble", 0, "", NULL) != 0)
            printf("\nYour paceval. library supports long double.");

        printf("\n\n%s",
               CreateErrorMessage(charBuffer500, PACEVAL_ERR_COMPUTATION_USER_COMPILER_NOT_SUPPORTS_LONG_DOUBLE, 500));

        printf("\nE.g. Microsoft Visual C++ does not support long double.");
        printf("\nExcerpt from the MSDN : 'Previous(...) versions of Microsoft C / C++ and Microsoft Visual C++ supported");
        printf("\nthe long double, 80-bit precision data type. (...), however, the long double data type");
        printf("\nmaps to the double, 64-bit precision data type.'");
    }

    if ((int)paceval_fmathv(NULL, &errType, "paceval_NumberThreadUsages", 0, "", NULL) > 0)
        printf("\n\n[Threads usages: %d]", (int)paceval_fmathv(NULL, &errType, "paceval_NumberThreadUsages", 0, "", NULL));
    if ((int)paceval_fmathv(NULL, &errType, "paceval_NumberCacheHitsACC", 0, "", NULL) > 0)
        printf("\n[Cache hits: %d]", (int)paceval_fmathv(NULL, &errType, "paceval_NumberCacheHitsACC", 0, "", NULL));
    printf("\n[Number of cores: %d]", (int)paceval_fmathv(NULL, &errType, "paceval_NumberOfCores", 0, "", NULL));
    printf("\n[paceval. Version number: %1.3g]", paceval_fmathv(NULL, &errType, "paceval_VersionNumber", 0, "", NULL));

    paceval_FreeLibrary();

    printf("\n\nClick RETURN twice");

    while ((getchar()) != '\n') {}
    while ((getchar()) != '\n') {}
    return  0;
}

void CalculateAndPresentFloatExample3()
{
    char charBuffer500[500];
    float* fvaluesVariablesArrayExt = new float[2*100000];
    float* fResults = new float[2*100000];
    float* fminResultIntervals = new float[2*100000];
    float* fmaxResultIntervals = new float[2*100000];
    float fFastIntegral;
    float fminFastIntegralInterval;
    float fmaxFastIntegralInterval;
    int* errorTypes = new int[2*100000];
    bool hasError;
    int errType;
    unsigned long startTime;
    unsigned long endTime;

    PACEVAL_HANDLE handle_pacevalComputation;
    PACEVAL_HANDLE handle_pacevalComputationi;

    //Create 2*100.000 values for the variables x and y
    float fareaDiff = (10.0f-(-10.0f)) / 100000.0f;

    for (unsigned long iCount = 0; iCount < 100000; iCount++)
    {
        fvaluesVariablesArrayExt[iCount * 2] = -10.0f + fareaDiff * iCount;
        fvaluesVariablesArrayExt[iCount * 2 + 1] = 0.5f;
    }

    //Create the paceval-Computation object
    handle_pacevalComputation = paceval_CreateComputation(functionStr,
                                2, "x y", false, NULL);

    //Create the paceval-Computation object with trusted intervals (TINC)
    handle_pacevalComputationi = paceval_CreateComputation(functionStr,
                                 2, "x y", true, NULL);

    //Calculate float results
    startTime = GetOSCurrentTime();
    hasError = paceval_fGetComputationResultExt(handle_pacevalComputation,
               &fvaluesVariablesArrayExt[0], 100000, &fResults[0],
               NULL, NULL, &errorTypes[0]);
    endTime = GetOSCurrentTime();

    fFastIntegral = 0;
    for (unsigned long iCount = 0; iCount < 100000; iCount++)
    {
        if (errorTypes[iCount] == PACEVAL_ERR_NO_ERROR)
            fFastIntegral = fFastIntegral + (fResults[iCount] * fareaDiff);
    }
    paceval_fConvertFloatToString(charBuffer500, fFastIntegral);
    printf("\n\nfloat: Fast integral is %s (paceval_fGetComputationResultExt)\n[Time needed: %d ms]", charBuffer500, endTime - startTime);

    //Calculate float interval results
    startTime = GetOSCurrentTime();
    hasError = paceval_fGetComputationResultExt(handle_pacevalComputationi,
               &fvaluesVariablesArrayExt[0], 100000, &fResults[0],
               &fminResultIntervals[0], &fmaxResultIntervals[0], &errorTypes[0]);
    endTime = GetOSCurrentTime();

    fFastIntegral = 0;
    fminFastIntegralInterval = 0;
    fmaxFastIntegralInterval = 0;
    for (unsigned long iCount = 0; iCount < 100000; iCount++)
    {
        if (errorTypes[iCount] == PACEVAL_ERR_NO_ERROR)
        {
            fFastIntegral = fFastIntegral + (fResults[iCount] * fareaDiff);
            fminFastIntegralInterval = fminFastIntegralInterval + (fminResultIntervals[iCount] * fareaDiff);
            fmaxFastIntegralInterval = fmaxFastIntegralInterval + (fmaxResultIntervals[iCount] * fareaDiff);
        }
    }
    paceval_fConvertFloatToString(charBuffer500, fFastIntegral);
    printf("\n\nfloat: Fast integral is %s (paceval_fGetComputationResultExt with TINC)", charBuffer500);
    paceval_fConvertFloatToString(charBuffer500, fminFastIntegralInterval);
    printf("\nfloat: Interval min. fast integral is %s (paceval_fGetComputationResultExt with TINC)", charBuffer500);
    paceval_fConvertFloatToString(charBuffer500, fmaxFastIntegralInterval);
    printf("\nfloat: Interval max. fast integral is %s (paceval_fGetComputationResultExt with TINC)\n[Time needed: %d ms]", charBuffer500, endTime - startTime);

    //Delete the paceval-Computation objects
    paceval_DeleteComputation(handle_pacevalComputation);
    paceval_DeleteComputation(handle_pacevalComputationi);

    delete[] fvaluesVariablesArrayExt;
    delete[] fResults;
    delete[] fminResultIntervals;
    delete[] fmaxResultIntervals;
    delete[] errorTypes;
}

void CalculateAndPresentDoubleExample3()
{
    char charBuffer500[500];
    double* dvaluesVariablesArrayExt = new double[2*100000];
    double* dResults = new double[2*100000];
    double* dminResultIntervals = new double[2*100000];
    double* dmaxResultIntervals = new double[2*100000];
    double dFastIntegral;
    double dminFastIntegralInterval;
    double dmaxFastIntegralInterval;
    int* errorTypes = new int[2*100000];
    bool hasError;
    int errType;
    unsigned long startTime;
    unsigned long endTime;

    PACEVAL_HANDLE handle_pacevalComputation;
    PACEVAL_HANDLE handle_pacevalComputationi;

    //Create 2*100.000 values for the variables x and y
    double dareaDiff = (10.0-(-10.0)) / 100000.0;

    for (unsigned long iCount = 0; iCount < 100000; iCount++)
    {
        dvaluesVariablesArrayExt[iCount * 2] = -10.0 + dareaDiff * iCount;
        dvaluesVariablesArrayExt[iCount * 2 + 1] = 0.5;
    }

    //Create the paceval-Computation object
    handle_pacevalComputation = paceval_CreateComputation(functionStr,
                                2, "x y", false, NULL);

    //Create the paceval-Computation object with trusted intervals (TINC)
    handle_pacevalComputationi = paceval_CreateComputation(functionStr,
                                 2, "x y", true, NULL);

    //Calculate double results
    startTime = GetOSCurrentTime();
    hasError = paceval_dGetComputationResultExt(handle_pacevalComputation,
               &dvaluesVariablesArrayExt[0], 100000, &dResults[0],
               NULL, NULL, &errorTypes[0]);
    endTime = GetOSCurrentTime();

    dFastIntegral = 0;
    for (unsigned long iCount = 0; iCount < 100000; iCount++)
    {
        if (errorTypes[iCount] == PACEVAL_ERR_NO_ERROR)
            dFastIntegral = dFastIntegral + (dResults[iCount] * dareaDiff);
    }
    paceval_dConvertFloatToString(charBuffer500, dFastIntegral);
    printf("\n\ndouble: Fast integral is %s (paceval_dGetComputationResultExt)\n[Time needed: %d ms]", charBuffer500, endTime - startTime);

    //Calculate double interval results
    startTime = GetOSCurrentTime();
    hasError = paceval_dGetComputationResultExt(handle_pacevalComputationi,
               &dvaluesVariablesArrayExt[0], 100000, &dResults[0],
               &dminResultIntervals[0], &dmaxResultIntervals[0], &errorTypes[0]);
    endTime = GetOSCurrentTime();

    dFastIntegral = 0;
    dminFastIntegralInterval = 0;
    dmaxFastIntegralInterval = 0;
    for (unsigned long iCount = 0; iCount < 100000; iCount++)
    {
        if (errorTypes[iCount] == PACEVAL_ERR_NO_ERROR)
        {
            dFastIntegral = dFastIntegral + (dResults[iCount] * dareaDiff);
            dminFastIntegralInterval = dminFastIntegralInterval + (dminResultIntervals[iCount] * dareaDiff);
            dmaxFastIntegralInterval = dmaxFastIntegralInterval + (dmaxResultIntervals[iCount] * dareaDiff);
        }
    }
    paceval_dConvertFloatToString(charBuffer500, dFastIntegral);
    printf("\n\ndouble: Fast integral is %s (paceval_dGetComputationResultExt with TINC)", charBuffer500);
    paceval_dConvertFloatToString(charBuffer500, dminFastIntegralInterval);
    printf("\ndouble: Interval min. fast integral is %s (paceval_dGetComputationResultExt with TINC)", charBuffer500);
    paceval_dConvertFloatToString(charBuffer500, dmaxFastIntegralInterval);
    printf("\ndouble: Interval max. fast integral is %s (paceval_dGetComputationResultExt with TINC)\n[Time needed: %d ms]", charBuffer500, endTime - startTime);

    //Delete the paceval-Computation objects
    paceval_DeleteComputation(handle_pacevalComputation);
    paceval_DeleteComputation(handle_pacevalComputationi);

    delete[] dvaluesVariablesArrayExt;
    delete[] dResults;
    delete[] dminResultIntervals;
    delete[] dmaxResultIntervals;
    delete[] errorTypes;
}

void CalculateAndPresentLongDoubleExample3()
{
    char charBuffer500[500];
    long double* ldvaluesVariablesArrayExt = new long double[2*100000];
    long double* ldResults = new long double[2*100000];
    long double* ldminResultIntervals = new long double[2*100000];
    long double* ldmaxResultIntervals = new long double[2*100000];
    long double ldFastIntegral;
    long double ldminFastIntegralInterval;
    long double ldmaxFastIntegralInterval;
    int* errorTypes = new int[2*100000];
    bool hasError;
    int errType;
    unsigned long startTime;
    unsigned long endTime;

    PACEVAL_HANDLE handle_pacevalComputation;
    PACEVAL_HANDLE handle_pacevalComputationi;

    //Create 2*100.000 values for the variables x and y
    long double ldareaDiff = (10.0L-(-10.0L)) / 100000.0L;

    for (unsigned long iCount = 0; iCount < 100000; iCount++)
    {
        ldvaluesVariablesArrayExt[iCount * 2] = -10.0L + ldareaDiff * iCount;
        ldvaluesVariablesArrayExt[iCount * 2 + 1] = 0.5L;
    }

    //Create the paceval-Computation object
    handle_pacevalComputation = paceval_CreateComputation(functionStr,
                                2, "x y", false, NULL);

    //Create the paceval-Computation object with trusted intervals (TINC)
    handle_pacevalComputationi = paceval_CreateComputation(functionStr,
                                 2, "x y", true, NULL);

    //Calculate long double results
    startTime = GetOSCurrentTime();
    hasError = paceval_ldGetComputationResultExt(handle_pacevalComputation,
               &ldvaluesVariablesArrayExt[0], 100000, &ldResults[0],
               NULL, NULL, &errorTypes[0]);
    endTime = GetOSCurrentTime();

    ldFastIntegral = 0;
    for (unsigned long iCount = 0; iCount < 100000; iCount++)
    {
        if (errorTypes[iCount] == PACEVAL_ERR_NO_ERROR)
            ldFastIntegral = ldFastIntegral + (ldResults[iCount] * ldareaDiff);
    }
    paceval_ldConvertFloatToString(charBuffer500, ldFastIntegral);
    printf("\n\nlong double: Fast integral is %s (paceval_ldGetComputationResultExt)\n[Time needed: %d ms]", charBuffer500, endTime - startTime);

    //Calculate long double interval results
    startTime = GetOSCurrentTime();
    hasError = paceval_ldGetComputationResultExt(handle_pacevalComputationi,
               &ldvaluesVariablesArrayExt[0], 100000, &ldResults[0],
               &ldminResultIntervals[0], &ldmaxResultIntervals[0], &errorTypes[0]);
    endTime = GetOSCurrentTime();

    ldFastIntegral = 0;
    ldminFastIntegralInterval = 0;
    ldmaxFastIntegralInterval = 0;
    for (unsigned long iCount = 0; iCount < 100000; iCount++)
    {
        if (errorTypes[iCount] == PACEVAL_ERR_NO_ERROR)
        {
            ldFastIntegral = ldFastIntegral + (ldResults[iCount] * ldareaDiff);
            ldminFastIntegralInterval = ldminFastIntegralInterval + (ldminResultIntervals[iCount] * ldareaDiff);
            ldmaxFastIntegralInterval = ldmaxFastIntegralInterval + (ldmaxResultIntervals[iCount] * ldareaDiff);
        }
    }
    paceval_ldConvertFloatToString(charBuffer500, ldFastIntegral);
    printf("\n\nlong double: Fast integral is %s (paceval_ldGetComputationResultExt with TINC)", charBuffer500);
    paceval_ldConvertFloatToString(charBuffer500, ldminFastIntegralInterval);
    printf("\nlong double: Interval min. fast integral is %s (paceval_ldGetComputationResultExt with TINC)", charBuffer500);
    paceval_ldConvertFloatToString(charBuffer500, ldmaxFastIntegralInterval);
    printf("\nlong double: Interval max. fast integral is %s (paceval_ldGetComputationResultExt with TINC)\n[Time needed: %d ms]", charBuffer500, endTime - startTime);

    //Delete the paceval-Computation objects
    paceval_DeleteComputation(handle_pacevalComputation);
    paceval_DeleteComputation(handle_pacevalComputationi);

    delete[] ldvaluesVariablesArrayExt;
    delete[] ldResults;
    delete[] ldminResultIntervals;
    delete[] ldmaxResultIntervals;
    delete[] errorTypes;
}

unsigned long GetOSCurrentTime()
{
    unsigned long currentTime;

#if (defined(_WIN32) || defined(_WIN64))
    currentTime = GetTickCount();
#else
    struct timespec struct_timeSpec;

    clock_gettime(CLOCK_REALTIME, &struct_timeSpec);
    currentTime = struct_timeSpec.tv_sec * 1000 + lround(struct_timeSpec.tv_nsec/1.0e6);
#endif

    return currentTime;
}

const char* CreateErrorMessage(char* messageBuffer, int pacevalErrorType, int lengthBuffer)
{
    int maxMessageDetailsLength;
    char* errMessage;

    maxMessageDetailsLength = paceval_GetErrorTypeMessage(pacevalErrorType,
                              NULL);
    errMessage = new char[maxMessageDetailsLength];
    maxMessageDetailsLength = paceval_GetErrorTypeMessage(pacevalErrorType,
                              errMessage);

    strncpy(messageBuffer, errMessage, lengthBuffer - 1);
    messageBuffer[lengthBuffer - 1] = '\0';
    delete[] errMessage;

    return messageBuffer;
}

