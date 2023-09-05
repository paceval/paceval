//---------------------------------------------------------------------------
// Copyright 1997-2014. Version 1.x Joerg Koenning - All rights reserved.
// Copyright 2015-2023. Version 2.x, 3.x, 4.x 2015-2023 paceval.[Registered Trade Mark]
//                                            All rights reserved.
// Author(s) : paceval., see http://www.paceval.com
// File      : paceval_example2.cpp
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
bool paceval_callbackUserFunction1(const int useCalculationPrecision_in,
                                   const long double* valueFieldAsLongDouble,
                                   long double* resultAsLongDouble,
                                   const double* valueFieldAsDouble,
                                   double* resultAsDouble,
                                   const float* valueFieldAsFloat,
                                   float* resultAsFloat);
//---------------------------------------------------------------------------

int main(int argc, char* argv[])
{
    int errType;
    char charBuffer500[500];
    double dcompResult;
    double dminResultInterval;
    double dmaxResultInterval;
    float fcompResult;
    float fminResultInterval;
    float fmaxResultInterval;
    long double ldcompResult;
    long double ldminResultInterval;
    long double ldmaxResultInterval;
    char versionString[500];

    char functionStr[] = "-sin(x*cos(x))^(1/y) + my_function1(y) \"<-user function\"";

    if (paceval_InitializeLibrary(NULL) != true)
    {
        printf("\n\n paceval_InitializeLibrary() failed");
        return 0;
    }

    bool success = paceval_SetCallbackUserFunction(1, "my_function1",
                   paceval_callbackUserFunction1);

    printf("\n|----------------------------------------------------------------------|");
    printf("\n| This demo application shows the capabilities of paceval. in terms of |");
    printf("\n| its convenience functions (mathv and mathvi).                        |");
    printf("\n| Just open the file 'paceval_example2.cpp' to see its source          |");
    printf("\n| code (~230 lines).                                                   |");
    printf("\n|                                                                      |");
    printf("\n| see https://paceval.com/api/ for the API                             |");
    printf("\n|----------------------------------------------------------------------|");

    printf("\n\nFor this function: f(x,y)=%s", functionStr);
    printf("\nand the given variables x=0.5, y=2.0 we get these results.");

    //Calculate float results
    fcompResult = paceval_fmathv(NULL, &errType, functionStr, 2, "x y", 0.5, 2.0);
    if (errType == PACEVAL_ERR_NO_ERROR)
    {
        paceval_fConvertFloatToString(charBuffer500, fcompResult);
        printf("\n\nfloat: Result is %s (paceval_fmathv)", charBuffer500);
    }
    else
        printf("\n\nError occured for paceval_fmathv(): %s", CreateErrorMessage(charBuffer500, errType, 500));

    //Calculate float interval results
    fcompResult = paceval_fmathvi(NULL, &errType, &fminResultInterval, &fmaxResultInterval,
                                  functionStr, 2, "x y", 0.5, 2.0);
    if (errType == PACEVAL_ERR_NO_ERROR)
    {
        paceval_fConvertFloatToString(charBuffer500, fcompResult);
        printf("\n\nfloat: Result is %s (paceval_fmathvi)", charBuffer500);
        paceval_fConvertFloatToString(charBuffer500, fminResultInterval);
        printf("\nfloat: Interval min. result is %s (paceval_fmathvi)", charBuffer500);
        paceval_fConvertFloatToString(charBuffer500, fmaxResultInterval);
        printf("\nfloat: Interval max. result is %s (paceval_fmathvi)", charBuffer500);
    }
    else
        printf("\n\nError occured for paceval_fmathvi(): %s", CreateErrorMessage(charBuffer500, errType, 500));

    //Calculate double results
    dcompResult = paceval_dmathv(NULL, &errType, functionStr, 2, "x y", 0.5, 2.0);
    if (errType == PACEVAL_ERR_NO_ERROR)
    {
        paceval_dConvertFloatToString(charBuffer500, dcompResult);
        printf("\n\ndouble: Result is %s (paceval_dmathv)", charBuffer500);
    }
    else
        printf("\n\nError occured for paceval_dmathvi(): %s", CreateErrorMessage(charBuffer500, errType, 500));

    //Calculate double interval results
    dcompResult = paceval_dmathvi(NULL, &errType, &dminResultInterval, &dmaxResultInterval,
                                  functionStr, 2, "x y", 0.5, 2.0);
    if (errType == PACEVAL_ERR_NO_ERROR)
    {
        paceval_dConvertFloatToString(charBuffer500, dcompResult);
        printf("\n\ndouble: Result is %s (paceval_dmathvi)", charBuffer500);
        paceval_dConvertFloatToString(charBuffer500, dminResultInterval);
        printf("\ndouble: Interval min. result is %s (paceval_dmathvi)", charBuffer500);
        paceval_dConvertFloatToString(charBuffer500, dmaxResultInterval);
        printf("\ndouble: Interval max. result is %s (paceval_dmathvi)", charBuffer500);
    }
    else
        printf("\n\nError occured for paceval_dmathvi(): %s", CreateErrorMessage(charBuffer500, errType, 500));

    if (sizeof(long double) == sizeof(double))
    {
        if (paceval_fmathv(NULL, &errType, "paceval_LibrarySupportsLongDouble", 0, "", NULL) != 0)
            printf("\n\nYour paceval. library supports long double.");

        printf("\n\n%s",
               CreateErrorMessage(charBuffer500, PACEVAL_ERR_COMPUTATION_USER_COMPILER_NOT_SUPPORTS_LONG_DOUBLE, 500));

        printf("\nE.g. Microsoft Visual C++ does not support long double.");
        printf("\nExcerpt from the MSDN : 'Previous(...) versions of Microsoft C / C++ and Microsoft Visual C++ supported");
        printf("\nthe long double, 80-bit precision data type. (...), however, the long double data type");
        printf("\nmaps to the double, 64-bit precision data type.'");
    }
    else
    {
        //Calculate long double results
        ldcompResult = paceval_ldmathv(NULL, &errType, functionStr, 2, "x y", 0.5L, 2.0L);
        if (errType == PACEVAL_ERR_NO_ERROR)
        {
            paceval_ldConvertFloatToString(charBuffer500, ldcompResult);
            printf("\n\nlong double: Result is %s (paceval_ldmathv)", charBuffer500);
        }
        else
            printf("\n\nError occured for paceval_ldmathv(): %s", CreateErrorMessage(charBuffer500, errType,500));

        //Calculate long double interval results
        ldcompResult = paceval_ldmathvi(NULL, &errType, &ldminResultInterval, &ldmaxResultInterval,
                                        functionStr, 2, "x y", 0.5L, 2.0L);
        if (errType == PACEVAL_ERR_NO_ERROR)
        {
            paceval_ldConvertFloatToString(charBuffer500, ldcompResult);
            printf("\n\nlong double: Result is %s (paceval_ldmathvi)", charBuffer500);
            paceval_ldConvertFloatToString(charBuffer500, ldminResultInterval);
            printf("\nlong double: Interval min. result is %s (paceval_ldmathvi)", charBuffer500);
            paceval_ldConvertFloatToString(charBuffer500, ldmaxResultInterval);
            printf("\nlong double: Interval max. result is %s (paceval_ldmathvi)", charBuffer500);
        }
        else
        {
            printf("\n\nError occured for paceval_ldmathvi(): %s", CreateErrorMessage(charBuffer500, errType, 500));
        }
    }

    if ((int)paceval_fmathv(NULL, &errType, "paceval_NumberThreadUsages", 0, "", NULL) > 0)
        printf("\n\n[Threads usages: %d]", (int)paceval_fmathv(NULL, &errType, "paceval_NumberThreadUsages", 0, "", NULL));
    if ((int)paceval_fmathv(NULL, &errType, "paceval_NumberCacheHitsACC", 0, "", NULL) > 0)
        printf("\n[Cache hits ACC: %d]", (int)paceval_fmathv(NULL, &errType, "paceval_NumberCacheHitsACC", 0, "", NULL));
    printf("\n[Number of cores: %d]", (int)paceval_fmathv(NULL, &errType, "paceval_NumberOfCores", 0, "", NULL));
    printf("\n[paceval. Version number: %1.3g]", paceval_fmathv(NULL, &errType, "paceval_VersionNumber", 0, "", NULL));

    paceval_FreeLibrary();

    printf("\n\nClick RETURN twice");

    while ((getchar()) != '\n') {}
    while ((getchar()) != '\n') {}
    return  0;
}

#if defined(__BORLANDC__)
#define sinf		sin
#define cosf		cos
#if defined(__clang__)
#endif //#if defined(__clang__)
#endif //#if defined(__BORLANDC__)

bool paceval_callbackUserFunction1(const int useCalculationPrecision_in,
                                   const long double* valueFieldAsLongDouble,
                                   long double* resultAsLongDouble,
                                   const double* valueFieldAsDouble,
                                   double* resultAsDouble,
                                   const float* valueFieldAsFloat,
                                   float* resultAsFloat)
{
    switch (useCalculationPrecision_in)
    {
    case PACEVAL_CALCULATION_PRECISION_LONG_DOUBLE:
    {
        *resultAsLongDouble =
            sinl(*valueFieldAsLongDouble) * cosl(*valueFieldAsLongDouble);
        return true;
    }
    case PACEVAL_CALCULATION_PRECISION_DOUBLE:
    {
        *resultAsDouble =
            sin(*valueFieldAsDouble) * cos(*valueFieldAsDouble);
        return true;
    }
    case PACEVAL_CALCULATION_PRECISION_FLOAT:
    {
        *resultAsFloat =
            sinf(*valueFieldAsFloat) * cosf(*valueFieldAsFloat);
        return true;
    }
    }

    return false;
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

