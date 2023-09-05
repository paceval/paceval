//---------------------------------------------------------------------------
// Copyright 1997-2014. Version 1.x Joerg Koenning - All rights reserved.
// Copyright 2015-2023. Version 2.x, 3.x, 4.x 2015-2023 paceval.[Registered Trade Mark]
//                                            All rights reserved.
// Author(s) : paceval., see http://www.paceval.com
// File      : paceval_example1.cpp
//---------------------------------------------------------------------------

//---------------------------------------------------------------------------
#if defined(_MSC_VER) //we don't use the Microsoft specific functions
#define _CRT_SECURE_NO_WARNINGS
#pragma warning(disable : 4996)
#endif //#if defined(_MSC_VER)

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../../system-independent/source_public/inc/paceval_main.h" //We include the paceval header

void PrintErrorMessage(PACEVAL_HANDLE handle_pacevalComputation_in);
//---------------------------------------------------------------------------

int main(int argc, char* argv[])
{
    char functionStr[500];
    int errType;
    int answerChar;
    bool useInterval;
    char xvalStr[500];
    char yvalStr[500];
    double valuesVariablesArray[2];
    double compResult;
    double minResultInterval;
    double maxResultInterval;
    char versionString[500];

    if (paceval_InitializeLibrary(NULL) != true)
    {
        printf("\n\n paceval_InitializeLibrary() failed");
        return 0;
    }

    printf("\n|----------------------------------------------------------------------|");
    printf("\n| This demo application shows the possibilities paceval. Use the       |");
    printf("\n| simple mathematical notation and only a few lines of source code.    |");
    printf("\n| The trusted interval computation 'TINC' shows the interval in which  |");
    printf("\n| the true result is.                                                  |");
    printf("\n| Just open the file 'paceval_example1.cpp' to see its source          |");
    printf("\n| code (~200 lines).                                                   |");
    printf("\n|                                                                      |");
    printf("\n| see http://paceval.com/product-brief for the supported terms - e.g.  |");
    printf("\n| sin(x)*y+4.356                                                       |");
    printf("\n|----------------------------------------------------------------------|");

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

    //Creates the paceval-Computation object with the user's mathematical function
    PACEVAL_HANDLE handle_pacevalComputation;

    handle_pacevalComputation = paceval_CreateComputation(functionStr, 2, "x y",
                                useInterval, NULL);

    if (paceval_GetIsError(handle_pacevalComputation))
    {
        PrintErrorMessage(handle_pacevalComputation);
    }
    else
    {
        while (true)
        {
            bool err = false;
            double minValue;
            double maxValue;
            long errPosition;

            printf("\n\nEnter the x value: x=");
            scanf("%255s", xvalStr);
            printf("Enter the y value: y=");
            scanf("%255s", yvalStr);

            //Converts the strings of the variables to floating point numbers
            valuesVariablesArray[0] = paceval_dConvertStringToFloat(xvalStr, &errType, &errPosition,
                                      useInterval, &minValue, &maxValue);
            if (errType != PACEVAL_ERR_NO_ERROR)
            {
                printf("\nThe string of the variable x cannot be converted to a floating point number.");
                err = true;
            }

            valuesVariablesArray[1] = paceval_dConvertStringToFloat(yvalStr, &errType, &errPosition,
                                      useInterval, &minValue, &maxValue);
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
                    compResult = paceval_dGetComputationResult(handle_pacevalComputation,
                                 valuesVariablesArray, NULL, NULL);
                }
                else
                {
                    compResult = paceval_dGetComputationResult(handle_pacevalComputation,
                                 valuesVariablesArray, &minResultInterval, &maxResultInterval);
                }

                if (paceval_GetIsError(handle_pacevalComputation))
                {
                    PrintErrorMessage(handle_pacevalComputation);
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

    paceval_GetComputationVersionString(handle_pacevalComputation, versionString);
    printf("\n\n");
    printf(versionString);

    //Delete the paceval-Computation object
    paceval_DeleteComputation(handle_pacevalComputation);

    if ((int)paceval_fmathv(NULL, &errType, "paceval_NumberThreadUsages", 0, "", NULL) > 0)
        printf("\n\n[Threads usages: %d]", (int)paceval_fmathv(NULL, &errType, "paceval_NumberThreadUsages", 0, "", NULL));
    if ((int)paceval_fmathv(NULL, &errType, "paceval_NumberCacheHitsACC", 0, "", NULL) > 0)
        printf("\n[Cache hits ACC: %d]", (int)paceval_fmathv(NULL, &errType, "paceval_NumberCacheHitsACC", 0, "", NULL));
    printf("\n[Number of cores: %d]", (int)paceval_fmathv(NULL, &errType, "paceval_NumberOfCores", 0, "", NULL));

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
