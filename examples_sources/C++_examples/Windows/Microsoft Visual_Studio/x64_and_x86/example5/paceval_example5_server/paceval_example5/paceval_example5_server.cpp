//---------------------------------------------------------------------------
// Copyright 2022. Version 4.x 2022 paceval.[Registered Trade Mark]
//                             All rights reserved.
// Author(s) : paceval., see http://www.paceval.com
// File      : paceval_example5_server.cpp
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

    if (paceval_InitializeLibrary(NULL) != true)
    {
        printf("\n\n paceval_InitializeLibrary() failed");
        return 0;
    }

	printf("\n|----------------------------------------------------------------------|");
    printf("\n| This demo application shows the capabilities of paceval. in terms of |");
    printf("\n| its features for text based calculations (ReadParametersFromXML).    |");
	printf("\n| Just open the file 'paceval_example5_server.cpp' to see its source   |");
	printf("\n| code (~250 lines).                                                   |");
	printf("\n|                                                                      |");
	printf("\n| see https://paceval.com/api/ for the API                             |");
	printf("\n|----------------------------------------------------------------------|");

    printf("\n\nA calculation in a paceval.-specific XML format will be saved");
    printf("\nto a file, read from a file and created.");

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

    //Writes a calculation to the file paceval_XML_example5.txt
    {
        unsigned long lengthXML;
        char* writeXMLStr;

        lengthXML = paceval_CreateXMLFromParameters(NULL, "-sin(x*cos(x))^(1/y)", 2, "x y",
                    "0.5 2", true);
        if (lengthXML > 0)
        {
            writeXMLStr = new char[lengthXML];
            lengthXML = paceval_CreateXMLFromParameters(writeXMLStr, "-sin(x*cos(x))^(1/y)", 2, "x y",
                        "0.5 2", true);

            std::ofstream fileToWrite;
            fileToWrite.open ("paceval_XML_example5.txt");
            if (fileToWrite.is_open())
            {
                fileToWrite << writeXMLStr;
                fileToWrite.close();

                printf("\n\nCalculation XML saved to file paceval_XML_example5.txt");
            }
            else
            {
                printf("\n\nError in writing to paceval_XML_example5.txt - please, set the correct access rights in your operating system to the directory");
            }
            delete[] writeXMLStr;
        }
    }

    //Reads a calculation from the file paceval_XML_example5.txt
    {
        std::ifstream fileToRead("paceval_XML_example5.txt", std::ios::in|std::ios::binary|std::ios::ate);
        if (fileToRead.is_open())
        {
            char* readXMLStr;
            std::streampos sizeFile;

            sizeFile = fileToRead.tellg();
            fileToRead.seekg(0, std::ios_base::beg);
            readXMLStr = new char[(unsigned int)sizeFile];
            fileToRead.read(readXMLStr, sizeFile);
            fileToRead.close();

            {
                unsigned long functionStringLength;
                unsigned long variablesStringLength;
                unsigned long numberOfVariables;
                unsigned long valuesStringLength;
                bool useInterval;

                if (paceval_ReadParametersFromXML(readXMLStr, &functionStringLength,
                                                  &variablesStringLength, &numberOfVariables,
                                                  &valuesStringLength, NULL, NULL, NULL,
                                                  &useInterval) == 0)
                {
                    char* functionStr = new char[functionStringLength];
                    char* variablesStr = new char[variablesStringLength];

                    if (paceval_ReadParametersFromXML(readXMLStr, &functionStringLength,
                                                      &variablesStringLength, &numberOfVariables,
                                                      &valuesStringLength, functionStr, variablesStr, NULL,
                                                      &useInterval) == 0)
                    {
                        //Creates the paceval-Computation object with the function from the file data
						char handle_pacevalComputationAsString[50];
						bool success;
						int errType;
						char errTypeString[PACEVAL_MAXERR];
						char errMessageString[PACEVAL_MAXERR];

						success = paceval_Remote_CreateComputation(pacevalServerStr, handle_pacevalComputationAsString,
							functionStr, numberOfVariables, variablesStr,
							useInterval, &errType, &errTypeString[0], &errMessageString[0]);

                        printf("\n\nCalculation XML read from file paceval_XML_example5.txt with %d characters",
                               functionStringLength);

						if (success == false)
						{
							printf(errMessageString);
							printf(errTypeString);
						}
						else
						{
							unsigned long lengthInfoXML;

							printf("\nand remote computation object creation successful for function");
							printf("\n'%s' and variables '%s'.", functionStr, variablesStr);

							success = paceval_Remote_GetComputationInformationXML(pacevalServerStr, handle_pacevalComputationAsString, 
								&lengthInfoXML, NULL);
							if (lengthInfoXML > 0)
							{
								char* writeInfoXMLStr;

								writeInfoXMLStr = new char[lengthInfoXML];
								success = paceval_Remote_GetComputationInformationXML(pacevalServerStr, handle_pacevalComputationAsString,
									&lengthInfoXML, writeInfoXMLStr);

								std::ofstream fileToWrite;
								fileToWrite.open("paceval_InformationXML_example5.txt");
								if (fileToWrite.is_open())
								{
									fileToWrite << writeInfoXMLStr;
									fileToWrite.close();

									printf("\n\nInformation XML of remote computation saved to file 'paceval_InformationXML_example5.txt'");
								}
								else
								{
									printf("\n\nError in writing to paceval_InformationXML_example5.txt - please, set the correct access rights in your operating system to the directory");
								}
								delete[] writeInfoXMLStr;
							}

							//now we can do more cool stuff with the object
							//...
						}
                    }

                    delete[] functionStr;
                    delete[] variablesStr;
                }
            }
            delete[] readXMLStr;
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
