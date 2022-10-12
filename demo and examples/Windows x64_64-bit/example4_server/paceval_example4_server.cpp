//---------------------------------------------------------------------------
// Copyright 1997-2014. Version 1.x Joerg Koenning - All rights reserved.
// Copyright 2015-2022. Version 2.x, 3.x, 4.x 2015-2022 paceval.[Registered Trade Mark]
//                                            All rights reserved.
// Author(s) : paceval., see http://www.paceval.com
// File      : paceval_example4_server.cpp
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

#include <iostream>
#include <fstream>

#include "../../system-independent/source_public/inc/paceval_main.h" //We include the paceval header
#include "../../system-independent/source_public/inc/paceval_net.h" //We include the paceval networking header

bool ReadServerString(char* readStr);
bool WriteServerString(char* writeStr);
void CalculateAndPresentDoubleExample4(char* pacevalServerStr_in);

char functionStrSin[] = "sin(x)*y";
char functionStrCos[] = "cos(x)*y";
char functionStrTan[] = "tan(x)*y";
//---------------------------------------------------------------------------

int main(int argc, char* argv[])
{
	char pacevalServerStr[500];
    int errType;

    if (paceval_InitializeLibrary(NULL) != true)
    {
        printf("\n\n paceval_InitializeLibrary() failed");
        return 0;
    }

	printf("\n|----------------------------------------------------------------------|");
    printf("\n| This demo application shows the capabilities of paceval. in terms of |");
    printf("\n| its features for simultaneous calculations with a remote server      |");
    printf("\n| (GetMultipleComputationsResults).                                    |");
	printf("\n| Just open the file 'paceval_example4_server.cpp' to see its source   |");
	printf("\n| code (~300 lines).                                                   |");
	printf("\n|                                                                      |");
	printf("\n| see https://paceval.com/api/ for the API                             |");
	printf("\n|----------------------------------------------------------------------|");

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

    printf("\n\nFor these functions:");
    printf("\n f(x,y)=%s", functionStrSin);
    printf("\n f(x,y)=%s", functionStrCos);
    printf("\n f(x,y)=%s", functionStrTan);
    printf("\nand the given variables x=2.5, y=1 we get these results.");

    printf("\n\n\n --- double --------");
    CalculateAndPresentDoubleExample4(pacevalServerStr);

	printf("\n\n[Threads usages remote ACC: %d]", (int)paceval_dRemote_mathv(pacevalServerStr, NULL, "paceval_NumberThreadUsages", 0, "", false, &errType, NULL, NULL, NULL));
	printf("\n[Cache hits remote ACC: %d]", (int)paceval_dRemote_mathv(pacevalServerStr, NULL, "paceval_NumberCacheHitsACC", 0, "", false, &errType, NULL, NULL, NULL));
	printf("\n[Number of cores local: %d]", (int)paceval_fmathv(NULL, &errType, "paceval_NumberOfCores", 0, "", NULL));
	printf("\n[Number of cores remote: %d]", (int)paceval_dRemote_mathv(pacevalServerStr, NULL, "paceval_NumberOfCores", 0, "", false, &errType, NULL, NULL, NULL));

	printf("\n[paceval. Version number local: %1.3g]", paceval_fmathv(NULL, &errType, "paceval_VersionNumber", 0, "", NULL));
	printf("\n[paceval. Version number remote: %1.3g]", paceval_dRemote_mathv(pacevalServerStr, NULL, "paceval_VersionNumber", 0, "", false, &errType, NULL, NULL, NULL));

    paceval_FreeLibrary();

    printf("\n\nClick RETURN twice");

    while ((getchar()) != '\n') {}
    while ((getchar()) != '\n') {}
    return  0;
}

void CalculateAndPresentDoubleExample4(char* pacevalServerStr_in)
{
    char charBuffer500[500];
    bool hasError;
	int errType;
	char errTypeString[PACEVAL_MAXERR];
	char errMessageString[PACEVAL_MAXERR];
	bool success = true;
	double timeComputeRemote;

    double* dvaluesVariablesArray = new double[2];
    double* dResults = new double[3];
    double* dminResultIntervals = new double[3];
    double* dmaxResultIntervals = new double[3];
    int* errorTypes = new int[3];

    dvaluesVariablesArray[0] = 2.5;
    dvaluesVariablesArray[1] = 1.0;

    //Calculates double results
    {
		char handle_pacevalComputationSinAsString[50];
		char handle_pacevalComputationCosAsString[50];
		char handle_pacevalComputationTanAsString[50];
		char handle_pacevalComputationsArrayAsString[3 * 50];

        PACEVAL_HANDLE* handle_pacevalComputationsArray = new PACEVAL_HANDLE[3];

        //Creates the paceval-Computation objects
		success = paceval_Remote_CreateComputation(pacevalServerStr_in, handle_pacevalComputationSinAsString,
			"sin(x)*y", 2, "x y", false, &errType, &errTypeString[0], &errMessageString[0]);
		if (success == true)
		{
			success = paceval_Remote_CreateComputation(pacevalServerStr_in, handle_pacevalComputationCosAsString,
				"cos(x)*y", 2, "x y", false, &errType, &errTypeString[0], &errMessageString[0]);

			if (success == true)
			{
				success = paceval_Remote_CreateComputation(pacevalServerStr_in, handle_pacevalComputationTanAsString,
					"tan(x)*y", 2, "x y", false, &errType, &errTypeString[0], &errMessageString[0]);
			}
		}

		if (success == false)
		{
			printf("\n -- error in creating paceval-Computation objects");
			success = false;
		}
		else
		{
			strcpy(handle_pacevalComputationsArrayAsString, handle_pacevalComputationSinAsString);
			strcat(handle_pacevalComputationsArrayAsString, ";");
			strcat(handle_pacevalComputationsArrayAsString, handle_pacevalComputationCosAsString);
			strcat(handle_pacevalComputationsArrayAsString, ";");
			strcat(handle_pacevalComputationsArrayAsString, handle_pacevalComputationTanAsString);
		}

		//Calculates double results
		success = paceval_dRemote_GetMultipleComputationsResults(pacevalServerStr_in,
			handle_pacevalComputationsArrayAsString,
			3, 2, &dvaluesVariablesArray[0],
			&dResults[0], NULL, NULL,
			&hasError, &errorTypes[0],
			&timeComputeRemote);

        printf("\nFor function: f(x,y)=%s (paceval_dRemote_GetMultipleComputationsResults)", functionStrSin);
        paceval_dConvertFloatToString(charBuffer500, dResults[0]);
        printf("\ndouble: Result is %s", charBuffer500);

        printf("\n\nFor function: g(x,y)=%s (paceval_dRemote_GetMultipleComputationsResults)", functionStrCos);
        paceval_dConvertFloatToString(charBuffer500, dResults[1]);
        printf("\ndouble: Result is %s", charBuffer500);

        printf("\n\nFor function: h(x,y)=%s (paceval_dRemote_GetMultipleComputationsResults)", functionStrTan);
        paceval_dConvertFloatToString(charBuffer500, dResults[2]);
        printf("\ndouble: Result is %s", charBuffer500);
		printf("\n[Remote computing time: <%d ms]", (unsigned long)ceil(timeComputeRemote * 1000));
    }

    //Calculate double interval results
    {
		char handle_pacevalComputationSinAsString_i[50];
		char handle_pacevalComputationCosAsString_i[50];
		char handle_pacevalComputationTanAsString_i[50];
		char handle_pacevalComputationsArrayAsString_i[3 * 50];

        //Create the paceval-Computation objects with trusted intervals (TINC)
		success = paceval_Remote_CreateComputation(pacevalServerStr_in, handle_pacevalComputationSinAsString_i,
			"sin(x)*y", 2, "x y", true, &errType, &errTypeString[0], &errMessageString[0]);
		if (success == true)
		{
			success = paceval_Remote_CreateComputation(pacevalServerStr_in, handle_pacevalComputationCosAsString_i,
				"cos(x)*y", 2, "x y", true, &errType, &errTypeString[0], &errMessageString[0]);

			if (success == true)
			{
				success = paceval_Remote_CreateComputation(pacevalServerStr_in, handle_pacevalComputationTanAsString_i,
					"tan(x)*y", 2, "x y", true, &errType, &errTypeString[0], &errMessageString[0]);
			}
		}

		if (success == false)
		{
			printf("\n -- error in creating paceval-Computation objects");
			success = false;
		}
		else
		{
			strcpy(handle_pacevalComputationsArrayAsString_i, handle_pacevalComputationSinAsString_i);
			strcat(handle_pacevalComputationsArrayAsString_i, ";");
			strcat(handle_pacevalComputationsArrayAsString_i, handle_pacevalComputationCosAsString_i);
			strcat(handle_pacevalComputationsArrayAsString_i, ";");
			strcat(handle_pacevalComputationsArrayAsString_i, handle_pacevalComputationTanAsString_i);
		}

		//Calculates double results with trusted intervals (TINC)
		success = paceval_dRemote_GetMultipleComputationsResults(pacevalServerStr_in,
			handle_pacevalComputationsArrayAsString_i,
			3, 2, &dvaluesVariablesArray[0],
			&dResults[0], &dminResultIntervals[0], &dmaxResultIntervals[0],
			&hasError, &errorTypes[0],
			&timeComputeRemote);

        printf("\n\n\nFor function: f(x,y)=%s  with trusted intervals (TINC)", functionStrSin);
        paceval_dConvertFloatToString(charBuffer500, dResults[0]);
        printf("\ndouble: Result is %s (paceval_dRemote_GetMultipleComputationsResults)", charBuffer500);
        paceval_dConvertFloatToString(charBuffer500, dminResultIntervals[0]);
        printf("\ndouble: Interval min. result is %s (paceval_dRemote_GetMultipleComputationsResults)", charBuffer500);
        paceval_dConvertFloatToString(charBuffer500, dmaxResultIntervals[0]);
        printf("\ndouble: Interval max. result is %s (paceval_dRemote_GetMultipleComputationsResults)", charBuffer500);

        printf("\n\nFor function: g(x,y)=%s  with trusted intervals (TINC)", functionStrCos);
        paceval_dConvertFloatToString(charBuffer500, dResults[1]);
        printf("\ndouble: Result is %s (paceval_dRemote_GetMultipleComputationsResults)", charBuffer500);
        paceval_dConvertFloatToString(charBuffer500, dminResultIntervals[1]);
        printf("\ndouble: Interval min. result is %s (paceval_dRemote_GetMultipleComputationsResults)", charBuffer500);
        paceval_dConvertFloatToString(charBuffer500, dmaxResultIntervals[1]);
        printf("\ndouble: Interval max. result is %s (paceval_dRemote_GetMultipleComputationsResults)", charBuffer500);

        printf("\n\nFor function: h(x,y)=%s  with trusted intervals (TINC)", functionStrTan);
        paceval_dConvertFloatToString(charBuffer500, dResults[2]);
        printf("\ndouble: Result is %s (paceval_dRemote_GetMultipleComputationsResults)", charBuffer500);
        paceval_dConvertFloatToString(charBuffer500, dminResultIntervals[2]);
        printf("\ndouble: Interval min. result is %s (paceval_dRemote_GetMultipleComputationsResults)", charBuffer500);
        paceval_dConvertFloatToString(charBuffer500, dmaxResultIntervals[2]);
        printf("\ndouble: Interval max. result is %s (paceval_dRemote_GetMultipleComputationsResults)", charBuffer500);
		printf("\n[Remote computing time with trusted intervals: <%d ms]\n", (unsigned long)ceil(timeComputeRemote * 1000));
	}

    delete[] dvaluesVariablesArray;
    delete[] dResults;
    delete[] dminResultIntervals;
    delete[] dmaxResultIntervals;
    delete[] errorTypes;
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