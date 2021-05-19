//---------------------------------------------------------------------------
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

    printf("\n| This demo application shows the capabilities of paceval. in terms of |");
    printf("\n| its computational excellence. Please examine its calculation power   |");
    printf("\n| and speed for a formula without limitations in length and number of  |");
    printf("\n| variables and use standard mathematical notations.                   |");
    printf("\n| In addition, it demonstrates how precise and reliable paceval.       |");
    printf("\n| works. The trusted interval computation 'TINC' shows an interval     |");
    printf("\n| within the true results can be found.                                |");
    printf("\n|                                                                      |");
    printf("\n| see http://paceval.com/product-brief for the supported terms - e.g.  |");
    printf("\n| sin(x)*y+4.356                                                       |");

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

    //Create the paceval-Computation object with the function from the user
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

            //Convert the strings of the variables to floating points
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
                //Get the result of the function for the varaibles of the user
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

            printf("\n\nDo you want to calculate with other values for the variables [y/n]?");
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
