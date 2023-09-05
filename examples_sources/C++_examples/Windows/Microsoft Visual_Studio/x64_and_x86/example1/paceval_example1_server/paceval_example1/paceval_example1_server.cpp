//---------------------------------------------------------------------------
// Copyright 2023. Version 4.x 2023 paceval.[Registered Trade Mark]
//                             All rights reserved.
// Author(s) : paceval., see http://www.paceval.com
// File      : paceval_example1_server.cpp
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
#include <string>

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
    char functionStr[500];
    int errType;
    char errTypeString[PACEVAL_MAXERR];
    char errMessageString[PACEVAL_MAXERR];
    int answerChar;
    bool useInterval;
    char xvalStr[500];
    char yvalStr[500];
    double valuesVariablesArray[2];
    double compResult;
    double minResultInterval;
    double maxResultInterval;
    bool success;
    char handle_pacevalComputationAsString[50];

    if (paceval_InitializeLibrary(NULL) != true)
    {
        printf("\n\n paceval_InitializeLibrary() failed");
        return 0;
    }

    printf("\n|----------------------------------------------------------------------|");
    printf("\n| This demo application shows the possibilities of a server with       |");
    printf("\n| paceval. and connects to it via curl, https://curl.se/. Use the      |");
    printf("\n| simple mathematical notation and only a few lines of source code.    |");
    printf("\n| The trusted interval computation 'TINC' shows the interval in which  |");
    printf("\n| the true result is.                                                  |");
    printf("\n| Just open the file 'paceval_example1_server.cpp' to see its source   |");
    printf("\n| code (~240 lines).                                                   |");
    printf("\n|                                                                      |");
    printf("\n| see http://paceval.com/product-brief for the supported terms - e.g.  |");
    printf("\n| sin(x)*y+4.356                                                       |");
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

    printf("\n\nEnter a function to solve: f(x,y)=");
    scanf("%500s", functionStr);

    printf("\n\nDo you want to use Interval arithmetic [y/n]?");
    answerChar = getchar();
    while ((answerChar != 'y') && (answerChar != 'n'))
        answerChar = getchar();

    if (answerChar == 'n')
        useInterval = false;
    else
        useInterval = true;

    printf("\n\nYour paceval-server will now be contacted to create the remote");
    printf("\npaceval-computation object. Depending on the latency and");
    printf("\nperformance of your server or cluster, this may take a few seconds.");
    printf("\nPlease wait ...");

    //Creates the paceval-Computation object with the user's mathematical function
    success = paceval_Remote_CreateComputation(pacevalServerStr, handle_pacevalComputationAsString,
              functionStr, 2, "x;y", useInterval, &errType, &errTypeString[0], &errMessageString[0]);

    if (success == false)
    {
        printf(errMessageString);
        printf(errTypeString);
    }
    else
    {
        printf(" done!");
        while (true)
        {
            bool err = false;
            double minValue;
            double maxValue;
            long errPosition;
            double timeComputeRemote;

            printf("\n\nEnter the x value: x=");
            scanf("%255s", xvalStr);
            printf("Enter the y value: y=");
            scanf("%255s", yvalStr);

            //Converts the strings of the variables to floating point numbers
            valuesVariablesArray[0] = paceval_dConvertStringToFloat(xvalStr, &errType, &errPosition,
                                      true, &minValue, &maxValue);
            if (errType != PACEVAL_ERR_NO_ERROR)
            {
                printf("\nThe string of the variable x cannot be converted to a floating point number.");
                err = true;
            }

            valuesVariablesArray[1] = paceval_dConvertStringToFloat(yvalStr, &errType, &errPosition,
                                      true, &minValue, &maxValue);
            if (errType != PACEVAL_ERR_NO_ERROR)
            {
                printf("\nThe string of the variable y cannot be converted to a floating point number.");
                err = true;
            }

            if (err == false)
            {
                //Gets the result of the function on the user's variables
                if (useInterval == false)
                {
                    success = paceval_dRemote_GetComputationResult(pacevalServerStr, handle_pacevalComputationAsString,
                              2, valuesVariablesArray, &compResult, NULL, NULL, &errType, &errTypeString[0], &errMessageString[0], &timeComputeRemote);
                }
                else
                {
                    success = paceval_dRemote_GetComputationResult(pacevalServerStr, handle_pacevalComputationAsString,
                              2, valuesVariablesArray, &compResult, &minResultInterval, &maxResultInterval, &errType, &errTypeString[0], &errMessageString[0], &timeComputeRemote);
                }

                if (success == false)
                {
                    printf(errMessageString);
                    printf(errTypeString);
                }
                else
                {
                    char strcValue[25];

                    paceval_dConvertFloatToString(strcValue, compResult);
                    printf("\nResult is ");
                    printf(strcValue);

                    if (useInterval == true)
                    {
                        paceval_dConvertFloatToString(strcValue, minResultInterval);
                        printf("\nInterval min. result is ");
                        printf(strcValue);

                        paceval_dConvertFloatToString(strcValue, maxResultInterval);
                        printf("\nInterval max. result is ");
                        printf(strcValue);

                        printf("\n[Remote computing time : <%d ms]", (unsigned long)ceil(timeComputeRemote * 1000));
                    }
                }
            }

            printf("\n\nWould you like to calculate with other values for the variables [y/n]?");
            answerChar = getchar();
            while ((answerChar != 'y') && (answerChar != 'n'))
            {
                answerChar = getchar();
            }
            if (answerChar == 'n')
                break;
        }
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