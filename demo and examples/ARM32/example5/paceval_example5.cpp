//---------------------------------------------------------------------------
// Author(s) : paceval., see http://www.paceval.com
// File      : paceval_example5.cpp
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

void PrintErrorMessage(PACEVAL_HANDLE handle_pacevalComputation_in);
//---------------------------------------------------------------------------

int main(int argc, char* argv[])
{
    int errType;

    if (paceval_InitializeLibrary(NULL) != true)
    {
        printf("\n\n paceval_InitializeLibrary() failed");
        return 0;
    }

    printf("\n| This demo application shows the capabilities of paceval. in terms of |");
    printf("\n| its features for text based calculations. Please open the source    |");
    printf("\n| code file paceval_example5.cpp.                                      |");

    printf("\n\nA calculation in a paceval.-specific XML format will be saved");
    printf("\nto a file, read from a file and created.");

    //Write a calculation to the file paceval_XML_example5.txt
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

    //Read a calculation from the file paceval_XML_example5.txt
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
                    char versionString[500];

                    if (paceval_ReadParametersFromXML(readXMLStr, &functionStringLength,
                                                      &variablesStringLength, &numberOfVariables,
                                                      &valuesStringLength, functionStr, variablesStr, NULL,
                                                      &useInterval) == 0)
                    {
                        //Create the paceval-Computation object with the function from the file data
                        PACEVAL_HANDLE handle_pacevalComputation;

                        handle_pacevalComputation = paceval_CreateComputation(functionStr,
                                                    numberOfVariables, variablesStr,
                                                    useInterval, NULL);

                        printf("\n\nCalculation XML read from file paceval_XML_example5.txt with %d characters",
                               functionStringLength);

                        if (paceval_GetIsError(handle_pacevalComputation))
                        {
                            printf("\nand computation object creation failed for function");
                            printf("\n'%s' and variables '%s'.", functionStr, variablesStr);
                            PrintErrorMessage(handle_pacevalComputation);
                        }
                        else
                        {
                            printf("\nand computation object creation successful for function");
                            printf("\n'%s' and variables '%s'.", functionStr, variablesStr);

                            //now we can do cool stuff with the object
                            //...
                        }

                        paceval_GetComputationVersionString(handle_pacevalComputation, versionString);
                        printf("\n\n");
                        printf(versionString);

                        //Delete the paceval-Computation object
                        paceval_DeleteComputation(handle_pacevalComputation);
                    }

                    delete[] functionStr;
                    delete[] variablesStr;
                }
            }
            delete[] readXMLStr;
        }
    }

    paceval_FreeLibrary();

    printf("\n\nClick RETURN twice");

    while ((getchar()) != '\n') {}
    while ((getchar()) != '\n') {}
    return  0;
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
