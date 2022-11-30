import requests


def Demo(mainUrl, functionString, numberOfVariables, variables, values, interval):

    urlSchema = mainUrl + "/Demo/?functionString={}&numberOfVariables={}&variables={}&values={}&interval={}"
    url = urlSchema.format(functionString, numberOfVariables, variables, values, interval)

    payload={}

    response = requests.request("GET", url, data=payload)

    print(response.text)

    return response

def CreateComputation(mainUrl, functionString, numberOfVariables, variables, values, interval):

    urlSchema = mainUrl + "/CreateComputation/?functionString={}&numberOfVariables={}&variables={}&values={}&interval={}"
    url = urlSchema.format(functionString, numberOfVariables, variables, values, interval)

    payload={}

    response = requests.request("GET", url, data=payload)

    print(response.text)

    return response

def GetComputationResult(mainUrl, handle_pacevalComputation, values,):

    urlSchema = mainUrl + "/GetComputationResult/?handle_pacevalComputation={}&values={}"
    url = urlSchema.format(handle_pacevalComputation, values)

    payload={}

    response = requests.request("GET", url, data=payload)

    print(response.text)

    return response

def GetErrorInformation(mainUrl, handle_pacevalComputation):

    urlSchema = mainUrl + "/GetErrorInformation/?handle_pacevalComputation={}"
    url = urlSchema.format(handle_pacevalComputation)

    payload={}

    response = requests.request("GET", url, data=payload)

    print(response.text)

    return response

def GetComputationResultExt(mainUrl, handle_pacevalComputation, numberOfCalculations, values,):

    urlSchema = mainUrl + "/GetComputationResultExt/?handle_pacevalComputation={}&numberOfCalculations={}&values={}"
    url = urlSchema.format(handle_pacevalComputation, numberOfCalculations, values)

    payload={}

    response = requests.request("GET", url, data=payload)

    print(response.text)

    return response

def GetComputationInformationXML(mainUrl, handle_pacevalComputation):

    urlSchema = mainUrl + "/GetComputationInformationXML/?handle_pacevalComputation={}"
    url = urlSchema.format(handle_pacevalComputation)

    payload={}

    response = requests.request("GET", url, data=payload)

    print(response.text)

    return response

