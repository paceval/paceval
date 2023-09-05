//---------------------------------------------------------------------------
// Copyright 2023. Version 4.x 2023 paceval.[Registered Trade Mark]
//                             All rights reserved.
// Author(s) : paceval., see http://www.paceval.com
// File      : paceval_example2_server.cpp
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

#include "../../system-independent/source_public/inc/paceval_main.h" //We include the paceval main header
#include "../../system-independent/source_public/inc/paceval_net.h" //We include the paceval networking header

bool ReadServerString(char* readStr);
bool WriteServerString(char* writeStr);
//---------------------------------------------------------------------------

int main(int argc, char* argv[])
{
    char pacevalServerStr[500];
    int errType;
    char errTypeString[PACEVAL_MAXERR];
    char errMessageString[PACEVAL_MAXERR];
    char charBuffer500[500];
    double dcompResult;
    double dminResultInterval;
    double dmaxResultInterval;
    double valuesVariablesArray[2];
    double timeComputeRemote;

    char functionStr[] = "-sin(x*cos(x))^(1/y) + sin(y)*cos(y)";

    if (paceval_InitializeLibrary(NULL) != true)
    {
        printf("\n\n paceval_InitializeLibrary() failed");
        return 0;
    }

    printf("\n|----------------------------------------------------------------------|");
    printf("\n| This demo application shows the capabilities of paceval. in terms of |");
    printf("\n| its convenience functions (mathv and mathvi).                        |");
    printf("\n| Just open the file 'paceval_example2_server.cpp' to see its source   |");
    printf("\n| code (~180 lines).                                                   |");
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

    printf("\n\nFor this function: f(x,y)=%s", functionStr);
    printf("\nand the given variables x=0.5, y=2.0 we get these results.");

    valuesVariablesArray[0] = 0.5; //x value
    valuesVariablesArray[1] = 2.0; //y value

    //Calculates double results
    dcompResult = paceval_dRemote_mathv(pacevalServerStr, NULL,
                                        functionStr, 2, "x;y", valuesVariablesArray, &errType,
                                        &errTypeString[0], &errMessageString[0], &timeComputeRemote);

    if (errType == PACEVAL_ERR_NO_ERROR)
    {
        paceval_dConvertFloatToString(charBuffer500, dcompResult);
        printf("\n\nWithout Interval arithmetic:");
        printf("\ndouble: Result is %s (paceval_dRemote_mathv)", charBuffer500);
        printf("\n[Remote computing time : <%d ms]", (unsigned long)ceil(timeComputeRemote * 1000));
    }
    else
    {
        printf("\n\nError occured for paceval_dRemote_mathv(): ");
        printf(errMessageString);
        printf(errTypeString);
    }

    //Calculates double interval results
    dcompResult = paceval_dRemote_mathvi(pacevalServerStr, NULL,
                                         functionStr, 2, "x;y", valuesVariablesArray, &errType, &dminResultInterval, &dmaxResultInterval,
                                         &errTypeString[0], &errMessageString[0], &timeComputeRemote);
    if (errType == PACEVAL_ERR_NO_ERROR)
    {
        paceval_dConvertFloatToString(charBuffer500, dcompResult);
        printf("\n\nWith Interval arithmetic:");
        printf("\ndouble: Result is %s (paceval_dRemote_mathvi)", charBuffer500);
        paceval_dConvertFloatToString(charBuffer500, dminResultInterval);
        printf("\ndouble: Interval min. result is %s (paceval_dRemote_mathvi)", charBuffer500);
        paceval_dConvertFloatToString(charBuffer500, dmaxResultInterval);
        printf("\ndouble: Interval max. result is %s (paceval_dRemote_mathvi)", charBuffer500);
        printf("\n[Remote computing time : <%d ms]", (unsigned long)ceil(timeComputeRemote * 1000));
    }
    else
    {
        printf("\n\nError occured for paceval_dRemote_mathvi(): ");
        printf(errMessageString);
        printf(errTypeString);
    }

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