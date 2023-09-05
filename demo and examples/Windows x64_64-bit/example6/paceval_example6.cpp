//---------------------------------------------------------------------------
// Copyright 1997-2014. Version 1.x Joerg Koenning - All rights reserved.
// Copyright 2015-2023. Version 2.x, 3.x, 4.x 2015-2023 paceval.[Registered Trade Mark]
//                                            All rights reserved.
// Author(s) : paceval., see http://www.paceval.com
// File      : paceval_example6.cpp
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

#include <iostream>
#include <fstream>

#if (defined(_WIN32) || defined(_WIN64))
#include <windows.h>
#endif

#include "../../system-independent/source_public/inc/paceval_main.h" //We include the paceval header

const char* CreateErrorMessage(char* messageBuffer, int pacevalErrorType, int lengthBuffer);
bool ReadCreationDataFromFiles(const char* mainFilename, unsigned int mainFilenameIndex,
                               unsigned long* functionStringLength_out,
                               unsigned long* variablesStringLength_out,
                               unsigned long* numberOfVariables_out,
                               char* functionString_out, char* variablesString_out);
void CalculateAndPresentFloatExample6(PACEVAL_HANDLE handle_pacevalComputations_in[],
                                      const char* fileForInference, unsigned long numberOfVariables_in, bool useInterval_in);
void CalculateAndPresentDoubleExample6(PACEVAL_HANDLE handle_pacevalComputations_in[],
                                       const char* fileForInference, unsigned long numberOfVariables_in, bool useInterval_in);
void CalculateAndPresentLongDoubleExample6(PACEVAL_HANDLE handle_pacevalComputations_in[],
        const char* fileForInference, unsigned long numberOfVariables_in, bool useInterval_in);
unsigned long paceval_getOSCurrentTime();
bool paceval_callbackStatus(const PACEVAL_HANDLE handle_pacevalComputation_in,
                            const paceval_eStatusTypes paceval_eStatus_in, const int percentageDone_in);
void PrintErrorMessage(PACEVAL_HANDLE handle_pacevalComputation_in);

//this function retrieves the variable out of 1..10 which holds the maximum value
//old variant without max-operator
/*
#define function_maxFrom10 "1*((x1>x2) AND (x1>x3) AND (x1>x4) AND (x1>x5) AND (x1>x6) AND (x1>x7) AND (x1>x8) AND (x1>x9) AND (x1>x10)) + \
                            2*((x2>x1) AND (x2>x3) AND (x2>x4) AND (x2>x5) AND (x2>x6) AND (x2>x7) AND (x2>x8) AND (x2>x9) AND (x2>x10)) + \
                            3*((x3>x1) AND (x3>x2) AND (x3>x4) AND (x3>x5) AND (x3>x6) AND (x3>x7) AND (x3>x8) AND (x3>x9) AND (x3>x10)) + \
                            4*((x4>x1) AND (x4>x2) AND (x4>x3) AND (x4>x5) AND (x4>x6) AND (x4>x7) AND (x4>x8) AND (x4>x9) AND (x4>x10)) + \
                            5*((x5>x1) AND (x5>x2) AND (x5>x3) AND (x5>x4) AND (x5>x6) AND (x5>x7) AND (x5>x8) AND (x5>x9) AND (x5>x10)) + \
                            6*((x6>x1) AND (x6>x2) AND (x6>x3) AND (x6>x4) AND (x6>x5) AND (x6>x7) AND (x6>x8) AND (x6>x9) AND (x6>x10)) + \
                            7*((x7>x1) AND (x7>x2) AND (x7>x3) AND (x7>x4) AND (x7>x5) AND (x7>x6) AND (x7>x8) AND (x7>x9) AND (x7>x10)) + \
                            8*((x8>x1) AND (x8>x2) AND (x8>x3) AND (x8>x4) AND (x8>x5) AND (x8>x6) AND (x8>x7) AND (x8>x9) AND (x8>x10)) + \
                            9*((x9>x1) AND (x9>x2) AND (x9>x3) AND (x9>x4) AND (x9>x5) AND (x9>x6) AND (x9>x7) AND (x9>x8) AND (x9>x10)) + \
                           10*((x10>x1) AND (x10>x2) AND (x10>x3) AND (x10>x4) AND (x10>x5) AND (x10>x6) AND (x10>x7) AND (x10>x8) AND (x10>x9))"   */

//new variant with max-operator
#define function_maxFrom10 "1*(x1 > (       x2 max x3 max x4 max x5 max x6 max x7 max x8 max x9 max x10)) + \
                            2*(x2 > (x1 max        x3 max x4 max x5 max x6 max x7 max x8 max x9 max x10)) + \
                            3*(x3 > (x1 max x2 max        x4 max x5 max x6 max x7 max x8 max x9 max x10)) + \
                            4*(x4 > (x1 max x2 max x3 max        x5 max x6 max x7 max x8 max x9 max x10)) + \
                            5*(x5 > (x1 max x2 max x3 max x4 max        x6 max x7 max x8 max x9 max x10)) + \
                            6*(x6 > (x1 max x2 max x3 max x4 max x5        max x7 max x8 max x9 max x10)) + \
                            7*(x7 > (x1 max x2 max x3 max x4 max x5 max x6 max        x8 max x9 max x10)) + \
                            8*(x8 > (x1 max x2 max x3 max x4 max x5 max x6 max x7 max        x9 max x10)) + \
                            9*(x9 > (x1 max x2 max x3 max x4 max x5 max x6 max x7 max x8 max        x10)) + \
                           10*(x10> (x1 max x2 max x3 max x4 max x5 max x6 max x7 max x8 max x9        ))"


//---------------------------------------------------------------------------

int main(int argc, char* argv[])
{
    int errType;
    char charBuffer500[500];
    PACEVAL_HANDLE handle_pacevalComputationsArray[10];
    bool success = true;
    unsigned long numberOfVariables = 0;
    char versionString[PACEVAL_MAXVER];
    int answerChar;
    bool useInterval;

    if (paceval_InitializeLibrary(NULL) != true)
    {
        printf("\n\n paceval_InitializeLibrary() failed");
        return 0;
    }

    printf("\n|----------------------------------------------------------------------|");
    printf("\n| This demo application shows the capabilities of paceval. in terms of |");
    printf("\n| its functionality for simultaneous calculations and artificial       |");
    printf("\n| neural networks (GetMultipleComputationsResults).                    |");
    printf("\n| Just open the file 'paceval_example6.cpp' to see its source code     |");
    printf("\n| (~700 lines).                                                        |");
    printf("\n|                                                                      |");
    printf("\n| see https://paceval.com/api/ for the API                             |");
    printf("\n|----------------------------------------------------------------------|");

    printf("\n\nThe handwritten numbers 0-9 are identified with 10 functions that");
    printf("\ndescribe the artificial neural network.");
    printf("\nEach function is >770,000 characters long and uses 784 variables that ");
    printf("\nrepresent 28x28 pixels in the image.\n");

    printf("\n\nDo you want to use Interval arithmetic [y/n]?");
    answerChar = getchar();
    while ((answerChar != 'y') && (answerChar != 'n'))
        answerChar = getchar();

    if (answerChar == 'n')
        useInterval = false;
    else
        useInterval = true;

    std::ofstream fileToWrite;
    fileToWrite.open("paceval_example6 reads and writes here.txt");
    if (fileToWrite.is_open())
    {
        fileToWrite << "please, see filename";
        fileToWrite.close();
    }

    /*
    //Alterative 1 : Create each paceval-Computation object
    //with paceval_CreateComputation
    for (unsigned int iCount = 0; iCount < 10; iCount++)
    {
        unsigned long functionStringLength = 0;
        unsigned long variablesStringLength = 0;
        char* functionString;
        char* variablesString;

        printf("\nCreate paceval-Computation object for function '%d'", iCount);
        success = ReadCreationDataFromFiles("paceval_CNN_", iCount,
                                            &functionStringLength, &variablesStringLength, &numberOfVariables,
                                            NULL, NULL);
        if (success == false)
            printf(" -- error in reading initiation data for creation from files");
        else
        {
            functionString = new char[functionStringLength];
            variablesString = new char[variablesStringLength];

            success = ReadCreationDataFromFiles("paceval_CNN_", iCount,
                                                &functionStringLength, &variablesStringLength, &numberOfVariables,
                                                functionString, variablesString);
            if (success == false)
                printf(" -- error in reading function data for creation from files");
            else
            {
                //Create the paceval-Computation objects
                handle_pacevalComputationsArray[iCount] = paceval_CreateComputation(functionString,
                        numberOfVariables, variablesString, useInterval, NULL);

                if (paceval_GetIsError(handle_pacevalComputationsArray[iCount]) == true)
                {
                    PrintErrorMessage(handle_pacevalComputationsArray[iCount]);
                    success = false;
                }

                printf(" -- done");
            }

            delete[] functionString;
            delete[] variablesString;
        }
    }
    */

    //Alterative 2 : Create paceval-Computation objects in one step
    //with paceval_CreateMultipleComputations
    {
        const char** functionStringsArray;
        char* functionStrings[10];
        char* variablesString = NULL;

        functionStringsArray = new const char*[10];

        for (unsigned int iCount = 0; iCount < 10; iCount++)
        {
            unsigned long functionStringLength = 0;
            unsigned long variablesStringLength = 0;

            printf("\nRead function for handwritten number '%d' from file", iCount);
            success = ReadCreationDataFromFiles("paceval_CNN_", iCount,
                                                &functionStringLength, &variablesStringLength, &numberOfVariables,
                                                NULL, NULL);
            if (success == false)
            {
                printf(" -- error in reading initiation data for creation from files");
                functionStrings[iCount] = NULL;
            }
            else
            {
                functionStrings[iCount] = new char[functionStringLength];
                functionStringsArray[iCount] = functionStrings[iCount];
                if (iCount == 0)
                {
                    variablesString = new char[variablesStringLength];
                    success = ReadCreationDataFromFiles("paceval_CNN_", iCount,
                                                        &functionStringLength, &variablesStringLength, &numberOfVariables,
                                                        functionStrings[iCount], variablesString);
                }
                else
                {
                    success = ReadCreationDataFromFiles("paceval_CNN_", iCount,
                                                        &functionStringLength, NULL, NULL,
                                                        functionStrings[iCount], NULL);
                }
                if (success == false)
                    printf(" -- error in reading function data for creation from files");
            }
        }
        //Create the paceval-Computation objects
        if (success == true)
        {
            printf("\nInitialize for ML inference and create paceval-Computation objects \nfor 10 functions '0' to '9'...");
            success = paceval_CreateMultipleComputations(handle_pacevalComputationsArray,
                      functionStringsArray, 10, numberOfVariables, variablesString, useInterval, &paceval_callbackStatus);
        }
        if (success == false)
            printf("\n -- error in creating paceval-Computation objects");
        else
            printf("\n -- success in creating paceval-Computation objects \n -> ready for ML inferences!");

        for (unsigned int iCount = 0; iCount < 10; iCount++)
        {
            if (functionStrings[iCount] != NULL)
                delete[] functionStringsArray[iCount];
        }

        delete[] functionStringsArray;
        delete[] variablesString;
    }


    if (success == true)
    {
        printf("\n\nClick RETURN twice to start inferences for 3 images each with float, double and long double.");

        while ((getchar()) != '\n') {}
        while ((getchar()) != '\n') {}

        printf("\n\n_____________________________________________");
        printf("\nStart inference on the picture 'image01'");
        printf("\nwith float, double and long double precision:");
        printf("\n_____________________________________________");

        printf("\n\n --- float ---------  (paceval_fGetMultipleComputationsResults)");
        CalculateAndPresentFloatExample6(handle_pacevalComputationsArray, "image01ValuesAsText.txt", numberOfVariables, useInterval);
        printf("\n\n\n --- double -------- (paceval_dGetMultipleComputationsResults)");
        CalculateAndPresentDoubleExample6(handle_pacevalComputationsArray, "image01ValuesAsText.txt", numberOfVariables, useInterval);
        printf("\n\n\n --- long double --- (paceval_ldGetMultipleComputationsResults)");
        //Check if compiler supports long double
        if (sizeof(long double) != sizeof(double))
            CalculateAndPresentLongDoubleExample6(handle_pacevalComputationsArray, "image01ValuesAsText.txt", numberOfVariables, useInterval);

        if (sizeof(long double) == sizeof(double))
        {
            printf("\n\n%s",
                   CreateErrorMessage(charBuffer500, PACEVAL_ERR_COMPUTATION_USER_COMPILER_NOT_SUPPORTS_LONG_DOUBLE, 500));
            printf("\n(see below)");
        }

        printf("\n\n_____________________________________________");
        printf("\nStart inference on the picture 'image02'");
        printf("\nwith float, double and long double precision:");
        printf("\n_____________________________________________");

        printf("\n\n --- float ---------  (paceval_fGetMultipleComputationsResults)");
        CalculateAndPresentFloatExample6(handle_pacevalComputationsArray, "image02ValuesAsText.txt", numberOfVariables, useInterval);
        printf("\n\n\n --- double -------- (paceval_dGetMultipleComputationsResults)");
        CalculateAndPresentDoubleExample6(handle_pacevalComputationsArray, "image02ValuesAsText.txt", numberOfVariables, useInterval);
        printf("\n\n\n --- long double --- (paceval_ldGetMultipleComputationsResults)");
        //Check if compiler supports long double
        if (sizeof(long double) != sizeof(double))
            CalculateAndPresentLongDoubleExample6(handle_pacevalComputationsArray, "image02ValuesAsText.txt", numberOfVariables, useInterval);

        if (sizeof(long double) == sizeof(double))
        {
            printf("\n\n%s",
                   CreateErrorMessage(charBuffer500, PACEVAL_ERR_COMPUTATION_USER_COMPILER_NOT_SUPPORTS_LONG_DOUBLE, 500));
            printf("\n(see below)");
        }

        printf("\n\n_____________________________________________");
        printf("\nStart inference on the picture 'image03'");
        printf("\nwith float, double and long double precision:");
        printf("\n_____________________________________________");

        printf("\n\n --- float ---------  (paceval_fGetMultipleComputationsResults)");
        CalculateAndPresentFloatExample6(handle_pacevalComputationsArray, "image03ValuesAsText.txt", numberOfVariables, useInterval);
        printf("\n\n\n --- double -------- (paceval_dGetMultipleComputationsResults)");
        CalculateAndPresentDoubleExample6(handle_pacevalComputationsArray, "image03ValuesAsText.txt", numberOfVariables, useInterval);
        printf("\n\n\n --- long double --- (paceval_ldGetMultipleComputationsResults)");
        //Check if compiler supports long double
        if (sizeof(long double) != sizeof(double))
            CalculateAndPresentLongDoubleExample6(handle_pacevalComputationsArray, "image03ValuesAsText.txt", numberOfVariables, useInterval);

        if (sizeof(long double) == sizeof(double))
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

        paceval_GetComputationVersionString(handle_pacevalComputationsArray[0], versionString);
        printf("\n\n");
        printf(versionString);

        if ((int)paceval_fmathv(NULL, &errType, "paceval_NumberThreadUsages", 0, "", NULL) > 0)
            printf("\n[Threads usages: %d]", (int)paceval_fmathv(NULL, &errType, "paceval_NumberThreadUsages", 0, "", NULL));
        if ((int)paceval_fmathv(NULL, &errType, "paceval_NumberCacheHitsACC", 0, "", NULL) > 0)
            printf("\n[Cache hits ACC: %d]", (int)paceval_fmathv(NULL, &errType, "paceval_NumberCacheHitsACC", 0, "", NULL));
        printf("\n[Number of cores: %d]", (int)paceval_fmathv(NULL, &errType, "paceval_NumberOfCores", 0, "", NULL));

        for (unsigned int iCount = 0; iCount < 10; iCount++)
        {
            paceval_DeleteComputation(handle_pacevalComputationsArray[iCount]);
        }
    }

    paceval_FreeLibrary();

    printf("\n\nClick RETURN twice");

    while ((getchar()) != '\n') {}
    while ((getchar()) != '\n') {}
    return  0;
}

void CalculateAndPresentFloatExample6(PACEVAL_HANDLE handle_pacevalComputations_in[],
                                      const char* fileForInference, unsigned long numberOfVariables_in, bool useInterval_in)
{
    //Initialize float variables-array from file
    std::ifstream fileValuesToRead(fileForInference, std::ios::in | std::ios::binary | std::ios::ate);
    if ((fileValuesToRead.is_open()) && (fileValuesToRead.tellg() > 0))
    {
        char charBuffer500[500];
        bool hasError = false;
        int errType;
        int imageIdentifiedAs;
        std::streampos sizeFile;
        char* readValuesStr;
        unsigned int cCount;
        unsigned int fCount;
        long errPosition;
        unsigned long startTime;
        unsigned long endTime;

        float* fvaluesVariablesArray = new float[numberOfVariables_in];
        float* fResults = new float[10];
        float* fminResultsInterval = new float[10];
        float* fmaxResultsInterval = new float[10];
        int* errorTypes = new int[10];

        sizeFile = fileValuesToRead.tellg();
        readValuesStr = new char[(unsigned int)sizeFile + 1];
        fileValuesToRead.seekg(0, std::ios_base::beg);
        fileValuesToRead.read(readValuesStr, sizeFile);
        readValuesStr[(unsigned int)sizeFile] = '\0';
        fileValuesToRead.close();

        cCount = 0;
        fCount = 0;
        for (unsigned int iCount = 0; iCount < sizeFile; iCount++)
        {
            if (readValuesStr[iCount] != ';')
            {
                charBuffer500[cCount] = readValuesStr[iCount];
                cCount++;
            }
            else
            {
                charBuffer500[cCount] = '\0';
                fvaluesVariablesArray[fCount] = paceval_fConvertStringToFloat(charBuffer500, &errType, &errPosition,
                                                false, NULL, NULL);
                fCount++;
                cCount = 0;
            }
        }

        delete[] readValuesStr;

        //Calculate float results
        startTime = paceval_getOSCurrentTime();
        hasError = paceval_fGetMultipleComputationsResults(handle_pacevalComputations_in,
                   10, &fvaluesVariablesArray[0],
                   &fResults[0], &fminResultsInterval[0], &fmaxResultsInterval[0],
                   &errorTypes[0]);
        endTime = paceval_getOSCurrentTime();

        if (hasError)
        {
            for (unsigned int iCount = 0; iCount < 10; iCount++)
            {
                printf("\nFunction '%d' with float result cannot be trusted.", iCount);
            }
        }
        else for (unsigned int iCount = 0; iCount < 10; iCount++)
            {
                paceval_fConvertFloatToString(charBuffer500, fResults[iCount]);
                printf("\nFor function '%d' float: Result is %s", iCount, charBuffer500);

                if (useInterval_in)
                {
                    paceval_fConvertFloatToString(charBuffer500, fminResultsInterval[iCount]);
                    printf(" : Interval [%s; ", charBuffer500);

                    paceval_fConvertFloatToString(charBuffer500, fmaxResultsInterval[iCount]);
                    printf("%s]", charBuffer500);
                }
            }

        imageIdentifiedAs = paceval_fmathv(NULL, &errType, function_maxFrom10,
                                           10, "x1 x2 x3 x4 x5 x6 x7 x8 x9 x10",
                                           fResults[0], fResults[1], fResults[2], fResults[3], fResults[4],
                                           fResults[5], fResults[6], fResults[7], fResults[8], fResults[9]);

        if (imageIdentifiedAs > 0)
            printf("\n   Picture identified as number '%d'. [Time needed: %d ms]", imageIdentifiedAs - 1, endTime - startTime);
        else
            printf("\n   No number identified in the picture. [Time needed: %d ms]", endTime - startTime);

        delete[] fvaluesVariablesArray;
        delete[] fResults;
        delete[] fminResultsInterval;
        delete[] fmaxResultsInterval;
        delete[] errorTypes;
    }
    else
    {
        if (fileValuesToRead.is_open())
            fileValuesToRead.close();

        printf("\n -- error in reading from file: ");
        printf(fileForInference);
    }
}

void CalculateAndPresentDoubleExample6(PACEVAL_HANDLE handle_pacevalComputations_in[],
                                       const char* fileForInference, unsigned long numberOfVariables_in, bool useInterval_in)
{
    //Initialize double variables-array from file
    std::ifstream fileValuesToRead(fileForInference, std::ios::in | std::ios::binary | std::ios::ate);
    if ((fileValuesToRead.is_open()) && (fileValuesToRead.tellg() > 0))
    {
        char charBuffer500[500];
        bool hasError;
        int errType;
        int imageIdentifiedAs;
        std::streampos sizeFile;
        char* readValuesStr;
        unsigned int cCount;
        unsigned int fCount;
        long errPosition;
        unsigned long startTime;
        unsigned long endTime;

        double* dvaluesVariablesArray = new double[numberOfVariables_in];
        double* dResults = new double[10];
        double* dminResultsInterval = new double[10];
        double* dmaxResultsInterval = new double[10];
        int* errorTypes = new int[10];

        sizeFile = fileValuesToRead.tellg();
        readValuesStr = new char[(unsigned int)sizeFile + 1];
        fileValuesToRead.seekg(0, std::ios_base::beg);
        fileValuesToRead.read(readValuesStr, sizeFile);
        readValuesStr[(unsigned int)sizeFile] = '\0';
        fileValuesToRead.close();

        cCount = 0;
        fCount = 0;
        for (unsigned int iCount = 0; iCount < sizeFile; iCount++)
        {
            if (readValuesStr[iCount] != ';')
            {
                charBuffer500[cCount] = readValuesStr[iCount];
                cCount++;
            }
            else
            {
                charBuffer500[cCount] = '\0';
                dvaluesVariablesArray[fCount] = paceval_dConvertStringToFloat(charBuffer500, &errType, &errPosition,
                                                false, NULL, NULL);
                fCount++;
                cCount = 0;
            }
        }

        delete[] readValuesStr;

        //Calculate double results
        startTime = paceval_getOSCurrentTime();
        hasError = paceval_dGetMultipleComputationsResults(handle_pacevalComputations_in,
                   10, &dvaluesVariablesArray[0],
                   &dResults[0], &dminResultsInterval[0], &dmaxResultsInterval[0],
                   &errorTypes[0]);
        endTime = paceval_getOSCurrentTime();

        for (unsigned int iCount = 0; iCount < 10; iCount++)
        {
            paceval_dConvertFloatToString(charBuffer500, dResults[iCount]);
            printf("\nFor function '%d' double: Result is %s", iCount, charBuffer500);

            if (useInterval_in)
            {
                paceval_dConvertFloatToString(charBuffer500, dminResultsInterval[iCount]);
                printf(" : Interval [%s; ", charBuffer500);

                paceval_dConvertFloatToString(charBuffer500, dmaxResultsInterval[iCount]);
                printf("%s]", charBuffer500);
            }
        }

        imageIdentifiedAs = paceval_dmathv(NULL, &errType, function_maxFrom10,
                                           10, "x1 x2 x3 x4 x5 x6 x7 x8 x9 x10",
                                           dResults[0], dResults[1], dResults[2], dResults[3], dResults[4],
                                           dResults[5], dResults[6], dResults[7], dResults[8], dResults[9]);

        if (imageIdentifiedAs > 0)
            printf("\n   Picture identified as number '%d'. [Time needed: %d ms]", imageIdentifiedAs - 1, endTime - startTime);
        else
            printf("\n   No number identified in the picture. [Time needed: %d ms]", endTime - startTime);

        delete[] dvaluesVariablesArray;
        delete[] dResults;
        delete[] dminResultsInterval;
        delete[] dmaxResultsInterval;
        delete[] errorTypes;
    }
    else
    {
        if (fileValuesToRead.is_open())
            fileValuesToRead.close();

        printf("\n -- error in reading from file: ");
        printf(fileForInference);
    }
}

void CalculateAndPresentLongDoubleExample6(PACEVAL_HANDLE handle_pacevalComputations_in[],
        const char* fileForInference, unsigned long numberOfVariables_in, bool useInterval_in)
{
    //Initialize long double variables-array from file
    std::ifstream fileValuesToRead(fileForInference, std::ios::in | std::ios::binary | std::ios::ate);
    if ((fileValuesToRead.is_open()) && (fileValuesToRead.tellg() > 0))
    {
        char charBuffer500[500];
        bool hasError;
        int imageIdentifiedAs;
        std::streampos sizeFile;
        char* readValuesStr;
        unsigned int cCount;
        unsigned int fCount;
        int errType;
        long errPosition;
        unsigned long startTime;
        unsigned long endTime;

        long double* ldvaluesVariablesArray = new long double[numberOfVariables_in];
        long double* ldResults = new long double[10];
        long double* ldminResultsInterval = new long double[10];
        long double* ldmaxResultsInterval = new long double[10];
        int* errorTypes = new int[10];

        sizeFile = fileValuesToRead.tellg();
        readValuesStr = new char[(unsigned int)sizeFile + 1];
        fileValuesToRead.seekg(0, std::ios_base::beg);
        fileValuesToRead.read(readValuesStr, sizeFile);
        readValuesStr[(unsigned int)sizeFile] = '\0';
        fileValuesToRead.close();

        cCount = 0;
        fCount = 0;
        for (unsigned int iCount = 0; iCount < sizeFile; iCount++)
        {
            if (readValuesStr[iCount] != ';')
            {
                charBuffer500[cCount] = readValuesStr[iCount];
                cCount++;
            }
            else
            {
                charBuffer500[cCount] = '\0';
                ldvaluesVariablesArray[fCount] = paceval_ldConvertStringToFloat(charBuffer500, &errType, &errPosition,
                                                 false, NULL, NULL);
                fCount++;
                cCount = 0;
            }
        }

        delete[] readValuesStr;

        //Calculate long double results
        startTime = paceval_getOSCurrentTime();
        hasError = paceval_ldGetMultipleComputationsResults(handle_pacevalComputations_in,
                   10, &ldvaluesVariablesArray[0],
                   &ldResults[0], &ldminResultsInterval[0], &ldmaxResultsInterval[0],
                   &errorTypes[0]);
        endTime = paceval_getOSCurrentTime();

        for (unsigned int iCount = 0; iCount < 10; iCount++)
        {
            paceval_ldConvertFloatToString(charBuffer500, ldResults[iCount]);
            printf("\nFor function '%d' long double: Result is %s", iCount, charBuffer500);

            if (useInterval_in)
            {
                paceval_ldConvertFloatToString(charBuffer500, ldminResultsInterval[iCount]);
                printf(" : Interval [%s; ", charBuffer500);

                paceval_ldConvertFloatToString(charBuffer500, ldmaxResultsInterval[iCount]);
                printf("%s]", charBuffer500);
            }
        }

        imageIdentifiedAs = paceval_ldmathv(NULL, &errType, function_maxFrom10,
                                            10, "x1 x2 x3 x4 x5 x6 x7 x8 x9 x10",
                                            ldResults[0], ldResults[1], ldResults[2], ldResults[3], ldResults[4],
                                            ldResults[5], ldResults[6], ldResults[7], ldResults[8], ldResults[9]);

        if (imageIdentifiedAs > 0)
            printf("\n   Picture identified as number '%d'. [Time needed: %d ms]", imageIdentifiedAs - 1, endTime - startTime);
        else
            printf("\n   No number identified in the picture. [Time needed: %d ms]", endTime - startTime);

        delete[] ldvaluesVariablesArray;
        delete[] ldminResultsInterval;
        delete[] ldmaxResultsInterval;
        delete[] ldResults;
        delete[] errorTypes;
    }
    else
    {
        if (fileValuesToRead.is_open())
            fileValuesToRead.close();

        printf("\n -- error in reading from file: ");
        printf(fileForInference);
    }
}

bool ReadCreationDataFromFiles(const char* mainFilename, unsigned int mainFilenameIndex,
                               unsigned long* functionStringLength_out,
                               unsigned long* variablesStringLength_out,
                               unsigned long* numberOfVariables_out,
                               char* functionString_out, char* variablesString_out)
{
    char* mainFilenamePlusExt = new char[strlen(mainFilename) + 100];
    char charBuffer500[500];
    bool success = true;

    strcpy(mainFilenamePlusExt, mainFilename);
    strcat(mainFilenamePlusExt, "functionStringforNumber_");
    paceval_dConvertFloatToString(charBuffer500, mainFilenameIndex);
    strcat(mainFilenamePlusExt, charBuffer500);
    strcat(mainFilenamePlusExt, ".txt");

    std::ifstream fileToRead(mainFilenamePlusExt, std::ios::in|std::ios::binary|std::ios::ate);
    if (fileToRead.is_open())
    {
        std::streampos sizeFile;

        sizeFile = fileToRead.tellg();
        fileToRead.seekg(0, std::ios_base::beg);
        *functionStringLength_out = (unsigned int)sizeFile + 1;
        if (functionString_out != NULL)
        {
            fileToRead.read(functionString_out, sizeFile);
            functionString_out[*functionStringLength_out - 1] = '\0';
        }
        fileToRead.close();
    }
    else
    {
        success = false;
    }
    delete[] mainFilenamePlusExt;

    if ((success == true) && (numberOfVariables_out != NULL))
    {
        mainFilenamePlusExt = new char[strlen(mainFilename) + 100];

        strcpy(mainFilenamePlusExt, mainFilename);
        strcat(mainFilenamePlusExt, "numberOfVariablesAsText.txt");

        std::ifstream fileToRead(mainFilenamePlusExt, std::ios::in|std::ios::binary|std::ios::ate);
        if (fileToRead.is_open())
        {
            char* numberOfVariablesString;
            int errorType;

            std::streampos sizeFile;

            sizeFile = fileToRead.tellg();
            fileToRead.seekg(0, std::ios_base::beg);
            numberOfVariablesString = new char[((unsigned int)sizeFile) + 1];
            fileToRead.read(numberOfVariablesString, sizeFile);
            numberOfVariablesString[(unsigned int)sizeFile] = '\0';
            fileToRead.close();

            *numberOfVariables_out = (unsigned long)paceval_dConvertStringToFloat(numberOfVariablesString,
                                     &errorType, NULL, false, NULL, NULL);

            delete[] numberOfVariablesString;
        }
        else
        {
            success = false;
        }
        delete[] mainFilenamePlusExt;
    }

    if ((success == true) && (variablesStringLength_out != NULL))
    {
        mainFilenamePlusExt = new char[strlen(mainFilename) + 100];

        strcpy(mainFilenamePlusExt, mainFilename);
        strcat(mainFilenamePlusExt, "variablesString.txt");

        std::ifstream fileToRead(mainFilenamePlusExt, std::ios::in|std::ios::binary|std::ios::ate);
        if (fileToRead.is_open())
        {
            std::streampos sizeFile;

            sizeFile = fileToRead.tellg();
            fileToRead.seekg(0, std::ios_base::beg);
            *variablesStringLength_out = (unsigned int)sizeFile + 1;
            if (variablesString_out != NULL)
            {
                fileToRead.read(variablesString_out, sizeFile);
                variablesString_out[*variablesStringLength_out - 1] = '\0';
            }
            fileToRead.close();
        }
        else
        {
            success = false;
        }
        delete[] mainFilenamePlusExt;
    }

    return success;
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

unsigned long paceval_getOSCurrentTime()
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

bool paceval_callbackStatus(const PACEVAL_HANDLE handle_pacevalComputation_in,
                            const paceval_eStatusTypes paceval_eStatus_in, const int percentageDone_in)
{
    if (paceval_eStatus_in == PACEVAL_STATUS_ANALYSIS_PROGRESS)
    {
        int errType;

        if ((int)paceval_fmathv(NULL, &errType, "(percentageDone=25) OR (percentageDone=50) OR (percentageDone=75)",
                                1, "percentageDone", (float)percentageDone_in))
        {
            printf(".");
        }
    }

    return true;
}

void PrintErrorMessage(PACEVAL_HANDLE handle_pacevalComputation_in)
{
    int maxMessageDetailsLength;
    char* errMessage;
    char* errDetails;

    maxMessageDetailsLength = paceval_CreateErrorInformationText(handle_pacevalComputation_in,
                              NULL, NULL);
    errMessage = new char[maxMessageDetailsLength];
    errDetails = new char[maxMessageDetailsLength];

    maxMessageDetailsLength = paceval_CreateErrorInformationText(handle_pacevalComputation_in,
                              errMessage, errDetails);
    printf(errMessage);
    printf(errDetails);

    delete[] errMessage;
    delete[] errDetails;
}
