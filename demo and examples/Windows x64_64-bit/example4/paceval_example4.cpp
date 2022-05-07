//---------------------------------------------------------------------------
// Copyright 1997-2014. Version 1.x Joerg Koenning - All rights reserved.
// Copyright 2015-2022. Version 2.x, 3.x, 4.x 2015-2022 paceval.[Registered Trade Mark]
//                                            All rights reserved.
// Author(s) : paceval., see http://www.paceval.com
// File      : paceval_example4.cpp
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

#include "../../system-independent/source_public/inc/paceval_main.h" //We include the paceval header

const char* CreateErrorMessage(char* messageBuffer, int pacevalErrorType, int lengthBuffer);
void CalculateAndPresentFloatExample4();
void CalculateAndPresentDoubleExample4();
void CalculateAndPresentLongDoubleExample4();

char functionStrSin[] = "sin(x)*y";
char functionStrCos[] = "cos(x)*y";
char functionStrTan[] = "tan(x)*y";
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
    printf("\n| its features for simultaneous calculations. Please open the source   |");
    printf("\n| code file paceval_example4.cpp.                                      |");

    printf("\n\nFor these functions:");
    printf("\n f(x,y)=%s", functionStrSin);
    printf("\n f(x,y)=%s", functionStrCos);
    printf("\n f(x,y)=%s", functionStrTan);
    printf("\nand the given variables x=2.5, y=1 we get these results.");

    printf("\n\n --- float ---------");
    CalculateAndPresentFloatExample4();
    printf("\n\n\n --- double --------");
    CalculateAndPresentDoubleExample4();

    printf("\n\n\n --- long double ---");
    //Check if compiler supports long double
    if (sizeof(long double) != sizeof(double))
    {
        CalculateAndPresentLongDoubleExample4();
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

void CalculateAndPresentFloatExample4()
{
    char charBuffer500[500];
    bool hasError;

    float* fvaluesVariablesArray = new float[2];
    float* fResults = new float[3];
    float* fminResultIntervals = new float[3];
    float* fmaxResultIntervals = new float[3];
    int* errorTypes = new int[3];

    fvaluesVariablesArray[0] = 2.5f;
    fvaluesVariablesArray[1] = 1.0f;

    //Calculate float results
    {
        PACEVAL_HANDLE handle_pacevalComputationSin;
        PACEVAL_HANDLE handle_pacevalComputationCos;
        PACEVAL_HANDLE handle_pacevalComputationTan;
        PACEVAL_HANDLE* handle_pacevalComputationsArray = new PACEVAL_HANDLE[3];

        //Create the paceval-Computation objects
        handle_pacevalComputationSin = paceval_CreateComputation("sin(x)*y",
                                       2, "x y", false, NULL);
        handle_pacevalComputationCos = paceval_CreateComputation("cos(x)*y",
                                       2, "x y", false, NULL);
        handle_pacevalComputationTan = paceval_CreateComputation("tan(x)*y",
                                       2, "x y", false, NULL);
        handle_pacevalComputationsArray[0] = handle_pacevalComputationSin;
        handle_pacevalComputationsArray[1] = handle_pacevalComputationCos;
        handle_pacevalComputationsArray[2] = handle_pacevalComputationTan;

        hasError = paceval_fGetMultipleComputationsResults(handle_pacevalComputationsArray,
                   3, &fvaluesVariablesArray[0],
                   &fResults[0], NULL, NULL, //&fminResultIntervals[0], &fmaxResultIntervals[0],
                   &errorTypes[0]);

        printf("\n\nFor function: f(x,y)=%s", functionStrSin);
        paceval_fConvertFloatToString(charBuffer500, fResults[0]);
        printf("\nfloat: Result is %s (paceval_fGetMultipleComputationsResults)", charBuffer500);

        printf("\n\nFor function: g(x,y)=%s", functionStrCos);
        paceval_fConvertFloatToString(charBuffer500, fResults[1]);
        printf("\nfloat: Result is %s (paceval_fGetMultipleComputationsResults)", charBuffer500);

        printf("\n\nFor function: h(x,y)=%s", functionStrTan);
        paceval_fConvertFloatToString(charBuffer500, fResults[2]);
        printf("\nfloat: Result is %s (paceval_fGetMultipleComputationsResults)", charBuffer500);

        //Delete the paceval-Computation objects
        paceval_DeleteComputation(handle_pacevalComputationSin);
        paceval_DeleteComputation(handle_pacevalComputationCos);
        paceval_DeleteComputation(handle_pacevalComputationTan);

        delete[] handle_pacevalComputationsArray;
    }

    //Calculate float interval results
    {
        PACEVAL_HANDLE handle_pacevalComputationSin_i;
        PACEVAL_HANDLE handle_pacevalComputationCos_i;
        PACEVAL_HANDLE handle_pacevalComputationTan_i;
        PACEVAL_HANDLE* handle_pacevalComputationsArray_i = new PACEVAL_HANDLE[3];

        //Create the paceval-Computation objects with trusted intervals (TINC)
        handle_pacevalComputationSin_i = paceval_CreateComputation("sin(x)*y",
                                         2, "x y", true, NULL);
        handle_pacevalComputationCos_i = paceval_CreateComputation("cos(x)*y",
                                         2, "x y", true, NULL);
        handle_pacevalComputationTan_i = paceval_CreateComputation("tan(x)*y",
                                         2, "x y", true, NULL);
        handle_pacevalComputationsArray_i[0] = handle_pacevalComputationSin_i;
        handle_pacevalComputationsArray_i[1] = handle_pacevalComputationCos_i;
        handle_pacevalComputationsArray_i[2] = handle_pacevalComputationTan_i;

        hasError = paceval_fGetMultipleComputationsResults(handle_pacevalComputationsArray_i,
                   3, &fvaluesVariablesArray[0],
                   &fResults[0], &fminResultIntervals[0], &fmaxResultIntervals[0],
                   &errorTypes[0]);

        printf("\n\nFor function: f(x,y)=%s  with trusted intervals (TINC)", functionStrSin);
        paceval_fConvertFloatToString(charBuffer500, fResults[0]);
        printf("\nfloat: Result is %s (paceval_fGetMultipleComputationsResults)", charBuffer500);
        paceval_fConvertFloatToString(charBuffer500, fminResultIntervals[0]);
        printf("\nfloat: Interval min. result is %s (paceval_fGetMultipleComputationsResults)", charBuffer500);
        paceval_fConvertFloatToString(charBuffer500, fmaxResultIntervals[0]);
        printf("\nfloat: Interval max. result is %s (paceval_fGetMultipleComputationsResults)", charBuffer500);

        printf("\n\nFor function: g(x,y)=%s  with trusted intervals (TINC)", functionStrCos);
        paceval_fConvertFloatToString(charBuffer500, fResults[1]);
        printf("\nfloat: Result is %s (paceval_fGetMultipleComputationsResults)", charBuffer500);
        paceval_fConvertFloatToString(charBuffer500, fminResultIntervals[1]);
        printf("\nfloat: Interval min. result is %s (paceval_fGetMultipleComputationsResults)", charBuffer500);
        paceval_fConvertFloatToString(charBuffer500, fmaxResultIntervals[1]);
        printf("\nfloat: Interval max. result is %s (paceval_fGetMultipleComputationsResults)", charBuffer500);

        printf("\n\nFor function: h(x,y)=%s  with trusted intervals (TINC)", functionStrTan);
        paceval_fConvertFloatToString(charBuffer500, fResults[2]);
        printf("\nfloat: Result is %s (paceval_fGetMultipleComputationsResults)", charBuffer500);
        paceval_fConvertFloatToString(charBuffer500, fminResultIntervals[2]);
        printf("\nfloat: Interval min. result is %s (paceval_fGetMultipleComputationsResults)", charBuffer500);
        paceval_fConvertFloatToString(charBuffer500, fmaxResultIntervals[2]);
        printf("\nfloat: Interval max. result is %s (paceval_fGetMultipleComputationsResults)", charBuffer500);

        //Delete the paceval-Computation objects
        paceval_DeleteComputation(handle_pacevalComputationSin_i);
        paceval_DeleteComputation(handle_pacevalComputationCos_i);
        paceval_DeleteComputation(handle_pacevalComputationTan_i);

        delete[] handle_pacevalComputationsArray_i;
    }

    delete[] fvaluesVariablesArray;
    delete[] fResults;
    delete[] fminResultIntervals;
    delete[] fmaxResultIntervals;
    delete[] errorTypes;
}

void CalculateAndPresentDoubleExample4()
{
    char charBuffer500[500];
    bool hasError;

    double* dvaluesVariablesArray = new double[2];
    double* dResults = new double[3];
    double* dminResultIntervals = new double[3];
    double* dmaxResultIntervals = new double[3];
    int* errorTypes = new int[3];

    dvaluesVariablesArray[0] = 2.5;
    dvaluesVariablesArray[1] = 1.0;

    //Calculate double results
    {
        PACEVAL_HANDLE handle_pacevalComputationSin;
        PACEVAL_HANDLE handle_pacevalComputationCos;
        PACEVAL_HANDLE handle_pacevalComputationTan;
        PACEVAL_HANDLE* handle_pacevalComputationsArray = new PACEVAL_HANDLE[3];

        //Create the paceval-Computation objects
        handle_pacevalComputationSin = paceval_CreateComputation("sin(x)*y",
                                       2, "x y", false, NULL);
        handle_pacevalComputationCos = paceval_CreateComputation("cos(x)*y",
                                       2, "x y", false, NULL);
        handle_pacevalComputationTan = paceval_CreateComputation("tan(x)*y",
                                       2, "x y", false, NULL);
        handle_pacevalComputationsArray[0] = handle_pacevalComputationSin;
        handle_pacevalComputationsArray[1] = handle_pacevalComputationCos;
        handle_pacevalComputationsArray[2] = handle_pacevalComputationTan;

        hasError = paceval_dGetMultipleComputationsResults(handle_pacevalComputationsArray,
                   3, &dvaluesVariablesArray[0],
                   &dResults[0], NULL, NULL,
                   &errorTypes[0]);

        printf("\n\nFor function: f(x,y)=%s", functionStrSin);
        paceval_dConvertFloatToString(charBuffer500, dResults[0]);
        printf("\ndouble: Result is %s (paceval_dGetMultipleComputationsResults)", charBuffer500);

        printf("\n\nFor function: g(x,y)=%s", functionStrCos);
        paceval_dConvertFloatToString(charBuffer500, dResults[1]);
        printf("\ndouble: Result is %s (paceval_dGetMultipleComputationsResults)", charBuffer500);

        printf("\n\nFor function: h(x,y)=%s", functionStrTan);
        paceval_dConvertFloatToString(charBuffer500, dResults[2]);
        printf("\ndouble: Result is %s (paceval_dGetMultipleComputationsResults)", charBuffer500);

        //Delete the paceval-Computation objects
        paceval_DeleteComputation(handle_pacevalComputationSin);
        paceval_DeleteComputation(handle_pacevalComputationCos);
        paceval_DeleteComputation(handle_pacevalComputationTan);

        delete[] handle_pacevalComputationsArray;
    }

    //Calculate double interval results
    {
        PACEVAL_HANDLE handle_pacevalComputationSin_i;
        PACEVAL_HANDLE handle_pacevalComputationCos_i;
        PACEVAL_HANDLE handle_pacevalComputationTan_i;
        PACEVAL_HANDLE* handle_pacevalComputationsArray_i = new PACEVAL_HANDLE[3];

        //Create the paceval-Computation objects with trusted intervals (TINC)
        handle_pacevalComputationSin_i = paceval_CreateComputation("sin(x)*y",
                                         2, "x y", true, NULL);
        handle_pacevalComputationCos_i = paceval_CreateComputation("cos(x)*y",
                                         2, "x y", true, NULL);
        handle_pacevalComputationTan_i = paceval_CreateComputation("tan(x)*y",
                                         2, "x y", true, NULL);
        handle_pacevalComputationsArray_i[0] = handle_pacevalComputationSin_i;
        handle_pacevalComputationsArray_i[1] = handle_pacevalComputationCos_i;
        handle_pacevalComputationsArray_i[2] = handle_pacevalComputationTan_i;

        hasError = paceval_dGetMultipleComputationsResults(handle_pacevalComputationsArray_i,
                   3, &dvaluesVariablesArray[0],
                   &dResults[0], &dminResultIntervals[0], &dmaxResultIntervals[0],
                   &errorTypes[0]);

        printf("\n\nFor function: f(x,y)=%s  with trusted intervals (TINC)", functionStrSin);
        paceval_dConvertFloatToString(charBuffer500, dResults[0]);
        printf("\ndouble: Result is %s (paceval_dGetMultipleComputationsResults)", charBuffer500);
        paceval_dConvertFloatToString(charBuffer500, dminResultIntervals[0]);
        printf("\ndouble: Interval min. result is %s (paceval_dGetMultipleComputationsResults)", charBuffer500);
        paceval_dConvertFloatToString(charBuffer500, dmaxResultIntervals[0]);
        printf("\ndouble: Interval max. result is %s (paceval_dGetMultipleComputationsResults)", charBuffer500);

        printf("\n\nFor function: g(x,y)=%s  with trusted intervals (TINC)", functionStrCos);
        paceval_dConvertFloatToString(charBuffer500, dResults[1]);
        printf("\ndouble: Result is %s (paceval_dGetMultipleComputationsResults)", charBuffer500);
        paceval_dConvertFloatToString(charBuffer500, dminResultIntervals[1]);
        printf("\ndouble: Interval min. result is %s (paceval_dGetMultipleComputationsResults)", charBuffer500);
        paceval_dConvertFloatToString(charBuffer500, dmaxResultIntervals[1]);
        printf("\ndouble: Interval max. result is %s (paceval_dGetMultipleComputationsResults)", charBuffer500);

        printf("\n\nFor function: h(x,y)=%s  with trusted intervals (TINC)", functionStrTan);
        paceval_dConvertFloatToString(charBuffer500, dResults[2]);
        printf("\ndouble: Result is %s (paceval_dGetMultipleComputationsResults)", charBuffer500);
        paceval_dConvertFloatToString(charBuffer500, dminResultIntervals[2]);
        printf("\ndouble: Interval min. result is %s (paceval_dGetMultipleComputationsResults)", charBuffer500);
        paceval_dConvertFloatToString(charBuffer500, dmaxResultIntervals[2]);
        printf("\ndouble: Interval max. result is %s (paceval_dGetMultipleComputationsResults)", charBuffer500);

        //Delete the paceval-Computation objects
        paceval_DeleteComputation(handle_pacevalComputationSin_i);
        paceval_DeleteComputation(handle_pacevalComputationCos_i);
        paceval_DeleteComputation(handle_pacevalComputationTan_i);

        delete[] handle_pacevalComputationsArray_i;
    }

    delete[] dvaluesVariablesArray;
    delete[] dResults;
    delete[] dminResultIntervals;
    delete[] dmaxResultIntervals;
    delete[] errorTypes;
}

void CalculateAndPresentLongDoubleExample4()
{
    char charBuffer500[500];
    bool hasError;

    long double* ldvaluesVariablesArray = new long double[2];
    long double* ldResults = new long double[3];
    long double* ldminResultIntervals = new long double[3];
    long double* ldmaxResultIntervals = new long double[3];
    int* errorTypes = new int[3];

    ldvaluesVariablesArray[0] = 2.5L;
    ldvaluesVariablesArray[1] = 1.0L;

    //Calculate long double results
    {
        PACEVAL_HANDLE handle_pacevalComputationSin;
        PACEVAL_HANDLE handle_pacevalComputationCos;
        PACEVAL_HANDLE handle_pacevalComputationTan;
        PACEVAL_HANDLE* handle_pacevalComputationsArray = new PACEVAL_HANDLE[3];

        //Create the paceval-Computation objects
        handle_pacevalComputationSin = paceval_CreateComputation("sin(x)*y",
                                       2, "x y", false, NULL);
        handle_pacevalComputationCos = paceval_CreateComputation("cos(x)*y",
                                       2, "x y", false, NULL);
        handle_pacevalComputationTan = paceval_CreateComputation("tan(x)*y",
                                       2, "x y", false, NULL);
        handle_pacevalComputationsArray[0] = handle_pacevalComputationSin;
        handle_pacevalComputationsArray[1] = handle_pacevalComputationCos;
        handle_pacevalComputationsArray[2] = handle_pacevalComputationTan;

        hasError = paceval_ldGetMultipleComputationsResults(handle_pacevalComputationsArray,
                   3, &ldvaluesVariablesArray[0],
                   &ldResults[0], NULL, NULL,
                   &errorTypes[0]);

        printf("\n\nFor function: f(x,y)=%s", functionStrSin);
        paceval_ldConvertFloatToString(charBuffer500, ldResults[0]);
        printf("\nlong double: Result is %s (paceval_ldGetMultipleComputationsResults)", charBuffer500);

        printf("\n\nFor function: g(x,y)=%s", functionStrCos);
        paceval_ldConvertFloatToString(charBuffer500, ldResults[1]);
        printf("\nlong double: Result is %s (paceval_ldGetMultipleComputationsResults)", charBuffer500);

        printf("\n\nFor function: h(x,y)=%s", functionStrTan);
        paceval_ldConvertFloatToString(charBuffer500, ldResults[2]);
        printf("\nlong double: Result is %s (paceval_ldGetMultipleComputationsResults)", charBuffer500);

        //Delete the paceval-Computation objects
        paceval_DeleteComputation(handle_pacevalComputationSin);
        paceval_DeleteComputation(handle_pacevalComputationCos);
        paceval_DeleteComputation(handle_pacevalComputationTan);

        delete[] handle_pacevalComputationsArray;
    }

    //Calculate long double interval results
    {
        PACEVAL_HANDLE handle_pacevalComputationSin_i;
        PACEVAL_HANDLE handle_pacevalComputationCos_i;
        PACEVAL_HANDLE handle_pacevalComputationTan_i;
        PACEVAL_HANDLE* handle_pacevalComputationsArray_i = new PACEVAL_HANDLE[3];

        //Create the paceval-Computation objects with trusted intervals (TINC)
        handle_pacevalComputationSin_i = paceval_CreateComputation("sin(x)*y",
                                         2, "x y", true, NULL);
        handle_pacevalComputationCos_i = paceval_CreateComputation("cos(x)*y",
                                         2, "x y", true, NULL);
        handle_pacevalComputationTan_i = paceval_CreateComputation("tan(x)*y",
                                         2, "x y", true, NULL);
        handle_pacevalComputationsArray_i[0] = handle_pacevalComputationSin_i;
        handle_pacevalComputationsArray_i[1] = handle_pacevalComputationCos_i;
        handle_pacevalComputationsArray_i[2] = handle_pacevalComputationTan_i;

        hasError = paceval_ldGetMultipleComputationsResults(handle_pacevalComputationsArray_i,
                   3, &ldvaluesVariablesArray[0],
                   &ldResults[0], &ldminResultIntervals[0], &ldmaxResultIntervals[0],
                   &errorTypes[0]);

        printf("\n\nFor function: f(x,y)=%s  with trusted intervals (TINC)", functionStrSin);
        paceval_ldConvertFloatToString(charBuffer500, ldResults[0]);
        printf("\nlong double: Result is %s (paceval_ldGetMultipleComputationsResults)", charBuffer500);
        paceval_ldConvertFloatToString(charBuffer500, ldminResultIntervals[0]);
        printf("\nlong double: Interval min. result is %s (paceval_ldGetMultipleComputationsResults)", charBuffer500);
        paceval_ldConvertFloatToString(charBuffer500, ldmaxResultIntervals[0]);
        printf("\nlong double: Interval max. result is %s (paceval_ldGetMultipleComputationsResults)", charBuffer500);

        printf("\n\nFor function: g(x,y)=%s  with trusted intervals (TINC)", functionStrCos);
        paceval_ldConvertFloatToString(charBuffer500, ldResults[1]);
        printf("\nlong double: Result is %s (paceval_ldGetMultipleComputationsResults)", charBuffer500);
        paceval_ldConvertFloatToString(charBuffer500, ldminResultIntervals[1]);
        printf("\nlong double: Interval min. result is %s (paceval_ldGetMultipleComputationsResults)", charBuffer500);
        paceval_ldConvertFloatToString(charBuffer500, ldmaxResultIntervals[1]);
        printf("\nlong double: Interval max. result is %s (paceval_ldGetMultipleComputationsResults)", charBuffer500);

        printf("\n\nFor function: h(x,y)=%s  with trusted intervals (TINC)", functionStrTan);
        paceval_ldConvertFloatToString(charBuffer500, ldResults[2]);
        printf("\nlong double: Result is %s (paceval_ldGetMultipleComputationsResults)", charBuffer500);
        paceval_ldConvertFloatToString(charBuffer500, ldminResultIntervals[2]);
        printf("\nlong double: Interval min. result is %s (paceval_ldGetMultipleComputationsResults)", charBuffer500);
        paceval_ldConvertFloatToString(charBuffer500, ldmaxResultIntervals[2]);
        printf("\nlong double: Interval max. result is %s (paceval_ldGetMultipleComputationsResults)", charBuffer500);

        //Delete the paceval-Computation objects
        paceval_DeleteComputation(handle_pacevalComputationSin_i);
        paceval_DeleteComputation(handle_pacevalComputationCos_i);
        paceval_DeleteComputation(handle_pacevalComputationTan_i);

        delete[] handle_pacevalComputationsArray_i;
    }

    delete[] ldvaluesVariablesArray;
    delete[] ldResults;
    delete[] ldminResultIntervals;
    delete[] ldmaxResultIntervals;
    delete[] errorTypes;
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

