#---------------------------------------------------------------------------
# Copyright 1997-2014. Version 1.x Joerg Koenning - All rights reserved.
# Copyright 2015-2022. Version 2.x, 3.x, 4.x 2015-2022 paceval.[Registered Trade Mark]
#                                            All rights reserved.
# Author(s) : paceval., see http://www.paceval.com
# Reference: https://app.swaggerhub.com/apis/paceval/paceval-service/4.04
# Documentation: https://pypi.org/project/paceval/
#---------------------------------------------------------------------------

import requests


def Demo(mainUrl, functionString, numberOfVariables, variables, values, interval):

    urlSchema = mainUrl + "/Demo/?functionString={}&numberOfVariables={}&variables={}&values={}&interval={}"
    url = urlSchema.format(functionString, numberOfVariables, variables, values, interval)

    payload={}

    response = requests.request("POST", url, data=payload)

    return response

def CreateComputation(mainUrl, functionString, numberOfVariables, variables, values, interval):

    urlSchema = mainUrl + "/CreateComputation/?functionString={}&numberOfVariables={}&variables={}&values={}&interval={}"
    url = urlSchema.format(functionString, numberOfVariables, variables, values, interval)

    payload={}

    response = requests.request("POST", url, data=payload)

    return response

def GetComputationResult(mainUrl, handle_pacevalComputation, values,):

    urlSchema = mainUrl + "/GetComputationResult/?handle_pacevalComputation={}&values={}"
    url = urlSchema.format(handle_pacevalComputation, values)

    payload={}

    response = requests.request("POST", url, data=payload)

    return response

def GetErrorInformation(mainUrl, handle_pacevalComputation):

    urlSchema = mainUrl + "/GetErrorInformation/?handle_pacevalComputation={}"
    url = urlSchema.format(handle_pacevalComputation)

    payload={}

    response = requests.request("POST", url, data=payload)

    return response

def GetComputationResultExt(mainUrl, handle_pacevalComputation, numberOfCalculations, values,):

    urlSchema = mainUrl + "/GetComputationResultExt/?handle_pacevalComputation={}&numberOfCalculations={}&values={}"
    url = urlSchema.format(handle_pacevalComputation, numberOfCalculations, values)

    payload={}

    response = requests.request("POST", url, data=payload)

    return response

def GetComputationInformationXML(mainUrl, handle_pacevalComputation):

    urlSchema = mainUrl + "/GetComputationInformationXML/?handle_pacevalComputation={}"
    url = urlSchema.format(handle_pacevalComputation)

    payload={}

    response = requests.request("POST", url, data=payload)

    return response

