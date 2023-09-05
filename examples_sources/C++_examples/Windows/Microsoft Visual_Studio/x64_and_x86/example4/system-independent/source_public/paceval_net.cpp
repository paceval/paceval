//---------------------------------------------------------------------------
// Copyright 2023. Version 4.x 2023 paceval.[Registered Trade Mark]
//                             All rights reserved.
// Author(s) : paceval., see http://www.paceval.com
// File      : paceval_net.cpp
//---------------------------------------------------------------------------

//---------------------------------------------------------------------------
#if defined(_MSC_VER) //we don't use the Microsoft specific functions
#define _CRT_SECURE_NO_WARNINGS
#pragma warning(disable : 4996)
#endif //#if defined(_MSC_VER)


#include <stdarg.h>
#include "../source_public/inc/paceval_main.h"
#include "../source_public/inc/paceval_net.h"
#include <string>
#include "curl/curl.h" //see https://curl.se/download.html
#include <algorithm>
#include <iostream>
#include <fstream>
#include <ctime>
#include <chrono>
#include <iomanip>


bool WriteServerLogging(const char* propertyStr, const char* dataStr)
{
    std::ofstream fileToWrite;
    fileToWrite.open("paceval_server.log", std::ios::app);
    if (fileToWrite.is_open())
    {
        auto const now = std::chrono::system_clock::now();
        auto now_time = std::chrono::system_clock::to_time_t(now);

        fileToWrite << std::put_time(std::localtime(&now_time), "%F %T") << " " << propertyStr << dataStr << "\n";
        fileToWrite.close();

        return true;
    }
    return false;
}

extern "C" static size_t WriteCallback_Remote(void *contents, size_t size, size_t nmemb, void *userp)
{
    ((std::string*)userp)->append((char*)contents, size * nmemb);
    return size * nmemb;
}

double paceval_Remote_Demo(char* pacevalServerStr_in,
                           char* handle_pacevalComputationAsString_out,
                           const char* functionString_in,
                           unsigned long numberOfVariables_in,
                           const char* variables_in,
                           bool useInterval_in,
                           double values_in[],
                           double* result_out,
                           double* trustedMinResult_out,
                           double* trustedMaxResult_out,
                           int* errorType_out,
                           char* errorTypeString_out,
                           char* errorMessageString_out,
                           double* timeComputeRemote_out)
{
    CURL *curl;

    curl = curl_easy_init();
    if (curl)
    {
        CURLcode res;
        std::string postString;
        std::string readBuffer;
        std::string urlString;
        std::string tempString;
        char *postEncoded;
        long httpCode(0);
        size_t searchPos;
        size_t startPos;
        size_t endPos;
        int errType;
        char strcValue[500];
        long errPosition;

        urlString = pacevalServerStr_in;
        urlString.append("/Demo/");
        postString = "functionString=";
        postEncoded = curl_easy_escape(curl, functionString_in, 0);
        postString.append(postEncoded);
        curl_free(postEncoded);
        postString.append("&numberOfVariables=");
        postString.append(std::to_string(numberOfVariables_in));
        postString.append("&variables=");
        tempString = variables_in;
        std::replace(tempString.begin(), tempString.end(), ' ', ';');
        postEncoded = curl_easy_escape(curl, tempString.c_str(), 0);
        postString.append(postEncoded);
        curl_free(postEncoded);
        postString.append("&values=");
        for (unsigned long iCount = 0; iCount < numberOfVariables_in; iCount++)
        {
            char strcValue[25];

            paceval_dConvertFloatToString(strcValue, values_in[iCount]);
            postEncoded = curl_easy_escape(curl, strcValue, 0);
            postString.append(postEncoded);
            curl_free(postEncoded);
            if (iCount != numberOfVariables_in - 1)
            {
                postEncoded = curl_easy_escape(curl, ";", (int)strlen(";"));
                postString.append(postEncoded);
                curl_free(postEncoded);
            }
        }
        postString.append("&interval=");
        if (useInterval_in == true)
            postString.append("yes");
        else
            postString.append("no");

        curl_easy_setopt(curl, CURLOPT_URL, urlString.c_str());
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postString.c_str());
        curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback_Remote);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);
        curl_easy_setopt(curl, CURLOPT_ACCEPT_ENCODING, "br, gzip, deflate");
        curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE_LARGE, (long)postString.length());
        res = curl_easy_perform(curl);
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &httpCode);
        curl_easy_cleanup(curl);

        WriteServerLogging("POST_URL: ", urlString.c_str());
        WriteServerLogging("POST_FIELDS: ", postString.c_str());
        tempString = std::to_string(httpCode);
        WriteServerLogging("RESPONSE_CODE: ", tempString.c_str());
        WriteServerLogging("RESPONSE_DATA: ", readBuffer.c_str());

        if (httpCode == 200)
        {
            if ((readBuffer == "")
                    || (readBuffer == "{ \"error\": \"internal error, please contact service admin\" }"))
            {
                *errorType_out = PACEVAL_ERR_FATAL_CONNECTING_SERVER;
                if (errorTypeString_out != NULL)
                    strcpy(errorTypeString_out, "[PACEVAL_ERR_FATAL_CONNECTING_SERVER]");
                if (errorMessageString_out != NULL)
                    strcpy(errorMessageString_out, "The paceval-server could not be connected (PACEVAL_ERR_FATAL_CONNECTING_SERVER).");
                WriteServerLogging("return false", "\n");
                return false;
            }

            if (readBuffer == "{ \"error\": \"missing parameters\" }")
            {
                *errorType_out = PACEVAL_ERR_FATAL_PARAMETERS_SERVER;
                if (errorTypeString_out != NULL)
                    strcpy(errorTypeString_out, "[PACEVAL_ERR_FATAL_PARAMETERS_SERVER]");
                if (errorMessageString_out != NULL)
                    strcpy(errorMessageString_out, "The paceval-server could not process the parameters (PACEVAL_ERR_FATAL_PARAMETERS_SERVER).");
                WriteServerLogging("return false", "\n");
                return false;
            }

            searchPos = readBuffer.find("[NO ERROR]");
            if ((searchPos > 0) && (searchPos < readBuffer.length()))
            {
                *errorType_out = PACEVAL_ERR_NO_ERROR;

                startPos = readBuffer.find("\"handle_pacevalComputation\":\"");
                if (startPos < readBuffer.size())
                {
                    startPos = startPos + strlen("\"handle_pacevalComputation\":\"");
                    endPos = readBuffer.find("\",", startPos);
                    strncpy(handle_pacevalComputationAsString_out, &readBuffer.c_str()[startPos], endPos - startPos);
                    handle_pacevalComputationAsString_out[endPos - startPos] = '\0';
                }

                startPos = readBuffer.find("\"result\":\"");
                if (startPos < readBuffer.size())
                {
                    startPos = startPos + strlen("\"result\":\"");
                    endPos = readBuffer.find("\",", startPos);
                    strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                    strcValue[endPos - startPos] = '\0';
                    *result_out = paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                  false, NULL, NULL);
                }

                if (trustedMinResult_out != NULL)
                {
                    startPos = readBuffer.find("\"interval-min-result\":\"");
                    if (startPos < readBuffer.size())
                    {
                        startPos = startPos + strlen("\"interval-min-result\":\"");
                        endPos = readBuffer.find("\",", startPos);
                        strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                        strcValue[endPos - startPos] = '\0';
                        *trustedMinResult_out = paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                                false, NULL, NULL);
                    }
                }

                if (trustedMaxResult_out != NULL)
                {
                    startPos = readBuffer.find("\"interval-max-result\":\"");
                    if (startPos < readBuffer.size())
                    {
                        startPos = startPos + strlen("\"interval-max-result\":\"");
                        endPos = readBuffer.find("\",", startPos);
                        strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                        strcValue[endPos - startPos] = '\0';
                        *trustedMaxResult_out = paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                                false, NULL, NULL);
                    }
                }

                if (timeComputeRemote_out != NULL)
                {
                    startPos = readBuffer.find("\"time-calculate\":\"");
                    if (startPos < readBuffer.size())
                    {
                        startPos = startPos + strlen("\"time-calculate\":\"");
                        endPos = readBuffer.find("s\",", startPos);
                        strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                        strcValue[endPos - startPos] = '\0';
                        *timeComputeRemote_out = paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                                 false, NULL, NULL);
                    }
                }

                if (errorTypeString_out != NULL)
                {
                    startPos = readBuffer.find("\"error-type\":\"");
                    if (startPos < readBuffer.size())
                    {
                        startPos = startPos + strlen("\"error-type\":\"");
                        endPos = readBuffer.find("\",", startPos);
                        strncpy(errorTypeString_out, &readBuffer.c_str()[startPos], endPos - startPos);
                        errorTypeString_out[endPos - startPos] = '\0';
                    }
                }

                if (errorMessageString_out != NULL)
                {
                    startPos = readBuffer.find("\"error-message\":\"");
                    if (startPos < readBuffer.size())
                    {
                        startPos = startPos + strlen("\"error-message\":\"");
                        endPos = readBuffer.find("\",", startPos);
                        strncpy(errorMessageString_out, &readBuffer.c_str()[startPos], endPos - startPos);
                        errorMessageString_out[endPos - startPos] = '\0';
                    }
                }

                WriteServerLogging("return true", "\n");
                return true;
            }
            else
            {
                if (errorTypeString_out != NULL)
                {
                    startPos = readBuffer.find("\"error-type\":\"");
                    if (startPos < readBuffer.size())
                    {
                        startPos = startPos + strlen("\"error-type\":\"");
                        endPos = readBuffer.find("\",", startPos);
                        strncpy(errorTypeString_out, &readBuffer.c_str()[startPos], endPos - startPos);
                        errorTypeString_out[endPos - startPos] = '\0';
                    }
                }

                startPos = readBuffer.find("\"error-type\":\"[Error #");
                if (startPos < readBuffer.size())
                {
                    startPos = startPos + strlen("\"error-type\":\"[Error #");
                    endPos = readBuffer.find(",", startPos);
                    strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                    strcValue[endPos - startPos] = '\0';
                    *errorType_out = (int)paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                     false, NULL, NULL);
                }

                if (errorMessageString_out != NULL)
                {
                    startPos = readBuffer.find("\"error-message\":\"");
                    if (startPos < readBuffer.size())
                    {
                        startPos = startPos + strlen("\"error-message\":\"");
                        endPos = readBuffer.find("\",", startPos);
                        strncpy(errorMessageString_out, &readBuffer.c_str()[startPos], endPos - startPos);
                        errorMessageString_out[endPos - startPos] = '\0';
                    }
                }

                WriteServerLogging("return false", "\n");
                return false;
            }
        }
    }


    *errorType_out = PACEVAL_ERR_FATAL_CONNECTING_SERVER;
    strcpy(errorTypeString_out, "[PACEVAL_ERR_FATAL_CONNECTING_SERVER]");
    strcpy(errorMessageString_out, "The paceval-server could not be connected (PACEVAL_ERR_FATAL_CONNECTING_SERVER).");
    WriteServerLogging("return false", "\n");
    return false;
}

bool paceval_Remote_WaitForCreateComputation(std::string* readBuffer,
        char* pacevalServerStr_in,
        char* handle_pacevalComputationAsString_out,
        int* errorType_out,
        char* errorTypeString_out,
        char* errorMessageString_out)
{
    size_t startPos;
    size_t endPos;

    //We repeat the process of requesting /GetErrorInformation until we no longer get the BUSY status
    bool pacevalComputation_available = false;

    startPos = readBuffer->find("\"handle_pacevalComputation\":\"");
    startPos = startPos + strlen("\"handle_pacevalComputation\":\"");
    endPos = readBuffer->find("\",", startPos);
    strncpy(handle_pacevalComputationAsString_out, &readBuffer->c_str()[startPos], endPos - startPos);
    handle_pacevalComputationAsString_out[endPos - startPos] = '\0';

    for (int iCount = 0; iCount < 480; iCount++) //We try for about 10 minutes, see Sleep(1250);
    {
        Sleep(1250);
        paceval_Remote_GetErrorInformation(pacevalServerStr_in,
                                           handle_pacevalComputationAsString_out,
                                           NULL,
                                           errorType_out,
                                           NULL,
                                           errorTypeString_out,
                                           errorMessageString_out);

        if ((*errorType_out != PACEVAL_ERR_CREATION_NO_ERROR_BUT_BUSY)
                && (*errorType_out != PACEVAL_ERR_FATAL_CONNECTING_SERVER)
                && (*errorType_out != PACEVAL_ERR_FATAL_PARAMETERS_SERVER))
        {
            pacevalComputation_available = true;
            return true;
        }
    }

    *errorType_out = PACEVAL_ERR_FATAL_CONNECTING_SERVER;
    strcpy(errorTypeString_out, "[PACEVAL_ERR_FATAL_CONNECTING_SERVER]");
    strcpy(errorMessageString_out, "The paceval-server could not be connected (PACEVAL_ERR_FATAL_CONNECTING_SERVER).");
    return false;
}

extern "C" bool paceval_Remote_CreateComputation(char* pacevalServerStr_in,
        char* handle_pacevalComputationAsString_out,
        const char* functionString_in,
        unsigned long numberOfVariables_in,
        const char* variables_in,
        bool useInterval_in,
        int* errorType_out,
        char* errorTypeString_out,
        char* errorMessageString_out)
{
    CURL *curl;

    curl = curl_easy_init();
    if (curl)
    {
        CURLcode res;
        std::string postString;
        std::string readBuffer;
        std::string urlString;
        std::string tempString;
        char *postEncoded;
        long httpCode(0);
        size_t searchPos;
        size_t startPos;
        size_t endPos;
        int errType;
        char strcValue[500];
        long errPosition;

        urlString = pacevalServerStr_in;
        urlString.append("/CreateComputation/");
        postString = "functionString=";
        postEncoded = curl_easy_escape(curl, functionString_in, 0);
        postString.append(postEncoded);
        curl_free(postEncoded);
        postString.append("&numberOfVariables=");
        postString.append(std::to_string(numberOfVariables_in));
        postString.append("&variables=");
        tempString = variables_in;
        std::replace(tempString.begin(), tempString.end(), ' ', ';');
        postEncoded = curl_easy_escape(curl, tempString.c_str(), 0);
        postString.append(postEncoded);
        curl_free(postEncoded);
        postString.append("&interval=");
        if (useInterval_in == true)
            postString.append("yes");
        else
            postString.append("no");

        curl_easy_setopt(curl, CURLOPT_URL, urlString.c_str());
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postString.c_str());
        curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback_Remote);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);
        curl_easy_setopt(curl, CURLOPT_ACCEPT_ENCODING, "br, gzip, deflate");
        curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE_LARGE, (long)postString.length());
        res = curl_easy_perform(curl);
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &httpCode);
        curl_easy_cleanup(curl);

        WriteServerLogging("POST_URL: ", urlString.c_str());
        WriteServerLogging("POST_FIELDS: ", postString.c_str());
        tempString = std::to_string(httpCode);
        WriteServerLogging("RESPONSE_CODE: ", tempString.c_str());
        WriteServerLogging("RESPONSE_DATA: ", readBuffer.c_str());

        if (httpCode == 200)
        {
            if ((readBuffer == "")
                    || (readBuffer == "{ \"error\": \"internal error, please contact service admin\" }"))
            {
                *errorType_out = PACEVAL_ERR_FATAL_CONNECTING_SERVER;
                strcpy(errorTypeString_out, "[PACEVAL_ERR_FATAL_CONNECTING_SERVER]");
                strcpy(errorMessageString_out, "The paceval-server could not be connected (PACEVAL_ERR_FATAL_CONNECTING_SERVER).");
                WriteServerLogging("return false", "\n");
                return false;
            }

            if (readBuffer == "{ \"error\": \"missing parameters\" }")
            {
                *errorType_out = PACEVAL_ERR_FATAL_PARAMETERS_SERVER;
                strcpy(errorTypeString_out, "[PACEVAL_ERR_FATAL_PARAMETERS_SERVER]");
                strcpy(errorMessageString_out, "The paceval-server could not process the parameters (PACEVAL_ERR_FATAL_PARAMETERS_SERVER).");
                WriteServerLogging("return false", "\n");
                return false;
            }

            searchPos = readBuffer.find("[PACEVAL_ERR_CREATION_NO_ERROR_BUT_BUSY]");
            if ((searchPos > 0) && (searchPos < readBuffer.length()))
            {
                bool success;

                WriteServerLogging("start wait for create computation done", "\n");
                success = paceval_Remote_WaitForCreateComputation(&readBuffer,
                          pacevalServerStr_in,
                          handle_pacevalComputationAsString_out,
                          errorType_out,
                          errorTypeString_out,
                          errorMessageString_out);
                WriteServerLogging("end wait for create computation done", "\n");
                if (success == true)
                    WriteServerLogging("return true", "\n");
                else
                    WriteServerLogging("return false", "\n");
                return success;
            }

            searchPos = readBuffer.find("[NO ERROR]");
            if ((searchPos > 0) && (searchPos < readBuffer.length()))
            {
                *errorType_out = PACEVAL_ERR_NO_ERROR;

                startPos = readBuffer.find("\"handle_pacevalComputation\":\"");
                if (startPos < readBuffer.size())
                {
                    startPos = startPos + strlen("\"handle_pacevalComputation\":\"");
                    endPos = readBuffer.find("\",", startPos);
                    strncpy(handle_pacevalComputationAsString_out, &readBuffer.c_str()[startPos], endPos - startPos);
                    handle_pacevalComputationAsString_out[endPos - startPos] = '\0';
                }

                if (errorTypeString_out != NULL)
                {
                    startPos = readBuffer.find("\"error-type\":\"");
                    if (startPos < readBuffer.size())
                    {
                        startPos = startPos + strlen("\"error-type\":\"");
                        endPos = readBuffer.find("\",", startPos);
                        strncpy(errorTypeString_out, &readBuffer.c_str()[startPos], endPos - startPos);
                        errorTypeString_out[endPos - startPos] = '\0';
                    }
                }

                if (errorMessageString_out != NULL)
                {
                    startPos = readBuffer.find("\"error-message\":\"");
                    if (startPos < readBuffer.size())
                    {
                        startPos = startPos + strlen("\"error-message\":\"");
                        endPos = readBuffer.find("\",", startPos);
                        strncpy(errorMessageString_out, &readBuffer.c_str()[startPos], endPos - startPos);
                        errorMessageString_out[endPos - startPos] = '\0';
                    }
                }

                WriteServerLogging("return true", "\n");
                return true;
            }
            else
            {
                if (errorTypeString_out != NULL)
                {
                    startPos = readBuffer.find("\"error-type\":\"");
                    if (startPos < readBuffer.size())
                    {
                        startPos = startPos + strlen("\"error-type\":\"");
                        endPos = readBuffer.find("\",", startPos);
                        strncpy(errorTypeString_out, &readBuffer.c_str()[startPos], endPos - startPos);
                        errorTypeString_out[endPos - startPos] = '\0';
                    }
                }

                startPos = readBuffer.find("\"error-type\":\"[Error #");
                if (startPos < readBuffer.size())
                {
                    startPos = startPos + strlen("\"error-type\":\"[Error #");
                    endPos = readBuffer.find(",", startPos);
                    strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                    strcValue[endPos - startPos] = '\0';
                    *errorType_out = (int)paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                     false, NULL, NULL);
                }

                if (errorMessageString_out != NULL)
                {
                    startPos = readBuffer.find("\"error-message\":\"");
                    if (startPos < readBuffer.size())
                    {
                        startPos = startPos + strlen("\"error-message\":\"");
                        endPos = readBuffer.find("\",", startPos);
                        strncpy(errorMessageString_out, &readBuffer.c_str()[startPos], endPos - startPos);
                        errorMessageString_out[endPos - startPos] = '\0';
                    }
                }

                WriteServerLogging("return false", "\n");
                return false;
            }
        }
    }

    *errorType_out = PACEVAL_ERR_FATAL_CONNECTING_SERVER;
    strcpy(errorTypeString_out, "[PACEVAL_ERR_FATAL_CONNECTING_SERVER]");
    strcpy(errorMessageString_out, "The paceval-server could not be connected (PACEVAL_ERR_FATAL_CONNECTING_SERVER).");
    WriteServerLogging("return false", "\n");
    return false;
}

extern "C" double paceval_dRemote_mathv(char* pacevalServerStr_in,
                                        char* handle_pacevalComputationAsString_out,
                                        const char* functionString_in,
                                        unsigned long numberOfVariables_in,
                                        const char* variables_in,
                                        double values_in[],
                                        int* errorType_out,
                                        char* errorTypeString_out,
                                        char* errorMessageString_out,
                                        double* timeComputeRemote_out)
{
    bool success;
    double result_out;
    char handle_pacevalComputationAsString[500];

    if (handle_pacevalComputationAsString_out == NULL)
    {
        paceval_Remote_Demo(pacevalServerStr_in, handle_pacevalComputationAsString, functionString_in,
                            numberOfVariables_in, variables_in, false, values_in, &result_out, NULL, NULL,
                            errorType_out, errorTypeString_out, errorMessageString_out, timeComputeRemote_out);
        return result_out;
    }

    success = paceval_Remote_CreateComputation(pacevalServerStr_in, handle_pacevalComputationAsString, functionString_in,
              numberOfVariables_in, variables_in, false, errorType_out, errorTypeString_out, errorMessageString_out);

    if (success == true)
    {
        success = paceval_dRemote_GetComputationResult(pacevalServerStr_in, handle_pacevalComputationAsString, numberOfVariables_in,
                  values_in, &result_out, NULL, NULL, errorType_out, errorTypeString_out, errorMessageString_out, timeComputeRemote_out);

    }

    if (handle_pacevalComputationAsString_out != NULL)
        strcpy(handle_pacevalComputationAsString_out, handle_pacevalComputationAsString);

    return result_out;
}

extern "C" double paceval_dRemote_mathvi(char* pacevalServerStr_in,
        char* handle_pacevalComputationAsString_out,
        const char* functionString_in,
        unsigned long numberOfVariables_in,
        const char* variables_in,
        double values_in[],
        int* errorType_out,
        double* trustedMinResult_out,
        double* trustedMaxResult_out,
        char* errorTypeString_out,
        char* errorMessageString_out,
        double* timeComputeRemote_out)
{
    bool success;
    double result_out;
    char handle_pacevalComputationAsString[500];

    if (handle_pacevalComputationAsString_out == NULL)
    {
        paceval_Remote_Demo(pacevalServerStr_in, handle_pacevalComputationAsString, functionString_in,
                            numberOfVariables_in, variables_in, true, values_in, &result_out, trustedMinResult_out, trustedMaxResult_out,
                            errorType_out, errorTypeString_out, errorMessageString_out, timeComputeRemote_out);
        return result_out;
    }

    success = paceval_Remote_CreateComputation(pacevalServerStr_in, handle_pacevalComputationAsString, functionString_in,
              numberOfVariables_in, variables_in, true, errorType_out, errorTypeString_out, errorMessageString_out);

    if (success == true)
    {
        success = paceval_dRemote_GetComputationResult(pacevalServerStr_in, handle_pacevalComputationAsString, numberOfVariables_in,
                  values_in, &result_out, trustedMinResult_out, trustedMaxResult_out, errorType_out, errorTypeString_out, errorMessageString_out, timeComputeRemote_out);

    }

    if (handle_pacevalComputationAsString_out != NULL)
        strcpy(handle_pacevalComputationAsString_out, handle_pacevalComputationAsString);

    return result_out;
}

extern "C" bool paceval_dRemote_GetComputationResult(char* pacevalServerStr_in,
        const char* handle_pacevalComputationAsString_in,
        unsigned long numberOfVariables_in,
        double values_in[],
        double* result_out,
        double* trustedMinResult_out,
        double* trustedMaxResult_out,
        int* errorType_out,
        char* errorTypeString_out,
        char* errorMessageString_out,
        double* timeComputeRemote_out)
{
    CURL *curl;

    curl = curl_easy_init();
    if (curl)
    {
        CURLcode res;
        std::string postString;
        std::string readBuffer;
        std::string urlString;
        std::string tempString;
        char *postEncoded;
        long httpCode(0);
        size_t searchPos;
        size_t startPos;
        size_t endPos;
        int errType;
        char strcValue[500];
        long errPosition;

        urlString = pacevalServerStr_in;
        urlString.append("/GetComputationResult/");
        postString = "handle_pacevalComputation=";
        postEncoded = curl_easy_escape(curl, handle_pacevalComputationAsString_in, 0);
        postString.append(postEncoded);
        curl_free(postEncoded);
        postString.append("&values=");
        for (unsigned long iCount = 0; iCount < numberOfVariables_in; iCount++)
        {
            char strcValue[25];

            paceval_dConvertFloatToString(strcValue, values_in[iCount]);
            postEncoded = curl_easy_escape(curl, strcValue, 0);
            postString.append(postEncoded);
            curl_free(postEncoded);
            if (iCount != numberOfVariables_in - 1)
            {
                postEncoded = curl_easy_escape(curl, ";", (int)strlen(";"));
                postString.append(postEncoded);
                curl_free(postEncoded);
            }
        }

        curl_easy_setopt(curl, CURLOPT_URL, urlString.c_str());
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postString.c_str());
        curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback_Remote);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);
        curl_easy_setopt(curl, CURLOPT_ACCEPT_ENCODING, "br, gzip, deflate");
        curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE_LARGE, (long)postString.length());
        res = curl_easy_perform(curl);
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &httpCode);
        curl_easy_cleanup(curl);

        WriteServerLogging("POST_URL: ", urlString.c_str());
        WriteServerLogging("POST_FIELDS: ", postString.c_str());
        tempString = std::to_string(httpCode);
        WriteServerLogging("RESPONSE_CODE: ", tempString.c_str());
        WriteServerLogging("RESPONSE_DATA: ", readBuffer.c_str());

        if (httpCode == 200)
        {
            if ((readBuffer == "")
                    || (readBuffer == "{ \"error\": \"internal error, please contact service admin\" }"))
            {
                *errorType_out = PACEVAL_ERR_FATAL_CONNECTING_SERVER;
                strcpy(errorTypeString_out, "[PACEVAL_ERR_FATAL_CONNECTING_SERVER]");
                strcpy(errorMessageString_out, "The paceval-server could not be connected (PACEVAL_ERR_FATAL_CONNECTING_SERVER).");
                WriteServerLogging("return false", "\n");
                return false;
            }

            if (readBuffer == "{ \"error\": \"missing parameters\" }")
            {
                *errorType_out = PACEVAL_ERR_FATAL_PARAMETERS_SERVER;
                strcpy(errorTypeString_out, "[PACEVAL_ERR_FATAL_PARAMETERS_SERVER]");
                strcpy(errorMessageString_out, "The paceval-server could not process the parameters (PACEVAL_ERR_FATAL_PARAMETERS_SERVER).");
                WriteServerLogging("return false", "\n");
                return false;
            }

            searchPos = readBuffer.find("[NO ERROR]");
            if ((searchPos > 0) && (searchPos < readBuffer.length()))
            {
                *errorType_out = PACEVAL_ERR_NO_ERROR;

                startPos = readBuffer.find("\"result\":\"");
                if (startPos < readBuffer.size())
                {
                    startPos = startPos + strlen("\"result\":\"");
                    endPos = readBuffer.find("\",", startPos);
                    strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                    strcValue[endPos - startPos] = '\0';
                    *result_out = paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                  false, NULL, NULL);
                }

                if (trustedMinResult_out != NULL)
                {
                    startPos = readBuffer.find("\"interval-min-result\":\"");
                    if (startPos < readBuffer.size())
                    {
                        startPos = startPos + strlen("\"interval-min-result\":\"");
                        endPos = readBuffer.find("\",", startPos);
                        strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                        strcValue[endPos - startPos] = '\0';
                        *trustedMinResult_out = paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                                false, NULL, NULL);
                    }
                }

                if (trustedMaxResult_out != NULL)
                {
                    startPos = readBuffer.find("\"interval-max-result\":\"");
                    if (startPos < readBuffer.size())
                    {
                        startPos = startPos + strlen("\"interval-max-result\":\"");
                        endPos = readBuffer.find("\",", startPos);
                        strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                        strcValue[endPos - startPos] = '\0';
                        *trustedMaxResult_out = paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                                false, NULL, NULL);
                    }
                }

                if (timeComputeRemote_out != NULL)
                {
                    startPos = readBuffer.find("\"time-calculate\":\"");
                    if (startPos < readBuffer.size())
                    {
                        startPos = startPos + strlen("\"time-calculate\":\"");
                        endPos = readBuffer.find("s\",", startPos);
                        strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                        strcValue[endPos - startPos] = '\0';
                        *timeComputeRemote_out = paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                                 false, NULL, NULL);
                    }
                }

                if (errorTypeString_out != NULL)
                {
                    startPos = readBuffer.find("\"error-type\":\"");
                    if (startPos < readBuffer.size())
                    {
                        startPos = startPos + strlen("\"error-type\":\"");
                        endPos = readBuffer.find("\",", startPos);
                        strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                        strcValue[endPos - startPos] = '\0';

                        strcpy(errorTypeString_out, "\"");
                        strcat(errorTypeString_out, strcValue);
                        strcat(errorTypeString_out, "\"");
                    }
                }

                if (errorMessageString_out != NULL)
                {
                    startPos = readBuffer.find("\"error-message\":\"");
                    if (startPos < readBuffer.size())
                    {
                        startPos = startPos + strlen("\"error-message\":\"");
                        endPos = readBuffer.find("\",", startPos);
                        strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                        strcValue[endPos - startPos] = '\0';

                        strcpy(errorMessageString_out, "\"");
                        strcat(errorMessageString_out, strcValue);
                        strcat(errorMessageString_out, "\"");
                    }
                }

                WriteServerLogging("return true", "\n");
                return true;
            }
            else
            {
                if (errorTypeString_out != NULL)
                {
                    startPos = readBuffer.find("\"error-type\":\"");
                    if (startPos < readBuffer.size())
                    {
                        startPos = startPos + strlen("\"error-type\":\"");
                        endPos = readBuffer.find("\",", startPos);
                        strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                        strcValue[endPos - startPos] = '\0';

                        strcpy(errorTypeString_out, "\"");
                        strcat(errorTypeString_out, strcValue);
                        strcat(errorTypeString_out, "\"");
                    }
                }

                startPos = readBuffer.find("\"error-type\":\"[Error #");
                if (startPos < readBuffer.size())
                {
                    startPos = startPos + strlen("\"error-type\":\"[Error #");
                    endPos = readBuffer.find(",", startPos);
                    strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                    strcValue[endPos - startPos] = '\0';
                    *errorType_out = (int)paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                     false, NULL, NULL);
                }

                if (errorMessageString_out != NULL)
                {
                    startPos = readBuffer.find("\"error-message\":\"");
                    if (startPos < readBuffer.size())
                    {
                        startPos = startPos + strlen("\"error-message\":\"");
                        endPos = readBuffer.find("\",", startPos);
                        strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                        strcValue[endPos - startPos] = '\0';

                        strcpy(errorMessageString_out, "\"");
                        strcat(errorMessageString_out, strcValue);
                        strcat(errorMessageString_out, "\"");
                    }
                }

                WriteServerLogging("return false", "\n");
                return false;
            }
        }
    }

    *errorType_out = PACEVAL_ERR_FATAL_CONNECTING_SERVER;
    strcpy(errorTypeString_out, "[PACEVAL_ERR_FATAL_CONNECTING_SERVER]");
    strcpy(errorMessageString_out, "The paceval-server could not be connected (PACEVAL_ERR_FATAL_CONNECTING_SERVER).");
    WriteServerLogging("return false", "\n");
    return false;
}

extern "C" bool paceval_dRemote_GetComputationResultExt(char* pacevalServerStr_in,
        const char* handle_pacevalComputationAsString_in,
        unsigned long numberOfVariables_in,
        double values_in[],
        unsigned long numberOfCalculations_in,
        double* results_out,
        double* trustedMinResults_out,
        double* trustedMaxResults_out,
        bool* hasError_out,
        int* errorTypes_out,
        double* timeComputeRemote_out)
{
    CURL *curl;

    curl = curl_easy_init();
    if (curl)
    {
        CURLcode res;
        std::string postString;
        std::string readBuffer;
        std::string urlString;
        std::string tempString;
        char *postEncoded;
        long httpCode(0);
        size_t startPos;
        size_t endPos;
        int errType;
        char strcValue[500];
        long errPosition;

        urlString = pacevalServerStr_in;
        urlString.append("/GetComputationResultExt/");
        postString = "handle_pacevalComputation=";
        postEncoded = curl_easy_escape(curl, handle_pacevalComputationAsString_in, 0);
        postString.append(postEncoded);
        curl_free(postEncoded);
        postString.append("&numberOfCalculations=");
        postString.append(std::to_string(numberOfCalculations_in));
        postString.append("&values=");
        for (unsigned long iCount = 0; iCount < numberOfVariables_in * numberOfCalculations_in; iCount++)
        {
            char strcValue[25];

            paceval_dConvertFloatToString(strcValue, values_in[iCount]);
            postEncoded = curl_easy_escape(curl, strcValue, 0);
            postString.append(postEncoded);
            curl_free(postEncoded);
            if (iCount != numberOfVariables_in * numberOfCalculations_in - 1)
            {
                postEncoded = curl_easy_escape(curl, ";", (int)strlen(";"));
                postString.append(postEncoded);
                curl_free(postEncoded);
            }
        }

        curl_easy_setopt(curl, CURLOPT_URL, urlString.c_str());
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postString.c_str());
        curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback_Remote);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);
        curl_easy_setopt(curl, CURLOPT_ACCEPT_ENCODING, "br, gzip, deflate");
        curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE_LARGE, (long)postString.length());
        res = curl_easy_perform(curl);
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &httpCode);
        curl_easy_cleanup(curl);

        WriteServerLogging("POST_URL: ", urlString.c_str());
        WriteServerLogging("POST_FIELDS: ", postString.c_str());
        tempString = std::to_string(httpCode);
        WriteServerLogging("RESPONSE_CODE: ", tempString.c_str());
        WriteServerLogging("RESPONSE_DATA: ", readBuffer.c_str());

        if (httpCode == 200)
        {
            if ((readBuffer == "")
                    || (readBuffer == "{ \"error\": \"internal error, please contact service admin\" }"))
            {
                *hasError_out = true;
                for (unsigned int iCount = 0; iCount < numberOfCalculations_in; iCount++)
                {
                    errorTypes_out[iCount] = PACEVAL_ERR_FATAL_CONNECTING_SERVER;
                }
                WriteServerLogging("return false", "\n");
                return false;
            }

            if (readBuffer == "{ \"error\": \"missing parameters\" }")
            {
                *hasError_out = true;
                for (unsigned int iCount = 0; iCount < numberOfCalculations_in; iCount++)
                {
                    errorTypes_out[iCount] = PACEVAL_ERR_FATAL_PARAMETERS_SERVER;
                }
                WriteServerLogging("return false", "\n");
                return false;
            }

            if (hasError_out != NULL)
            {
                startPos = readBuffer.find("\"hasError\":");
                if (startPos < readBuffer.size())
                {
                    startPos = startPos + strlen("\"hasError\":");
                    endPos = readBuffer.find(",", startPos);
                    strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                    strcValue[endPos - startPos] = '\0';
                    if (strcmp(strcValue, "true") == 0)
                    {
                        *hasError_out = true;
                    }
                    else
                    {
                        *hasError_out = false;
                    }
                }
            }

            startPos = readBuffer.find("\"error-type-numbers\":[");
            if (startPos < readBuffer.size())
            {
                startPos = startPos + strlen("\"error-type-numbers\":[");
                for (unsigned int iCount = 0; iCount < numberOfCalculations_in; iCount++)
                {
                    if (iCount != numberOfCalculations_in - 1)
                        endPos = readBuffer.find(",", startPos);
                    else if (iCount == numberOfCalculations_in - 1)
                        endPos = readBuffer.find("]", startPos);

                    strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                    strcValue[endPos - startPos] = '\0';
                    errorTypes_out[iCount] = paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                             false, NULL, NULL);

                    if (iCount != numberOfCalculations_in - 1)
                    {
                        startPos = endPos + 1;
                    }
                }
            }

            startPos = readBuffer.find("\"results\":[\"");
            if (startPos < readBuffer.size())
            {
                startPos = startPos + strlen("\"results\":[\"");
                for (unsigned int iCount = 0; iCount < numberOfCalculations_in; iCount++)
                {
                    endPos = readBuffer.find("\"", startPos);
                    strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                    strcValue[endPos - startPos] = '\0';
                    if (errorTypes_out[iCount] != PACEVAL_ERR_NO_ERROR)
                    {
                        results_out[iCount] = NAN;
                    }
                    else
                    {
                        results_out[iCount] = paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                              false, NULL, NULL);
                    }

                    if (iCount != numberOfCalculations_in - 1)
                    {
                        startPos = readBuffer.find(",\"", endPos + 1);
                        startPos = startPos + strlen(",\"");
                    }
                }
            }

            if (trustedMinResults_out != NULL)
            {
                startPos = readBuffer.find("\"interval-min-results\":[\"");
                if (startPos < readBuffer.size())
                {
                    startPos = startPos + strlen("\"interval-min-results\":[\"");
                    for (unsigned int iCount = 0; iCount < numberOfCalculations_in; iCount++)
                    {
                        endPos = readBuffer.find("\"", startPos);
                        strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                        strcValue[endPos - startPos] = '\0';
                        if (errorTypes_out[iCount] != PACEVAL_ERR_NO_ERROR)
                        {
                            trustedMinResults_out[iCount] = NAN;
                        }
                        else
                        {
                            trustedMinResults_out[iCount] = paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                                            false, NULL, NULL);
                        }

                        if (iCount != numberOfCalculations_in - 1)
                        {
                            startPos = readBuffer.find(",\"", endPos + 1);
                            startPos = startPos + strlen(",\"");
                        }
                    }
                }
            }

            if (trustedMaxResults_out != NULL)
            {
                startPos = readBuffer.find("\"interval-max-results\":[\"");
                if (startPos < readBuffer.size())
                {
                    startPos = startPos + strlen("\"interval-max-results\":[\"");
                    for (unsigned int iCount = 0; iCount < numberOfCalculations_in; iCount++)
                    {
                        endPos = readBuffer.find("\"", startPos);
                        strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                        strcValue[endPos - startPos] = '\0';
                        if (errorTypes_out[iCount] != PACEVAL_ERR_NO_ERROR)
                        {
                            trustedMaxResults_out[iCount] = NAN;
                        }
                        else
                        {
                            trustedMaxResults_out[iCount] = paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                                            false, NULL, NULL);
                        }

                        if (iCount != numberOfCalculations_in - 1)
                        {
                            startPos = readBuffer.find(",\"", endPos + 1);
                            startPos = startPos + strlen(",\"");
                        }
                    }
                }
            }

            if (timeComputeRemote_out != NULL)
            {
                startPos = readBuffer.find("\"time-calculate\":\"");
                if (startPos < readBuffer.size())
                {
                    startPos = startPos + strlen("\"time-calculate\":\"");
                    endPos = readBuffer.find("s\",", startPos);
                    strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                    strcValue[endPos - startPos] = '\0';
                    *timeComputeRemote_out = paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                             false, NULL, NULL);
                }
            }

            WriteServerLogging("return true", "\n");
            return true;
        }
    }

    *hasError_out = true;
    for (unsigned int iCount = 0; iCount < numberOfCalculations_in; iCount++)
    {
        errorTypes_out[iCount] = PACEVAL_ERR_FATAL_CONNECTING_SERVER;
    }
    WriteServerLogging("return false", "\n");
    return false;
}

extern "C" bool paceval_dRemote_GetMultipleComputationsResults(char* pacevalServerStr_in,
        const char* handle_pacevalComputationAsStrings_in,
        unsigned long numberOfpacevalComputations_in,
        unsigned long numberOfVariables_in,
        double values_in[],
        double* results_out,
        double* trustedMinResults_out,
        double* trustedMaxResults_out,
        bool* hasError_out,
        int* errorTypes_out,
        double* timeComputeRemote_out)
{
    CURL *curl;

    curl = curl_easy_init();
    if (curl)
    {
        CURLcode res;
        std::string postString;
        std::string readBuffer;
        std::string urlString;
        std::string tempString;
        char *postEncoded;
        long httpCode(0);
        size_t startPos;
        size_t endPos;
        int errType;
        char strcValue[500];
        long errPosition;

        urlString = pacevalServerStr_in;
        urlString.append("/GetMultipleComputationsResults/");
        postString = "handle_pacevalComputations=";
        postEncoded = curl_easy_escape(curl, handle_pacevalComputationAsStrings_in, 0);
        postString.append(postEncoded);
        curl_free(postEncoded);
        postString.append("&numberOfpacevalComputations=");
        postString.append(std::to_string(numberOfpacevalComputations_in));
        postString.append("&values=");
        for (unsigned long iCount = 0; iCount < numberOfVariables_in; iCount++)
        {
            char strcValue[25];

            paceval_dConvertFloatToString(strcValue, values_in[iCount]);
            postEncoded = curl_easy_escape(curl, strcValue, 0);
            postString.append(postEncoded);
            curl_free(postEncoded);
            if (iCount != numberOfVariables_in - 1)
            {
                postEncoded = curl_easy_escape(curl, ";", (int)strlen(";"));
                postString.append(postEncoded);
                curl_free(postEncoded);
            }
        }

        curl_easy_setopt(curl, CURLOPT_URL, urlString.c_str());
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postString.c_str());
        curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback_Remote);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);
        curl_easy_setopt(curl, CURLOPT_ACCEPT_ENCODING, "br, gzip, deflate");
        curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE_LARGE, (long)postString.length());
        res = curl_easy_perform(curl);
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &httpCode);
        curl_easy_cleanup(curl);

        WriteServerLogging("POST_URL: ", urlString.c_str());
        WriteServerLogging("POST_FIELDS: ", postString.c_str());
        tempString = std::to_string(httpCode);
        WriteServerLogging("RESPONSE_CODE: ", tempString.c_str());
        WriteServerLogging("RESPONSE_DATA: ", readBuffer.c_str());

        if (httpCode == 200)
        {
            if ((readBuffer == "")
                    || (readBuffer == "{ \"error\": \"internal error, please contact service admin\" }"))
            {

                *hasError_out = true;
                for (unsigned int iCount = 0; iCount < numberOfpacevalComputations_in; iCount++)
                {
                    errorTypes_out[iCount] = PACEVAL_ERR_FATAL_CONNECTING_SERVER;
                }
                WriteServerLogging("return false", "\n");
                return false;
            }

            if (readBuffer == "{ \"error\": \"missing parameters\" }")
            {
                *hasError_out = true;
                for (unsigned int iCount = 0; iCount < numberOfpacevalComputations_in; iCount++)
                {
                    errorTypes_out[iCount] = PACEVAL_ERR_FATAL_PARAMETERS_SERVER;
                }
                WriteServerLogging("return false", "\n");
                return false;
            }

            startPos = readBuffer.find("\"results\":[\"");
            if (startPos < readBuffer.size())
            {
                startPos = startPos + strlen("\"results\":[\"");
                for (unsigned int iCount = 0; iCount < numberOfpacevalComputations_in; iCount++)
                {
                    endPos = readBuffer.find("\"", startPos);
                    strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                    strcValue[endPos - startPos] = '\0';
                    results_out[iCount] = paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                          false, NULL, NULL);

                    if (iCount != numberOfpacevalComputations_in - 1)
                    {
                        startPos = readBuffer.find(",\"", endPos + 1);
                        startPos = startPos + strlen(",\"");
                    }
                }
            }

            if (trustedMinResults_out != NULL)
            {
                startPos = readBuffer.find("\"interval-min-results\":[\"");
                if (startPos < readBuffer.size())
                {
                    startPos = startPos + strlen("\"interval-min-results\":[\"");
                    for (unsigned int iCount = 0; iCount < numberOfpacevalComputations_in; iCount++)
                    {
                        endPos = readBuffer.find("\"", startPos);
                        strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                        strcValue[endPos - startPos] = '\0';
                        trustedMinResults_out[iCount] = paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                                        false, NULL, NULL);

                        if (iCount != numberOfpacevalComputations_in - 1)
                        {
                            startPos = readBuffer.find(",\"", endPos + 1);
                            startPos = startPos + strlen(",\"");
                        }
                    }
                }
            }

            if (trustedMaxResults_out != NULL)
            {
                startPos = readBuffer.find("\"interval-max-results\":[\"");
                if (startPos < readBuffer.size())
                {
                    startPos = startPos + strlen("\"interval-max-results\":[\"");
                    for (unsigned int iCount = 0; iCount < numberOfpacevalComputations_in; iCount++)
                    {
                        endPos = readBuffer.find("\"", startPos);
                        strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                        strcValue[endPos - startPos] = '\0';
                        trustedMaxResults_out[iCount] = paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                                        false, NULL, NULL);

                        if (iCount != numberOfpacevalComputations_in - 1)
                        {
                            startPos = readBuffer.find(",\"", endPos + 1);
                            startPos = startPos + strlen(",\"");
                        }
                    }
                }
            }

            if (timeComputeRemote_out != NULL)
            {
                startPos = readBuffer.find("\"time-calculate\":\"");
                if (startPos < readBuffer.size())
                {
                    startPos = startPos + strlen("\"time-calculate\":\"");
                    endPos = readBuffer.find("s\",", startPos);
                    strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                    strcValue[endPos - startPos] = '\0';
                    *timeComputeRemote_out = paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                             false, NULL, NULL);
                }
            }

            if (hasError_out != NULL)
            {
                startPos = readBuffer.find("\"hasError\":");
                if (startPos < readBuffer.size())
                {
                    startPos = startPos + strlen("\"hasError\":");
                    endPos = readBuffer.find(",", startPos);
                    strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                    strcValue[endPos - startPos] = '\0';
                    if (strcmp(strcValue, "true") == 0)
                    {
                        *hasError_out = true;
                    }
                    else
                    {
                        *hasError_out = false;
                    }
                }
            }

            startPos = readBuffer.find("\"error-type-numbers\":[");
            if (startPos < readBuffer.size())
            {
                startPos = startPos + strlen("\"error-type-numbers\":[");
                for (unsigned int iCount = 0; iCount < numberOfpacevalComputations_in; iCount++)
                {
                    if (iCount != numberOfpacevalComputations_in - 1)
                        endPos = readBuffer.find(",", startPos);
                    else if (iCount == numberOfpacevalComputations_in - 1)
                        endPos = readBuffer.find("]", startPos);

                    strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                    strcValue[endPos - startPos] = '\0';
                    errorTypes_out[iCount] = paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                             false, NULL, NULL);

                    if (iCount != numberOfpacevalComputations_in - 1)
                    {
                        startPos = endPos + 1;
                    }
                }
            }

            WriteServerLogging("return true", "\n");
            return true;
        }
    }

    *hasError_out = true;
    for (unsigned int iCount = 0; iCount < numberOfpacevalComputations_in; iCount++)
    {
        errorTypes_out[iCount] = PACEVAL_ERR_FATAL_CONNECTING_SERVER;
    }
    WriteServerLogging("return false", "\n");
    return false;
}

extern "C" bool paceval_Remote_GetComputationInformationXML(char* pacevalServerStr_in,
        const char* handle_pacevalComputationAsString_in,
        unsigned long* sizeOf_paceval_strXML_out,
        char* paceval_strXML_out)
{
    CURL *curl;

    curl = curl_easy_init();
    if (curl)
    {
        CURLcode res;
        std::string postString;
        std::string readBuffer;
        std::string urlString;
        std::string tempString;
        char *postEncoded;
        long httpCode(0);
        size_t startPos;
        size_t endPos;

        urlString = pacevalServerStr_in;
        urlString.append("/GetComputationInformationXML/");
        postString = "handle_pacevalComputation=";
        postEncoded = curl_easy_escape(curl, handle_pacevalComputationAsString_in, 0);
        postString.append(postEncoded);
        curl_free(postEncoded);

        curl_easy_setopt(curl, CURLOPT_URL, urlString.c_str());
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postString.c_str());
        curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback_Remote);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);
        curl_easy_setopt(curl, CURLOPT_ACCEPT_ENCODING, "br, gzip, deflate");
        curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE_LARGE, (long)postString.length());
        res = curl_easy_perform(curl);
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &httpCode);
        curl_easy_cleanup(curl);

        WriteServerLogging("POST_URL: ", urlString.c_str());
        WriteServerLogging("POST_FIELDS: ", postString.c_str());
        tempString = std::to_string(httpCode);
        WriteServerLogging("RESPONSE_CODE: ", tempString.c_str());
        WriteServerLogging("RESPONSE_DATA: ", readBuffer.c_str());

        if (httpCode == 200)
        {
            if ((readBuffer == "")
                    || (readBuffer == "{ \"error\": \"internal error, please contact service admin\" }"))
            {
                WriteServerLogging("return false", "\n");
                return false;
            }

            if (readBuffer == "{ \"error\": \"missing parameters\" }")
            {
                WriteServerLogging("return false", "\n");
                return false;
            }

            startPos = readBuffer.find("\"information-XML\":\"");
            if (startPos < readBuffer.size())
            {
                startPos = startPos + strlen("\"information-XML\":\"");
                endPos = readBuffer.find("\",", startPos);
                if (paceval_strXML_out != NULL)
                {
                    strncpy(paceval_strXML_out, &readBuffer.c_str()[startPos], endPos - startPos);
                    paceval_strXML_out[endPos - startPos] = '\0';
                }

                *sizeOf_paceval_strXML_out = endPos - startPos + 1;

                WriteServerLogging("return true", "\n");
                return true;
            }
        }

        WriteServerLogging("return false", "\n");
        return false;
    }

    WriteServerLogging("return false", "\n");
    return false;
}

extern "C" bool paceval_Remote_GetErrorInformation(char* pacevalServerStr_in,
        const char* handle_pacevalComputationAsString_in,
        bool* hasError_out,
        int* errorType_out,
        char* errorOperator_out,
        char* errorTypeString_out,
        char* errorMessageString_out)
{
    CURL *curl;

    curl = curl_easy_init();
    if (curl)
    {
        CURLcode res;
        std::string postString;
        std::string readBuffer;
        std::string urlString;
        std::string tempString;
        char *postEncoded;
        long httpCode(0);
        size_t startPos;
        size_t endPos;
        int errType;
        char strcValue[500];
        long errPosition;

        urlString = pacevalServerStr_in;
        urlString.append("/GetErrorInformation/");
        postString = "handle_pacevalComputation=";
        postEncoded = curl_easy_escape(curl, handle_pacevalComputationAsString_in, 0);
        postString.append(postEncoded);
        curl_free(postEncoded);

        curl_easy_setopt(curl, CURLOPT_URL, urlString.c_str());
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postString.c_str());
        curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback_Remote);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);
        curl_easy_setopt(curl, CURLOPT_ACCEPT_ENCODING, "br, gzip, deflate");
        curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE_LARGE, (long)postString.length());
        res = curl_easy_perform(curl);
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &httpCode);
        curl_easy_cleanup(curl);

        WriteServerLogging("POST_URL: ", urlString.c_str());
        WriteServerLogging("POST_FIELDS: ", postString.c_str());
        tempString = std::to_string(httpCode);
        WriteServerLogging("RESPONSE_CODE: ", tempString.c_str());
        WriteServerLogging("RESPONSE_DATA: ", readBuffer.c_str());

        if (httpCode == 200)
        {
            if ((readBuffer == "")
                    || (readBuffer == "{ \"error\": \"internal error, please contact service admin\" }"))
            {
                *errorType_out = PACEVAL_ERR_FATAL_CONNECTING_SERVER;
                strcpy(errorTypeString_out, "[PACEVAL_ERR_FATAL_CONNECTING_SERVER]");
                strcpy(errorMessageString_out, "The paceval-server could not be connected (PACEVAL_ERR_FATAL_CONNECTING_SERVER).");
                WriteServerLogging("return false", "\n");
                return false;
            }

            if (readBuffer == "{ \"error\": \"missing parameters\" }")
            {
                *errorType_out = PACEVAL_ERR_FATAL_PARAMETERS_SERVER;
                strcpy(errorTypeString_out, "[PACEVAL_ERR_FATAL_PARAMETERS_SERVER]");
                strcpy(errorMessageString_out, "The paceval-server could not process the parameters (PACEVAL_ERR_FATAL_PARAMETERS_SERVER).");
                WriteServerLogging("return false", "\n");
                return false;
            }

            if (hasError_out != NULL)
            {
                startPos = readBuffer.find("\"hasError\":");
                if (startPos < readBuffer.size())
                {
                    startPos = startPos + strlen("\"hasError\":");
                    endPos = readBuffer.find(",", startPos);
                    strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                    strcValue[endPos - startPos] = '\0';
                    if (strcmp(strcValue, "true") == 0)
                    {
                        *hasError_out = true;
                    }
                    else
                    {
                        *hasError_out = false;
                    }
                }
            }

            if (errorTypeString_out != NULL)
            {
                startPos = readBuffer.find("\"error-type\":\"");
                if (startPos < readBuffer.size())
                {
                    startPos = startPos + strlen("\"error-type\":\"");
                    endPos = readBuffer.find("\",", startPos);
                    strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                    strcValue[endPos - startPos] = '\0';

                    strcpy(errorTypeString_out, "\"");
                    strcat(errorTypeString_out, strcValue);
                    strcat(errorTypeString_out, "\"");
                }
            }

            if (errorType_out != NULL)
            {
                startPos = readBuffer.find("\"error-type-number\":");
                if (startPos < readBuffer.size())
                {
                    startPos = startPos + strlen("\"error-type-number\":");
                    endPos = readBuffer.find(",", startPos);
                    strncpy(strcValue, &readBuffer.c_str()[startPos], endPos - startPos);
                    strcValue[endPos - startPos] = '\0';
                    *errorType_out = (int)paceval_dConvertStringToFloat(strcValue, &errType, &errPosition,
                                     false, NULL, NULL);
                }
            }

            if (errorOperator_out != NULL)
            {
                startPos = readBuffer.find("\"error-operator\":\"");
                if (startPos < readBuffer.size())
                {
                    startPos = startPos + strlen("\"error-operator\":\"");
                    endPos = readBuffer.find("\",", startPos);
                    strncpy(errorOperator_out, &readBuffer.c_str()[startPos], endPos - startPos);
                    errorOperator_out[endPos - startPos] = '\0';
                }
            }

            if (errorMessageString_out != NULL)
            {
                startPos = readBuffer.find("\"error-message\":\"");
                if (startPos < readBuffer.size())
                {
                    startPos = startPos + strlen("\"error-message\":\"");
                    endPos = readBuffer.find("\",", startPos);
                    strncpy(errorMessageString_out, &readBuffer.c_str()[startPos], endPos - startPos);
                    errorMessageString_out[endPos - startPos] = '\0';
                }
            }
            WriteServerLogging("return true", "\n");
            return true;
        }

        WriteServerLogging("return false", "\n");
        return false;
    }

    *errorType_out = PACEVAL_ERR_FATAL_CONNECTING_SERVER;
    strcpy(errorTypeString_out, "[PACEVAL_ERR_FATAL_CONNECTING_SERVER]");
    strcpy(errorMessageString_out, "The paceval-server could not be connected (PACEVAL_ERR_FATAL_CONNECTING_SERVER).");
    WriteServerLogging("return false", "\n");
    return false;
}
