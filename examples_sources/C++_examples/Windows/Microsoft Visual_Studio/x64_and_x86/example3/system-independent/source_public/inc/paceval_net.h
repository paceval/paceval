//---------------------------------------------------------------------------
// Copyright 2022. Version 4.x 2022 paceval.[Registered Trade Mark]
//                             All rights reserved.
// Author(s) : paceval., see http://www.paceval.com
// File      : paceval_net.h
//---------------------------------------------------------------------------

//---------------------------------------------------------------------------
#ifndef paceval_netH
#define paceval_netH

#ifdef __cplusplus
extern "C" {
#endif
	//Communicates with a paceval-service
	//see https://app.swaggerhub.com/apis-docs/paceval/paceval-service/4.04

	//-------------------------------------------------------------------------------------
    //  paceval_Remote_CreateComputation
    //  remote version of https://paceval.com/api/#paceval_CreateComputation
	//-------------------------------------------------------------------------------------
	bool paceval_Remote_CreateComputation(char* pacevalServerStr_in,
		char* handle_pacevalComputationAsString_out,
		const char* functionString_in,
		unsigned long numberOfVariables_in,
		const char* variables_in,
		bool useInterval_in,
		int* errorType_out,
		char* errorTypeString_out,
		char* errorMessageString_out);

	//-------------------------------------------------------------------------------------
	//  paceval_dRemote_mathv
	//  remote version of https://paceval.com/api/#paceval_dmathv
	//-------------------------------------------------------------------------------------
	double paceval_dRemote_mathv(char* pacevalServerStr_in,
		char* handle_pacevalComputationAsString_out,
		const char* functionString_in,
		unsigned long numberOfVariables_in,
		const char* variables_in,
		double values_in[],
		int* errorType_out,
		char* errorTypeString_out,
		char* errorMessageString_out,
		double* timeComputeRemote_out);

	//-------------------------------------------------------------------------------------
	//  paceval_dRemote_mathvi
	//  remote version of https://paceval.com/api/#paceval_dmathvi
	//-------------------------------------------------------------------------------------
	double paceval_dRemote_mathvi(char* pacevalServerStr_in,
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
		double* timeComputeRemote_out);

	//-------------------------------------------------------------------------------------
	//  paceval_dRemote_GetComputationResult
	//  remote version of https://paceval.com/api/#paceval_GetComputationResult
	//-------------------------------------------------------------------------------------
	bool paceval_dRemote_GetComputationResult(char* pacevalServerStr_in,
		const char* handle_pacevalComputationAsString_in,
		unsigned long numberOfVariables_in,
		double values_in[],
		double* result_out,
		double* trustedMinResult_out,
		double* trustedMaxResult_out,
		int* errorType_out,
		char* errorTypeString_out,
		char* errorMessageString_out,
		double* timeComputeRemote_out);

	//-------------------------------------------------------------------------------------
    //  paceval_dRemote_GetComputationResultExt
    //  remote version of https://paceval.com/api/#paceval_dGetComputationResultExt
    //-------------------------------------------------------------------------------------
	bool paceval_dRemote_GetComputationResultExt(char* pacevalServerStr_in,
		const char* handle_pacevalComputationAsString_in,
		unsigned long numberOfVariables_in,
		double values_in[],
		unsigned long numberOfCalculations_in,
		double* results_out,
		double* trustedMinResults_out,
		double* trustedMaxResults_out,
		bool* hasError_out,
		int* errorTypes_out,
		double* timeComputeRemote_out);

	//-------------------------------------------------------------------------------------
	//  paceval_dRemote_GetMultipleComputationsResults
	//  remote version of https://paceval.com/api/#paceval_dGetMultipleComputationsResults
	//-------------------------------------------------------------------------------------
	bool paceval_dRemote_GetMultipleComputationsResults(char* pacevalServerStr_in,
		const char* handle_pacevalComputationAsStrings_in,
		unsigned long numberOfpacevalComputations_in,
		unsigned long numberOfVariables_in,
		double values_in[],
		double* results_out,
		double* trustedMinResults_out,
		double* trustedMaxResults_out,
		bool* hasError_out,
		int* errorTypes_out,
		double* timeComputeRemote_out);

	//---------------------------------------------------------------------------
	//  paceval_Remote_GetComputationInformationXML
	//  remote version of https://paceval.com/api/#paceval_GetComputationInformationXML
	//---------------------------------------------------------------------------
	bool paceval_Remote_GetComputationInformationXML(char* pacevalServerStr_in,
		const char* handle_pacevalComputationAsString_in,
		unsigned long* sizeOf_paceval_strXML_out,
		char* paceval_strXML_out);

	//---------------------------------------------------------------------------
	//  paceval_Remote_GetErrorInformation
	//  remote version of https://paceval.com/api/#paceval_GetErrorInformation
	//---------------------------------------------------------------------------
	bool paceval_Remote_GetErrorInformation(char* pacevalServerStr_in,
		const char* handle_pacevalComputationAsString_in,
		bool* hasError_out,
		int* errorType_out,
		long* errorPosition,
		char* errorOperator_out,
		char* errorTypeString_out,
		char* errorMessageString_out);

#ifdef __cplusplus
}
#endif
//---------------------------------------------------------------------------
#endif //paceval_netH