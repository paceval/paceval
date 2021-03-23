//---------------------------------------------------------------------------
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

#include <iostream>
#include <fstream>

#include "../../system-independent/source_public/inc/paceval_main.h" //We include the paceval header

const char* CreateErrorMessage(char* messageBuffer, int pacevalErrorType, int lengthBuffer);
bool ReadCreationDataFromFiles(const char* mainFilename, unsigned int mainFilenameIndex,
                               unsigned long* functionStringLength_out,
                               unsigned long* variablesStringLength_out,
                               unsigned long* numberOfVariables_out,
                               char* functionString_out, char* variablesString_out);
void CalculateAndPresentFloatExample6(PACEVAL_HANDLE handle_pacevalComputations_in[],
                                      unsigned long numberOfVariables_in);
void CalculateAndPresentDoubleExample6(PACEVAL_HANDLE handle_pacevalComputations_in[],
                                       unsigned long numberOfVariables_in);
void CalculateAndPresentLongDoubleExample6(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfVariables_in);

//---------------------------------------------------------------------------

int main(int argc, char* argv[])
{
    int errType;
    char charBuffer500[500];
    PACEVAL_HANDLE handle_pacevalComputationsArray[10];
    bool success = true;
    unsigned long numberOfVariables = 0;
    char versionString[PACEVAL_MAXVER];

    if (paceval_InitializeLibrary(NULL) != true)
    {
        printf("\n\n paceval_InitializeLibrary() failed");
        return 0;
    }

    printf("\n| This demo application shows the capabilities of paceval. in terms of |");
    printf("\n| its features for simultaneous calculations and neural networks.      |");
    printf("\n| Please open the source code file paceval_example6.cpp.               |");

    printf("\n\nFor 10 functions identifying handwritten numbers 0-9.");
    printf("\nEach function is >920.000 characters and uses 784 variables.\n");

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
                        numberOfVariables, variablesString, false, NULL);

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

            printf("\nRead function '%d' from file", iCount);
            success = ReadCreationDataFromFiles("paceval_CNN_", iCount,
                                                &functionStringLength, &variablesStringLength, &numberOfVariables,
                                                NULL, NULL);
            if (success == false)
                printf(" -- error in reading initiation data for creation from files");
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
            printf("\nCreate paceval-Computation objects for 10 functions '0' to '9'");
            success = paceval_CreateMultipleComputations(handle_pacevalComputationsArray,
                      functionStringsArray, 10, numberOfVariables, variablesString, false, NULL);
        }
        if (success == false)
            printf(" -- error in creating paceval-Computation objects");
        else
            for (unsigned int iCount = 0; iCount < 10; iCount++)
                delete[] functionStringsArray[iCount];

        delete[] functionStringsArray;
        delete[] variablesString;
    }

    if (success == true)
    {
        printf("\n\n --- float ---------  (paceval_fGetMultipleComputationsResults)");
        CalculateAndPresentFloatExample6(handle_pacevalComputationsArray, numberOfVariables);
        printf("\n\n\n --- double -------- (paceval_dGetMultipleComputationsResults)");
        CalculateAndPresentDoubleExample6(handle_pacevalComputationsArray, numberOfVariables);

        printf("\n\n\n --- long double --- (paceval_ldGetMultipleComputationsResults)");
        //Check if compiler supports long double
        if (sizeof(long double) != sizeof(double))
        {
            CalculateAndPresentLongDoubleExample6(handle_pacevalComputationsArray, numberOfVariables);
        }
        else
        {
            if (paceval_fmathv(NULL, &errType, "paceval_LibrarySupportsLongDouble", 0, "", NULL) != 0)
                printf("\nYour paceval. library supports long double.");
            else
                printf("\nYour paceval. library not supports long double.");

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

        printf("\n\n[Threads usages: %d]", (int)paceval_fmathv(NULL, &errType, "paceval_NumberThreadUsages", 0, "", NULL));

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
                                      unsigned long numberOfVariables_in)
{
    char charBuffer500[500];
    bool hasError = false;

    float* fvaluesVariablesArray = new float[numberOfVariables_in];
    float* fResults = new float[10];
    int* errorTypes = new int[10];

    //Initialize float variables-array from file
    std::ifstream fileValuesToRead("image01ValuesAsText.txt", std::ios::in | std::ios::binary | std::ios::ate);
    if (fileValuesToRead.is_open())
    {
        std::streampos sizeFile;
        char* readValuesStr;
        unsigned int cCount;
        unsigned int fCount;
        int errType;
        long errPosition;

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
    }

    //Calculate float results
    hasError = paceval_fGetMultipleComputationsResults(handle_pacevalComputations_in,
               10, &fvaluesVariablesArray[0],
               &fResults[0], NULL, NULL,
               &errorTypes[0]);

    for (unsigned int iCount = 0; iCount < 10; iCount++)
    {
        paceval_fConvertFloatToString(charBuffer500, fResults[iCount]);
        printf("\nFor function '%d' float: Result is %s", iCount, charBuffer500);
        if (fResults[iCount] > 3.5)
            printf("\n   Picture identified as number '%d'", iCount);
    }

    delete[] fvaluesVariablesArray;
    delete[] fResults;
    delete[] errorTypes;
}

void CalculateAndPresentDoubleExample6(PACEVAL_HANDLE handle_pacevalComputations_in[],
                                       unsigned long numberOfVariables_in)
{
    char charBuffer500[500];
    bool hasError;

    double* dvaluesVariablesArray = new double[numberOfVariables_in];
    double* dResults = new double[10];
    int* errorTypes = new int[10];

    //Initialize double variables-array from file
    std::ifstream fileValuesToRead("image01ValuesAsText.txt", std::ios::in | std::ios::binary | std::ios::ate);
    if (fileValuesToRead.is_open())
    {
        std::streampos sizeFile;
        char* readValuesStr;
        unsigned int cCount;
        unsigned int fCount;
        int errType;
        long errPosition;

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
    }

    //Calculate double results
    hasError = paceval_dGetMultipleComputationsResults(handle_pacevalComputations_in,
               10, &dvaluesVariablesArray[0],
               &dResults[0], NULL, NULL,
               &errorTypes[0]);

    for (unsigned int iCount = 0; iCount < 10; iCount++)
    {
        paceval_dConvertFloatToString(charBuffer500, dResults[iCount]);
        printf("\nFor function '%d' double: Result is %s", iCount, charBuffer500);
        if (dResults[iCount] > 3.5)
            printf("\n   Picture identified as number '%d'", iCount);
    }

    delete[] dvaluesVariablesArray;
    delete[] dResults;
    delete[] errorTypes;
}

void CalculateAndPresentLongDoubleExample6(PACEVAL_HANDLE handle_pacevalComputations_in[],
        unsigned long numberOfVariables_in)
{
    char charBuffer500[500];
    bool hasError;

    long double* ldvaluesVariablesArray = new long double[numberOfVariables_in];
    long double* ldResults = new long double[10];
    int* errorTypes = new int[10];

    //Initialize long double variables-array from file
    std::ifstream fileValuesToRead("image01ValuesAsText.txt", std::ios::in | std::ios::binary | std::ios::ate);
    if (fileValuesToRead.is_open())
    {
        std::streampos sizeFile;
        char* readValuesStr;
        unsigned int cCount;
        unsigned int fCount;
        int errType;
        long errPosition;

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
    }

    //Calculate long double results
    hasError = paceval_ldGetMultipleComputationsResults(handle_pacevalComputations_in,
               10, &ldvaluesVariablesArray[0],
               &ldResults[0], NULL, NULL,
               &errorTypes[0]);

    for (unsigned int iCount = 0; iCount < 10; iCount++)
    {
        paceval_ldConvertFloatToString(charBuffer500, ldResults[iCount]);
        printf("\nFor function '%d' long double: Result is %s", iCount, charBuffer500);
        if (ldResults[iCount] > 3.5)
            printf("\n   Picture identified as number '%d'", iCount);
    }

    delete[] ldvaluesVariablesArray;
    delete[] ldResults;
    delete[] errorTypes;
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


