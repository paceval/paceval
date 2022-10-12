//---------------------------------------------------------------------------
// Copyright 1997-2014. Version 1.x Joerg Koenning - All rights reserved.
// Copyright 2015-2022. Version 2.x, 3.x, 4.x 2015-2022 paceval.[Registered Trade Mark]
//                                            All rights reserved.
// Author(s) : paceval., see http://www.paceval.com
// File      : paceval_example6_server.cpp
//---------------------------------------------------------------------------

//---------------------------------------------------------------------------
#if defined(_MSC_VER) //we don't use the Microsoft specific functions
#define _CRT_SECURE_NO_WARNINGS
#pragma warning(disable : 4996)

#if !defined(_WIN64) //#if !defined(_WIN64)
#pragma comment(lib, "curl/lib-win32/libcurl.dll.a")
#else
#pragma comment(lib, "curl/lib-win64/libcurl.dll.a")
#endif
#endif //#if defined(_MSC_VER)

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <string>

#include <iostream>
#include <fstream>

#if (defined(_WIN32) || defined(_WIN64))
#include <windows.h>
#endif

//#include "curl/curl.h" //see https://curl.se/download.html

#include "../../system-independent/source_public/inc/paceval_main.h" //We include the paceval main header
#include "../../system-independent/source_public/inc/paceval_net.h" //We include the paceval networking header

bool ReadServerString(char* readStr);
bool WriteServerString(char* writeStr);
bool ReadCreationDataFromFiles(const char* mainFilename, unsigned int mainFilenameIndex,
                               unsigned long* functionStringLength_out,
                               unsigned long* variablesStringLength_out,
                               unsigned long* numberOfVariables_out,
                               char* functionString_out, char* variablesString_out);
void CalculateAndPresentDoubleExample6(char* pacevalServerStr_in, const char* handle_pacevalComputationsArrayAsString_in,
	const char* fileForInference, unsigned long numberOfVariables_in);

//this function retrieves the variable out of 1..10 which holds the maximum value
#define function_maxFrom10 "1*((x1>x2) AND (x1>x3) AND (x1>x4) AND (x1>x5) AND (x1>x6) AND (x1>x7) AND (x1>x8) AND (x1>x9) AND (x1>x10)) + \
                            2*((x2>x1) AND (x2>x3) AND (x2>x4) AND (x2>x5) AND (x2>x6) AND (x2>x7) AND (x2>x8) AND (x2>x9) AND (x2>x10)) + \
                            3*((x3>x1) AND (x3>x2) AND (x3>x4) AND (x3>x5) AND (x3>x6) AND (x3>x7) AND (x3>x8) AND (x3>x9) AND (x3>x10)) + \
                            4*((x4>x1) AND (x4>x2) AND (x4>x3) AND (x4>x5) AND (x4>x6) AND (x4>x7) AND (x4>x8) AND (x4>x9) AND (x4>x10)) + \
                            5*((x5>x1) AND (x5>x2) AND (x5>x3) AND (x5>x4) AND (x5>x6) AND (x5>x7) AND (x5>x8) AND (x5>x9) AND (x5>x10)) + \
                            6*((x6>x1) AND (x6>x2) AND (x6>x3) AND (x6>x4) AND (x6>x5) AND (x6>x7) AND (x6>x8) AND (x6>x9) AND (x6>x10)) + \
                            7*((x7>x1) AND (x7>x2) AND (x7>x3) AND (x7>x4) AND (x7>x5) AND (x7>x6) AND (x7>x8) AND (x7>x9) AND (x7>x10)) + \
                            8*((x8>x1) AND (x8>x2) AND (x8>x3) AND (x8>x4) AND (x8>x5) AND (x8>x6) AND (x8>x7) AND (x8>x9) AND (x8>x10)) + \
                            9*((x9>x1) AND (x9>x2) AND (x9>x3) AND (x9>x4) AND (x9>x5) AND (x9>x6) AND (x9>x7) AND (x9>x8) AND (x9>x10)) + \
                           10*((x10>x1) AND (x10>x2) AND (x10>x3) AND (x10>x4) AND (x10>x5) AND (x10>x6) AND (x10>x7) AND (x10>x8) AND (x10>x9))"

//---------------------------------------------------------------------------

int main(int argc, char* argv[])
{
	char pacevalServerStr[500];
	int errType;
	char errTypeString[PACEVAL_MAXERR];
	char errMessageString[PACEVAL_MAXERR];
    bool success = true;
    unsigned long numberOfVariables = 0;
	char handle_pacevalComputationAsString[50];
	char handle_pacevalComputationsArrayAsString[10 * 50];

    if (paceval_InitializeLibrary(NULL) != true)
    {
        printf("\n\n paceval_InitializeLibrary() failed");
        return 0;
    }

	printf("\n|----------------------------------------------------------------------|");
    printf("\n| This demo application shows the capabilities of paceval. in terms of |");
    printf("\n| its functionality for simultaneous calculations and artificial       |");
    printf("\n| neural networks (GetMultipleComputationsResults). This example uses  |");
    printf("\n| a remote server for the calculations.                                                        |");
	printf("\n| Just open the file 'paceval_example6_server.cpp' to see its source   |");
	printf("\n| code (~450 lines).                                                   |");
	printf("\n|                                                                      |");
	printf("\n| see https://paceval.com/api/ for the API                             |");
	printf("\n|----------------------------------------------------------------------|");

    printf("\n\nThe handwritten numbers 0-9 are identified with 10 functions that");
    printf("\ndescribe the artificial neural network.");
    printf("\nEach function is >770,000 characters long and uses 784 variables that ");
    printf("\nrepresent 28x28 pixels in the image.\n");

	ReadServerString(pacevalServerStr);

	printf("\n\nProvide the name or address/port of your paceval. server, ");
	printf("\ne.g. http://localhost:8080 or http://paceval-service.com ");
	if (strlen(pacevalServerStr) > 0)
	{
		printf("\n(Just press Y and RETURN if you want to use \nthis server - ");
		printf(pacevalServerStr);
		printf(")");
	}
	printf(": ");
	scanf("%500s", pacevalServerStr);

	if ((strcmp(pacevalServerStr, "y") == 0) || (strcmp(pacevalServerStr, "Y") == 0))
		ReadServerString(pacevalServerStr);
	else
		WriteServerString(pacevalServerStr);

    std::ofstream fileToWrite;
    fileToWrite.open("paceval_example6 reads and writes here.txt");
    if (fileToWrite.is_open())
    {
        fileToWrite << "please, see filename";
        fileToWrite.close();
    }

	strcpy(handle_pacevalComputationsArrayAsString, "");

    //Creates each paceval-Computation object
    //with paceval_Remote_CreateComputation
    for (unsigned int iCount = 0; iCount < 10; iCount++)
    {
        unsigned long functionStringLength = 0;
        unsigned long variablesStringLength = 0;
        char* functionString;
        char* variablesString;

        printf("\nCreate paceval-Computation object remote for function '%d'", iCount);
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
                //Creates the paceval-Computation objects
				success = paceval_Remote_CreateComputation(pacevalServerStr, handle_pacevalComputationAsString,
					functionString, numberOfVariables, variablesString, false, &errType, &errTypeString[0], &errMessageString[0]);

                if (success == false)
                {
					printf("\n -- error in creating paceval-Computation objects");
                    success = false;
                }
				else
				{
					strcat(handle_pacevalComputationsArrayAsString, handle_pacevalComputationAsString);
					if (iCount != 10 - 1)
					{
						strcat(handle_pacevalComputationsArrayAsString, ";");
					}
					printf(" -- done");
				}
            }

            delete[] functionString;
            delete[] variablesString;
        }
    }

    if (success == true) 
    {
        printf("\n\nClick RETURN twice to start remote inferences for 3 images each with double precision.");

        while ((getchar()) != '\n') {}
        while ((getchar()) != '\n') {}

		//Starts the inference process for the three images
		{
			printf("\n\n_____________________________________________");
			printf("\nStart inference on the picture 'image01'");
			printf("\nwith double precision:");
			printf("\n_____________________________________________");

			printf("\n\n\n --- double -------- (remote paceval_dGetMultipleComputationsResults)");
			CalculateAndPresentDoubleExample6(pacevalServerStr, handle_pacevalComputationsArrayAsString, "image01ValuesAsText.txt", numberOfVariables);

			printf("\n\n_____________________________________________");
			printf("\nStart inference on the picture 'image02'");
			printf("\nwith double precision:");
			printf("\n_____________________________________________");

			printf("\n\n\n --- double -------- (remote paceval_dGetMultipleComputationsResults)");
			CalculateAndPresentDoubleExample6(pacevalServerStr, handle_pacevalComputationsArrayAsString, "image02ValuesAsText.txt", numberOfVariables);

			printf("\n\n_____________________________________________");
			printf("\nStart inference on the picture 'image03'");
			printf("\nwith double precision:");
			printf("\n_____________________________________________");

			printf("\n\n\n --- double -------- (remote paceval_dGetMultipleComputationsResults)");
			CalculateAndPresentDoubleExample6(pacevalServerStr, handle_pacevalComputationsArrayAsString, "image03ValuesAsText.txt", numberOfVariables);
		}

		printf("\n\n[Threads usages remote ACC: %d]", (int)paceval_dRemote_mathv(pacevalServerStr, NULL, "paceval_NumberThreadUsages", 0, "", false, &errType, NULL, NULL, NULL));
		printf("\n[Cache hits remote ACC: %d]", (int)paceval_dRemote_mathv(pacevalServerStr, NULL, "paceval_NumberCacheHitsACC", 0, "", false, &errType, NULL, NULL, NULL));
		printf("\n[Number of cores local: %d]", (int)paceval_fmathv(NULL, &errType, "paceval_NumberOfCores", 0, "", NULL));
		printf("\n[Number of cores remote: %d]", (int)paceval_dRemote_mathv(pacevalServerStr, NULL, "paceval_NumberOfCores", 0, "", false, &errType, NULL, NULL, NULL));

		printf("\n[paceval. Version number local: %1.3g]", paceval_fmathv(NULL, &errType, "paceval_VersionNumber", 0, "", NULL));
		printf("\n[paceval. Version number remote: %1.3g]", paceval_dRemote_mathv(pacevalServerStr, NULL, "paceval_VersionNumber", 0, "", false, &errType, NULL, NULL, NULL));
    }

    paceval_FreeLibrary();

    printf("\n\nClick RETURN twice");

    while ((getchar()) != '\n') {}
    while ((getchar()) != '\n') {}
    return  0;
}

void CalculateAndPresentDoubleExample6(char* pacevalServerStr_in, const char* handle_pacevalComputationsArrayAsString_in,
                                       const char* fileForInference, unsigned long numberOfVariables_in)
{
    //Initializes double variables-array from file
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
		double timeComputeRemote;

        double* dvaluesVariablesArray = new double[numberOfVariables_in];
        double* dResults = new double[10];
        int* errorTypes = new int[10];
		bool success = true;

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

        //Calculates double results
		success = paceval_dRemote_GetMultipleComputationsResults(pacevalServerStr_in,
			handle_pacevalComputationsArrayAsString_in,
			10,	numberOfVariables_in, &dvaluesVariablesArray[0],
			&dResults[0], NULL, NULL,
			&hasError, &errorTypes[0],
			&timeComputeRemote);

        for (unsigned int iCount = 0; iCount < 10; iCount++)
        {
            paceval_dConvertFloatToString(charBuffer500, dResults[iCount]);
            printf("\nFor function '%d' double: Result is %s", iCount, charBuffer500);
        }

        imageIdentifiedAs = paceval_dmathv(NULL, &errType, function_maxFrom10,
                                           10, "x1 x2 x3 x4 x5 x6 x7 x8 x9 x10",
                                           dResults[0], dResults[1], dResults[2], dResults[3], dResults[4],
                                           dResults[5], dResults[6], dResults[7], dResults[8], dResults[9]);

        if (imageIdentifiedAs > 0)
            printf("\n   Picture identified as number '%d'. [Time needed: %d ms]", imageIdentifiedAs - 1, (unsigned long)(timeComputeRemote * 1000));
        else
            printf("\n   No number identified in the picture. [Time needed: %d ms]", (unsigned long)(timeComputeRemote * 1000));

        delete[] dvaluesVariablesArray;
        delete[] dResults;
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

bool ReadServerString(char* readStr)
{
	strcpy(readStr, "");

	std::ifstream fileToRead("paceval_server.ini", std::ios::in | std::ios::binary | std::ios::ate);
	if (fileToRead.is_open())
	{
		std::streampos sizeFile;

		sizeFile = fileToRead.tellg();
		fileToRead.seekg(0, std::ios_base::beg);
		fileToRead.read(readStr, sizeFile);
		readStr[sizeFile] = '\0';
		fileToRead.close();

		return true;
	}
	return false;
}

bool WriteServerString(char* writeStr)
{
	std::ofstream fileToWrite;
	fileToWrite.open("paceval_server.ini");
	if (fileToWrite.is_open())
	{
		fileToWrite << writeStr;
		fileToWrite.close();

		return true;
	}
	return false;
}
