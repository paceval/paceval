//---------------------------------------------------------------------------
// Copyright 2022. Version 4.x 2022 paceval.[Registered Trade Mark]
//                             All rights reserved.
// Author(s) : paceval., see http://www.paceval.com
// File      : paceval_example3_server.cpp
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
#include <time.h>

#include <iostream>
#include <fstream>

#if (defined(_WIN32) || defined(_WIN64))
#include <windows.h>
#endif

#include "../../system-independent/source_public/inc/paceval_main.h" //We include the paceval header
#include "../../system-independent/source_public/inc/paceval_net.h" //We include the paceval networking header

bool ReadServerString(char* readStr);
bool WriteServerString(char* writeStr);

void CalculateAndPresentDoubleExample3(char* pacevalServerStr);

char functionStr[] = "-sin(x*cos(x))^(1/y)";
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
    printf("\n| its features for multiple remote calculations (CreateComputation and |");
	printf("\n| GetComputationResultExt, GetErrorInformation).                       |");
	printf("\n| Just open the file 'paceval_example3_server.cpp' to see its source   |");
	printf("\n| code (~260 lines).                                                   |");
	printf("\n|                                                                      |");
	printf("\n| Annotation: Depending on your network connection, the transfer of    |");
	printf("\n| the several megabytes of JSON data can take a few seconds.           |");
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

    printf("\n\nFor this function: f(x,y)=%s", functionStr);
    printf("\n100.000 calculations each are performed remote for the area x in [-10;10[.");
	printf("\nAll 100,000 results are then summed up locally to get the numerical integral.");

    CalculateAndPresentDoubleExample3(pacevalServerStr);

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

void CalculateAndPresentDoubleExample3(char* pacevalServerStr)
{
    char charBuffer500[500];
	double* dvaluesVariablesArrayExt = new double[2 * 100000];
	double* dResults = new double[100000];
    double* dminResultIntervals = new double[100000];
    double* dmaxResultIntervals = new double[100000];
    double dFastIntegral;
    double dminFastIntegralInterval;
    double dmaxFastIntegralInterval;
    int* errorTypes = new int[2 * 100000];
	bool hasError;
	int errType;
	long errPosition;
	char errTypeString[PACEVAL_MAXERR];
	char errOperator[PACEVAL_MAXERR];
	char errMessageString[PACEVAL_MAXERR];
	bool hasErrori;
	int errTypei;
	long errPositioni;
	char errTypeStringi[PACEVAL_MAXERR];
	char errOperatori[PACEVAL_MAXERR];
	char errMessageStringi[PACEVAL_MAXERR];
	bool success;
	bool successi;
	char handle_pacevalComputationAsString[50];
	char handle_pacevalComputationAsStringi[50];
	double timeComputeRemote;

    //Creates 2*100.000 values for the variables x and y
	double dareaDiff = (10.0 - (-10.0)) / 100000.0;

    for (unsigned long iCount = 0; iCount < 100000; iCount++)
    {
        dvaluesVariablesArrayExt[iCount * 2] = -10.0 + dareaDiff * iCount;
        dvaluesVariablesArrayExt[iCount * 2 + 1] = 0.5;
    }

    //Creates the paceval-Computation object
	success = paceval_Remote_CreateComputation(pacevalServerStr, handle_pacevalComputationAsString,
		functionStr, 2, "x y", false, &errType, &errTypeString[0], &errMessageString[0]);

    if (success == false)
	{
		paceval_Remote_GetErrorInformation(pacevalServerStr, handle_pacevalComputationAsString,
			&hasError,	&errType, &errPosition, &errTypeString[0], &errOperator[0], &errMessageString[0]);
		printf("\n\n");
		printf(errMessageString);
		printf(errTypeString);

		return;
	}

    //Creates the paceval-Computation object with trusted intervals (TINC)
 	successi = paceval_Remote_CreateComputation(pacevalServerStr, handle_pacevalComputationAsStringi,
		functionStr, 2, "x y", true, &errTypei, &errTypeStringi[0], &errMessageStringi[0]);

	if (successi == false)
	{
		paceval_Remote_GetErrorInformation(pacevalServerStr, handle_pacevalComputationAsStringi,
			&hasErrori, &errTypei, &errPositioni, &errTypeStringi[0], &errOperatori[0], &errMessageStringi[0]);
		printf("\n\n");
		printf(errMessageStringi);
		printf(errTypeStringi);

		return;
	}

    //Calculates double results
	printf("\n\n\n --- start double remote without interval arithmetic --------");
	printf("\nplease wait a few seconds for the data transfer...");
	successi = paceval_dRemote_GetComputationResultExt(pacevalServerStr, handle_pacevalComputationAsString, 2,
		&dvaluesVariablesArrayExt[0], 100000, &dResults[0], NULL, NULL,
		&hasError, &errorTypes[0], &timeComputeRemote);
 
    dFastIntegral = 0;
    for (unsigned long iCount = 0; iCount < 100000; iCount++)
    {
        if (errorTypes[iCount] == PACEVAL_ERR_NO_ERROR)
            dFastIntegral = dFastIntegral + (dResults[iCount] * dareaDiff);
    }
    paceval_dConvertFloatToString(charBuffer500, dFastIntegral);
    printf("\n\ndouble: Fast integral is %s (paceval_dRemote_GetComputationResultExt)\n[Remote computing time: <%d ms]", charBuffer500, (unsigned long)ceil(timeComputeRemote * 1000));

    //Calculates double interval results
	printf("\n\n\n --- start double remote with interval arithmetic --------");
	printf("\nplease wait a few seconds for the data transfer...");
    successi = paceval_dRemote_GetComputationResultExt(pacevalServerStr, handle_pacevalComputationAsStringi, 2,
		&dvaluesVariablesArrayExt[0], 100000, &dResults[0], &dminResultIntervals[0], &dmaxResultIntervals[0],
		&hasError, &errorTypes[0], &timeComputeRemote);
 
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
    printf("\n\ndouble: Fast integral is %s (paceval_dRemote_GetComputationResultExt with TINC)", charBuffer500);
    paceval_dConvertFloatToString(charBuffer500, dminFastIntegralInterval);
    printf("\ndouble: Interval min. fast integral is %s (paceval_dRemote_GetComputationResultExt with TINC)", charBuffer500);
    paceval_dConvertFloatToString(charBuffer500, dmaxFastIntegralInterval);
    printf("\ndouble: Interval max. fast integral is %s (paceval_dRemote_GetComputationResultExt with TINC)\n[Remote computing time: <%d ms]", charBuffer500, (unsigned long)ceil(timeComputeRemote * 1000));

    delete[] dvaluesVariablesArrayExt;
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

