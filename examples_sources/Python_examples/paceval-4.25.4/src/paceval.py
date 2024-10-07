#---------------------------------------------------------------------------
# Copyright ©1994-2024. Version 1.x, 2.x, 3.x, 4.x ©1994-2024
#       Joerg Koenning & paceval.[Registered Trade Mark] All rights reserved.
# Author(s) : paceval., see http://www.paceval.com
# Reference: https://app.swaggerhub.com/apis/paceval/paceval-service
# Documentation: https://pypi.org/project/paceval/
#---------------------------------------------------------------------------


# see https://app.swaggerhub.com/apis/paceval/paceval-service/4.25#/default/post_Demo_
def Demo(mainUrl, functionString, numberOfVariables, variables, values, interval):
    import requests

    url = mainUrl + "/Demo/"
    payload = {
        "functionString": functionString,
        "numberOfVariables": numberOfVariables,
        "variables": variables,
        "values": values,
        "interval": interval
    }
 
    response = requests.request("POST", url, data=payload)
 
    return response


# see https://app.swaggerhub.com/apis/paceval/paceval-service/4.25#/default/post_CreateComputation_
def CreateComputation(mainUrl, functionString, numberOfVariables, variables, interval):
    import requests

    url = mainUrl + "/CreateComputation/"
    payload = {
        "functionString": functionString,
        "numberOfVariables": numberOfVariables,
        "variables": variables,
        "interval": interval
    }
 
    response = requests.request("POST", url, data=payload)
 
    return response


# see https://app.swaggerhub.com/apis/paceval/paceval-service/4.25#/default/post_GetComputationResult_
def GetComputationResult(mainUrl, handle_pacevalComputation, values):
    import requests

    url = mainUrl + "/GetComputationResult/"
    payload = {
        "handle_pacevalComputation": handle_pacevalComputation,
        "values": values
    }
 
    response = requests.request("POST", url, data=payload)
 
    return response


# see https://app.swaggerhub.com/apis/paceval/paceval-service/4.25#/default/post_GetErrorInformation_
def GetErrorInformation(mainUrl, handle_pacevalComputation):
    import requests

    url = mainUrl + "/GetErrorInformation/"
    payload = {
        "handle_pacevalComputation": handle_pacevalComputation
    }
 
    response = requests.request("POST", url, data=payload)
 
    return response


# see https://app.swaggerhub.com/apis/paceval/paceval-service/4.25#/default/post_GetComputationResultExt_
def GetComputationResultExt(mainUrl, handle_pacevalComputation, numberOfCalculations, values):
    import requests

    url = mainUrl + "/GetComputationResultExt/"
    payload = {
        "handle_pacevalComputation": handle_pacevalComputation,
        "numberOfCalculations": numberOfCalculations,
        "values": values
    }
 
    response = requests.request("POST", url, data=payload)
 
    return response


# see https://app.swaggerhub.com/apis/paceval/paceval-service/4.25#/default/post_GetMultipleComputationsResults_
def GetMultipleComputationsResults(mainUrl, handle_pacevalComputations, numberOfpacevalComputations, values):
    import requests

    url = mainUrl + "/GetMultipleComputationsResults/"
    payload = {
        "handle_pacevalComputations": handle_pacevalComputations,
        "numberOfpacevalComputations": numberOfpacevalComputations,
        "values": values
    }
 
    response = requests.request("POST", url, data=payload)
 
    return response


# see https://app.swaggerhub.com/apis/paceval/paceval-service/4.25#/default/post_GetMultipleComputationsResultsExt
def GetMultipleComputationsResultsExt(mainUrl, handle_pacevalComputations, numberOfpacevalComputations, numberOfCalculations, values):
    import requests

    url = mainUrl + "/GetMultipleComputationsResultsExt/"
    payload = {
        "handle_pacevalComputations": handle_pacevalComputations,
        "numberOfpacevalComputations": numberOfpacevalComputations,
        "numberOfCalculations": numberOfCalculations,
        "values": values
    }
 
    response = requests.request("POST", url, data=payload)
 
    return response


# see https://app.swaggerhub.com/apis/paceval/paceval-service/4.25#/default/post_GetComputationInformationXML_
def GetComputationInformationXML(mainUrl, handle_pacevalComputation):
    import requests

    url = mainUrl + "/GetComputationInformationXML/"
    payload = {
        "handle_pacevalComputation": handle_pacevalComputation
    }
 
    response = requests.request("POST", url, data=payload)
 
    return response
