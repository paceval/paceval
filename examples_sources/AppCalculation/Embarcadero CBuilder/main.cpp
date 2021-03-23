//---------------------------------------------------------------------------
// Author(s) : paceval®, http://www.paceval.com
// File      : paceval-calculation main.cpp
//---------------------------------------------------------------------------

#include <vcl.h>
#pragma hdrstop

#include <algorithm>
using namespace std;

#include <stdlib.h>

#include "..\system-independent\source_public\inc\paceval_main.h" //We include the paceval header

#include "main.h"
#include "graph.h"

#include <shellapi.h>
#include <stdio.h>
#include <math.h>

#include "paceval_addon.h"

//---------------------------------------------------------------------------
#pragma package(smart_init)
#pragma resource "*.dfm"

TpacevalFormMainCalculation *pacevalFormMainCalculation;

const char* CreateErrorMessage(char* messageBuffer, int pacevalErrorType, int lengthBuffer);
//---------------------------------------------------------------------------

__fastcall TpacevalFormMainCalculation::TpacevalFormMainCalculation(TComponent* Owner)
	: TForm(Owner)
{
	paceval_available = false;
	parameterStartStr = "";

	for (int iCount = 1; iCount <= ParamCount(); iCount++)
	{
		parameterStartStr = parameterStartStr + ParamStr(iCount) + " ";
	}

	handle_pacevalComputation = NULL;
	selectedVariableRow = 1;

	StringGridVariables->RowCount = PACEVAL_DEMO_USE_MAX_NUMBER_OF_VARIABLES + 1;
	LabelNumberOfVariables->Caption = AnsiString(StringGridVariables->RowCount - 1);
	precisionType = PACEVAL_CALCULATION_PRECISION_LONG_DOUBLE;
}
//---------------------------------------------------------------------------

void __fastcall TpacevalFormMainCalculation::ButtonExitClick(TObject *Sender)
{
	Close();
}
//---------------------------------------------------------------------------

void __fastcall TpacevalFormMainCalculation::RichEditFunctionChange(TObject *Sender)
{
	DataChangedForCalculation();
}
//---------------------------------------------------------------------------

void TpacevalFormMainCalculation::DataChangedForCalculation()
{
	//Delete the paceval-Computation object because data has changed
	if (handle_pacevalComputation != NULL)
	{
		paceval_DeleteComputation(handle_pacevalComputation);
		handle_pacevalComputation = NULL;
	}

	ButtonCreateCalculate->Caption = "Create object for computation and calculate";
	LabelStatus->Caption = AnsiString("Data changed - next step creation");

	EditResult->Text = "no result, please, press \"Create object for computation and calculate\"";
	if (RadioButtonTINCOn->Checked)
	{
		EditMinResultTINC->Text = "no result, please, press \"Create object for computation and calculate\"";
		EditMaxResultTINC->Text = "no result, please, press \"Create object for computation and calculate\"";
	}
	else
	{
		EditMinResultTINC->Text = "use Interval \"off\"";
		EditMaxResultTINC->Text = "use Interval \"off\"";
	}

	LabelLength->Caption = String(RichEditFunction->Text.Length());
	LabelCreationTime->Caption = "0ms";
	LabelThreadsUsages->Caption = "0";
	LabelCalculationTime->Caption = "0ms";
	RichEditInformation->Clear();
}


bool paceval_callbackStatus(const PACEVAL_HANDLE handle_pacevalComputation_in,
							const paceval_eStatusTypes paceval_eStatus_in, const int percentageDone_in)
{
	return pacevalFormMainCalculation->Handle_pacevalCallbackStatus(paceval_eStatus_in,
			percentageDone_in);
}

bool paceval_callbackUserFunction1(const int useCalculationPrecision_in,
								   const long double* valueFieldAsLongDouble,
								   long double* resultAsLongDouble,
								   const double* valueFieldAsDouble,
								   double* resultAsDouble,
								   const float* valueFieldAsFloat,
								   float* resultAsFloat)
{
	switch (useCalculationPrecision_in)
	{
	case PACEVAL_CALCULATION_PRECISION_LONG_DOUBLE:
	{
		*resultAsLongDouble =
			sinl(*valueFieldAsLongDouble) * cosl(*valueFieldAsLongDouble);

		return true;
	}
	break;
	case PACEVAL_CALCULATION_PRECISION_DOUBLE:
	{
		*resultAsDouble =
			sin(*valueFieldAsDouble) * cos(*valueFieldAsDouble);

		return true;
	}
	break;
	case PACEVAL_CALCULATION_PRECISION_FLOAT:
	{
		*resultAsFloat =
			sin(*valueFieldAsFloat) * cos(*valueFieldAsFloat);
	}
	}

	return false;
}

void TpacevalFormMainCalculation::DoFormUpdate()
{
	MSG msg;

	while (::PeekMessage(&msg, 0, 0, 0, PM_REMOVE))
	{
		TranslateMessage(&msg);
		DispatchMessage(&msg);
	}
}

bool TpacevalFormMainCalculation::Handle_pacevalCallbackStatus(int paceval_eStatus,
		int percentageDone)
{
	if (paceval_eStatus == PACEVAL_STATUS_NO_STATUS)
	{
		LabelStatus->Caption = AnsiString("Nothing to do... yet!");
	}
	else if (paceval_eStatus == PACEVAL_STATUS_ANALYSIS_PROGRESS)
	{
		LabelStatus->Caption = AnsiString("Creation ")
							   + AnsiString(percentageDone)
							   + AnsiString("% done");

		if (percentageDone == 100)
		{
			LabelStatus->Caption = LabelStatus->Caption + " - next step calculation only";
		}
	}
	else if (paceval_eStatus == PACEVAL_STATUS_ANALYSIS_ERROR)
	{
		LabelStatus->Caption = AnsiString("Creation error");
	}

	DoFormUpdate();
	return true;
}

void __fastcall TpacevalFormMainCalculation::doCreate_pacevalCalculation()
{
	int numberOfVariables;
	bool useInterval;
	AnsiString stringVariablesForCalculation;
	AnsiString stringSingleVariable;
	AnsiString stringUserFunction;
	long ctime;

	numberOfVariables = StringGridVariables->RowCount - 1;

	if (RadioButtonTINCOn->Checked)
	{
		useInterval = true;
	}
	else
	{
		useInterval = false;
	}

	stringVariablesForCalculation = "";
	for (unsigned long iCount = 0; iCount < (unsigned long)numberOfVariables; iCount++)
	{
		if (iCount > 0)
		{
			stringVariablesForCalculation = stringVariablesForCalculation + " ";
		}
		stringSingleVariable = StringGridVariables->Rows[iCount + 1]->Strings[0];
		stringVariablesForCalculation = stringVariablesForCalculation + stringSingleVariable;
	}

	Screen->Cursor = crHourGlass;
	ctime = GetCurrentTime();

	handle_pacevalComputation = paceval_CreateComputation(AnsiString(RichEditFunction->Text).c_str(),
								numberOfVariables,
								stringVariablesForCalculation.c_str(),
								useInterval,
								&paceval_callbackStatus);

	ctime = GetCurrentTime() - ctime;
	if (ctime == 0)
		ctime = ctime + 1;
	LabelCreationTime->Caption = "<" + String(ctime) + "ms";
	Screen->Cursor = crDefault;

	if (paceval_GetIsError(handle_pacevalComputation))
	{
		int errType;
		char errOperator[25];
		long errPosition;
		int maxMessageDetailsLength;
		char* errMessage;
		char* errDetails;

		errType = paceval_GetErrorInformation(handle_pacevalComputation,
											  errOperator, &errPosition);

		RichEditFunction->SelStart = errPosition;
		RichEditFunction->SelLength = 1;
		RichEditFunction->SetFocus();

		maxMessageDetailsLength = paceval_CreateErrorInformationText(handle_pacevalComputation,
								  NULL, NULL);
		errMessage = new char[2 * maxMessageDetailsLength];
		errDetails = new char[maxMessageDetailsLength];

		maxMessageDetailsLength = paceval_CreateErrorInformationText(handle_pacevalComputation,
								  errMessage, errDetails);
		strcat(errMessage, "\r\n");
		strcat(errMessage, errDetails);

		MessageBox(Handle, errMessage, "Error in creation", MB_ICONERROR);

		delete[] errMessage;
		delete[] errDetails;
	}
}

void __fastcall TpacevalFormMainCalculation::doCalculate_pacevalCalculation()
{
	long double ldResult;
	double dResult;
	float fResult;
	long double* ldValuesVariablesArray;
	double* dValuesVariablesArray;
	float* fValuesVariablesArray;
	int numberOfVariables;
	AnsiString stringValueVariable;
	char* endptr;
	bool hasError = false;
	long double ldMinResultInterval;
	long double ldMaxResultInterval;
	double dMinResultInterval;
	double dMaxResultInterval;
	float fMinResultInterval;
	float fMaxResultInterval;
	char strcRestult[100];
	AnsiString strResult;
	int precision;
	long ctime;
	int errType;

	numberOfVariables = StringGridVariables->RowCount - 1;

	if (RadioButtonLongDouble->Checked)
		ldValuesVariablesArray = new long double[numberOfVariables];
	else if (RadioButtonDouble->Checked)
		dValuesVariablesArray = new double[numberOfVariables];
	else if (RadioButtonFloat->Checked)
		fValuesVariablesArray = new float[numberOfVariables];

	for (unsigned long iCount = 0; iCount < (unsigned long)numberOfVariables; iCount++)
	{
		stringValueVariable = StringGridVariables->Rows[iCount + 1]->Strings[1];

		if (RadioButtonLongDouble->Checked)
		{
			ldValuesVariablesArray[iCount] =
				paceval_ldConvertStringToFloat(stringValueVariable.c_str(),
											   &errType, NULL, false, NULL, NULL);
		}
		else if (RadioButtonDouble->Checked)
		{
			dValuesVariablesArray[iCount] =
				paceval_dConvertStringToFloat(stringValueVariable.c_str(),
											  &errType, NULL, false, NULL, NULL);
		}
		else if (RadioButtonFloat->Checked)
		{
			fValuesVariablesArray[iCount] =
				paceval_fConvertStringToFloat(stringValueVariable.c_str(),
											  &errType, NULL, false, NULL, NULL);
		}

		if (errType != PACEVAL_ERR_NO_ERROR)
			hasError = true;
	}

	if (hasError == true)
	{
		AnsiString errText;
		errText = AnsiString("Error variable");
		MessageBox(Handle, errText.c_str(),
				   "Error in calculation", MB_ICONERROR);
	}

	ctime = GetCurrentTime();

	//Get the result of the function for the variables of the user
	if (RadioButtonLongDouble->Checked)
	{
		ldResult =
			paceval_ldGetComputationResult(handle_pacevalComputation,
										   ldValuesVariablesArray,
										   &ldMinResultInterval, &ldMaxResultInterval);
		delete[] ldValuesVariablesArray;

		precision = paceval_ldConvertFloatToString(strcRestult, ldResult);
	}
	else if (RadioButtonDouble->Checked)
	{
		dResult =
			paceval_dGetComputationResult(handle_pacevalComputation,
										  dValuesVariablesArray,
										  &dMinResultInterval, &dMaxResultInterval);
		delete[] dValuesVariablesArray;

		precision = paceval_dConvertFloatToString(strcRestult, dResult);
	}
	else if (RadioButtonFloat->Checked)
	{
		fResult =
			paceval_fGetComputationResult(handle_pacevalComputation,
										  fValuesVariablesArray,
										  &fMinResultInterval, &fMaxResultInterval);
		delete[] fValuesVariablesArray;

		precision = paceval_fConvertFloatToString(strcRestult, fResult);
	}

	ctime = GetCurrentTime() - ctime;
	if (ctime == 0)
		ctime = ctime + 1;
	LabelCalculationTime->Caption = "<" + String(ctime) + "ms";

	if (paceval_GetIsError(handle_pacevalComputation))
	{
		int errType;
		char errOperator[25];
		long errPosition;
		int maxMessageDetailsLength;
		char* errMessage;
		char* errDetails;

		errType = paceval_GetErrorInformation(handle_pacevalComputation,
											  errOperator, &errPosition);
		RichEditFunction->SelStart = errPosition;
		RichEditFunction->SelLength = 1;
		RichEditFunction->SetFocus();

		maxMessageDetailsLength = paceval_CreateErrorInformationText(handle_pacevalComputation,
								  NULL, NULL);
		errMessage = new char[2 * maxMessageDetailsLength];
		errDetails = new char[maxMessageDetailsLength];

		maxMessageDetailsLength = paceval_CreateErrorInformationText(handle_pacevalComputation,
								  errMessage, errDetails);
		strcat(errMessage, "\r\n");
		strcat(errMessage, errDetails);

		MessageBox(Handle, errMessage, "Error in computation", MB_ICONERROR);

		delete[] errMessage;
		delete[] errDetails;

		return;
	}

	EditResult->Text = strcRestult;

	if (RadioButtonTINCOn->Checked)
	{
		if (RadioButtonLongDouble->Checked)
		{
			precision = paceval_ldConvertFloatToString(strcRestult, ldMinResultInterval);
			EditMinResultTINC->Text = strcRestult;

			precision = paceval_ldConvertFloatToString(strcRestult, ldMaxResultInterval);
			EditMaxResultTINC->Text = strcRestult;
		}
		else if (RadioButtonDouble->Checked)
		{
			precision = paceval_dConvertFloatToString(strcRestult, dMinResultInterval);
			EditMinResultTINC->Text = strcRestult;

			precision = paceval_dConvertFloatToString(strcRestult, dMaxResultInterval);
			EditMaxResultTINC->Text = strcRestult;
		}
		else if (RadioButtonFloat->Checked)
		{
			precision = paceval_fConvertFloatToString(strcRestult, fMinResultInterval);
			EditMinResultTINC->Text = strcRestult;

			precision = paceval_fConvertFloatToString(strcRestult, fMaxResultInterval);
			EditMaxResultTINC->Text = strcRestult;
		}
	}
}

void __fastcall TpacevalFormMainCalculation::ButtonCreateCalculateClick(
	TObject *Sender)
{
	RichEditInformation->Lines->Clear();

	if (CBEnableLogging->Checked)
	{
		DoFormUpdate();

		AddToLogFile(false);
	}

	if (handle_pacevalComputation == NULL)
	{
		doCreate_pacevalCalculation();

		if (paceval_GetIsError(handle_pacevalComputation) == false)
		{
			ButtonCreateCalculate->Caption = "Calculate - computation object is created";
		}
	}

	if (handle_pacevalComputation != NULL)
	{
		int errType;
		char errOperator[25];
		long errPosition;
		unsigned long lengthXML;
		char* bufferXML;

		errType = paceval_GetErrorInformation(handle_pacevalComputation,
											  errOperator, &errPosition);

		if ((paceval_GetIsError(handle_pacevalComputation) == false) ||
				((errType >= PACEVAL_ERR_COMPUTATION_BEGIN) && (errType <= PACEVAL_ERR_COMPUTATION_END)))
		{
			doCalculate_pacevalCalculation();
		}

		lengthXML = paceval_GetComputationInformationXML(handle_pacevalComputation,
					NULL);
		bufferXML = new char[lengthXML];
		lengthXML = paceval_GetComputationInformationXML(handle_pacevalComputation,
					bufferXML);
		RichEditInformation->Text = bufferXML;
		delete[] bufferXML;
	}

	if (CBEnableLogging->Checked)
	{
		AddToLogFile(true);
	}
}
//---------------------------------------------------------------------------


void __fastcall TpacevalFormMainCalculation::FormCreate(TObject *Sender)
{
	//Initialize the 'paceval_win32.dll'
	if (paceval_InitializeLibrary(NULL) == true)
		paceval_available =  true;
	else
		paceval_available =  false;
}
//---------------------------------------------------------------------------

void __fastcall TpacevalFormMainCalculation::FormDestroy(TObject *Sender)
{
	if (handle_pacevalComputation)
	{
		//Delete the paceval-Computation object
		paceval_DeleteComputation(handle_pacevalComputation);
	}

	if (paceval_available == true)
	{
		//Free the 'paceval_win32.dll'
		paceval_FreeLibrary();
	}
}
//---------------------------------------------------------------------------

void __fastcall TpacevalFormMainCalculation::LabelInfoPacevalClick(TObject *Sender)
{
	AnsiString mailPaceval = "mailto:info@paceval.com&subject=paceval-Demonstrator&body=...";

	ShellExecute(this->Handle, "open", mailPaceval.c_str(), NULL, NULL, SW_SHOW);
}
//---------------------------------------------------------------------------

unsigned long TpacevalFormMainCalculation::CreateXMLData(char** buffer_dataXML)
{
	unsigned long dataXMLsize;
	AnsiString stringUserFunction;
	int numberOfVariables;
	bool useInterval;
	AnsiString stringVariablesForCalculation;
	AnsiString stringValuesForCalculation;

	stringUserFunction = RichEditFunction->Text;
	numberOfVariables = StringGridVariables->RowCount - 1;

	if (RadioButtonTINCOn->Checked)
	{
		useInterval = true;
	}
	else
	{
		useInterval = false;
	}

	stringVariablesForCalculation = "";
	for (unsigned long iCount = 0; iCount < (unsigned long)numberOfVariables; iCount++)
	{
		if (iCount > 0)
		{
			stringVariablesForCalculation = stringVariablesForCalculation + " ";
		}
		stringVariablesForCalculation = stringVariablesForCalculation + StringGridVariables->Rows[iCount + 1]->Strings[0];
	}

	stringValuesForCalculation = "";
	for (unsigned long iCount = 0; iCount < (unsigned long)numberOfVariables; iCount++)
	{
		if (iCount > 0)
		{
			stringValuesForCalculation = stringValuesForCalculation + ";";
		}
		stringValuesForCalculation = stringValuesForCalculation + StringGridVariables->Rows[iCount + 1]->Strings[1];
	}

	dataXMLsize = paceval_CreateXMLFromParameters(NULL,
				  stringUserFunction.c_str(),
				  numberOfVariables,
				  stringVariablesForCalculation.c_str(),
				  stringValuesForCalculation.c_str(),
				  useInterval);

	*buffer_dataXML = new char[dataXMLsize];

	dataXMLsize = paceval_CreateXMLFromParameters(*buffer_dataXML,
				  stringUserFunction.c_str(),
				  numberOfVariables,
				  stringVariablesForCalculation.c_str(),
				  stringValuesForCalculation.c_str(),
				  useInterval);

	return dataXMLsize;
}

void TpacevalFormMainCalculation::SaveToFile(const char* buffer_dataXML, unsigned long dataXMLsize)
{
	TFileName nameOfFile;
	TFileStream *FStream;

	if(SaveDialogPaceval->Execute())
	{
		nameOfFile = SaveDialogPaceval->FileName;
		if (nameOfFile.Length() > 3)
		{
			if (nameOfFile[nameOfFile.Length()-3] != '.')
				nameOfFile = nameOfFile + ".xpv";
		}
		else
		{
			nameOfFile = nameOfFile + ".xpv";
		}

		FStream = new TFileStream(nameOfFile, fmCreate);
		FStream->Write(buffer_dataXML, dataXMLsize);

		delete FStream;
	}
}

void TpacevalFormMainCalculation::AddToLogFile(bool logEnd)
{
	TFileName nameOfFile;
	TFileStream *FStream;
	AnsiString logLine;

	nameOfFile = "paceval-Calculation.log";

	if (logEnd == true)
	{
		if (FileExists(nameOfFile))
		{
			FStream = new TFileStream(nameOfFile, fmOpenWrite);
		}
		else
			return;
	}
	else
	{
		FStream = new TFileStream(nameOfFile, fmCreate);
	}

	if (logEnd == false)
	{
		char* buffer_dataXML;
		unsigned long dataXMLsize;

		dataXMLsize = CreateXMLData(&buffer_dataXML);
		FStream->Seek(0, soFromEnd);

		logLine = AnsiString("\r\n") + LabelVersionString->Caption + "\r\n";
		FStream->Write(logLine.c_str(), logLine.Length());
		FStream->Write(buffer_dataXML, dataXMLsize);

		logLine = AnsiString("\r\n") + AnsiString(GetCurrentTime()) + ": Start*";
		FStream->Write(logLine.c_str(), logLine.Length());

		delete[] buffer_dataXML;
	}
	else if (logEnd == true)
	{
		logLine = AnsiString("\r\n") + AnsiString(GetCurrentTime()) + ": End\r\n";
		FStream->Seek(-1, soFromEnd); //overwrite the marker *
		FStream->Write(logLine.c_str(), logLine.Length());
	}

	delete FStream;
}

void __fastcall TpacevalFormMainCalculation::ButtonSaveClick(
	TObject *Sender)
{
	char* buffer_dataXML;
	unsigned long dataXMLsize;

	dataXMLsize = CreateXMLData(&buffer_dataXML);
	SaveToFile(buffer_dataXML, dataXMLsize);

	delete[] buffer_dataXML;
}
//---------------------------------------------------------------------------

void __fastcall TpacevalFormMainCalculation::LabelLinkPacevalClick(TObject *Sender)
{
	AnsiString webPaceval = "http://www.paceval.com";

	ShellExecute(this->Handle, "open", webPaceval.c_str(), NULL, NULL, SW_SHOW);
}
//---------------------------------------------------------------------------

bool TpacevalFormMainCalculation::OpenFilename(const char* fileName)
{
	if (strlen(fileName) > 0)
	{
		TFileStream *FStream;
		TFileName nameOfFile(fileName);
		char* buffer_dataXML;
		unsigned long functionStringLength;
		unsigned long variablesStringLength;
		unsigned long valuesStringLength;
		unsigned long numberOfVariables;
		bool useInterval;
		bool successOpenFile = true;

		FStream = new TFileStream(nameOfFile,
								  fmOpenRead | fmShareExclusive);
		buffer_dataXML = new char[FStream->Size + 1];

		FStream->Read(buffer_dataXML, FStream->Size);
		buffer_dataXML[FStream->Size] = '\0';

		if (paceval_ReadParametersFromXML(buffer_dataXML, &functionStringLength,
										  &variablesStringLength, &numberOfVariables, &valuesStringLength,
										  NULL, NULL, NULL, &useInterval) == 0)
		{
			char* functionString;
			char* variablesString;
			char* valuesString;

			functionString = NULL;
			variablesString = NULL;
			valuesString = NULL;

			if (functionStringLength > 0)
			{
				functionString = new char[functionStringLength];
			}
			if (variablesStringLength > 0)
			{
				variablesString = new char[variablesStringLength];
			}
			if (valuesStringLength > 0)
			{
				valuesString = new char[valuesStringLength];
			}

			if (paceval_ReadParametersFromXML(buffer_dataXML, &functionStringLength,
											  &variablesStringLength, &numberOfVariables, &valuesStringLength,
											  functionString, variablesString, valuesString, &useInterval) == 0)
			{
				unsigned long iCount;
				char* strDelimeterPos;

				RichEditFunction->Text = functionString;
				if (useInterval == true)
					RadioButtonTINCOn->Checked = true;
				else
					RadioButtonTINCOff->Checked = true;

				ResetVariablesAndValuesGrid();

				for (unsigned long iCount = 0; iCount < numberOfVariables; iCount++)
				{
					strDelimeterPos = strstr(variablesString, " ");
					if (strDelimeterPos != NULL)
					{
						strDelimeterPos[0] = '\0';
					}
					StringGridVariables->Rows[iCount + 1]->Strings[0] = variablesString;
					if (strDelimeterPos != NULL)
					{
						strcpy(variablesString, &strDelimeterPos[1]);
					}
				}

				for (unsigned long iCount = 0; iCount < numberOfVariables; iCount++)
				{
					strDelimeterPos = strstr(valuesString, ";");
					if (strDelimeterPos != NULL)
					{
						strDelimeterPos[0] = '\0';
					}
					StringGridVariables->Rows[iCount + 1]->Strings[1] = valuesString;
					if (strDelimeterPos != NULL)
					{
						strcpy(valuesString, &strDelimeterPos[1]);
					}
				}
			}
			else
			{
				successOpenFile = false;
			}

			if (functionString != NULL)
			{
				delete[] functionString;
			}
			if (variablesString != NULL)
			{
				delete[] variablesString;
			}
			if (valuesString != NULL)
			{
				delete[] valuesString;
			}
		}
		else
		{
			successOpenFile = false;
		}

		delete FStream;
		delete[] buffer_dataXML;

		return successOpenFile;
	}
	else
	{
		return false;
	}
}

void __fastcall TpacevalFormMainCalculation::ButtonOpenClick(TObject *Sender)
{
	TFileName nameOfFile;
	TFileStream *FStream;
	AnsiString filenameToOpen;

	if (OpenDialogPaceval->Execute())
	{
		filenameToOpen = OpenDialogPaceval->FileName;

		if (OpenFilename(filenameToOpen.c_str()) == false)
		{
			MessageBox(Handle, "This is not a file in the correct format.", "File open", MB_ICONERROR);
		}
	}
}
//---------------------------------------------------------------------------

void __fastcall TpacevalFormMainCalculation::RadioButtonTINCOnClick(
	TObject *Sender)
{
	RadioButtonTINCOff->Checked = !RadioButtonTINCOn->Checked;
	if (RadioButtonTINCOn->Checked)
	{
		LabelMinResultTINC->Font->Color = clWindowText;
		LabelMaxResultTINC->Font->Color = clWindowText;
		EditMinResultTINC->Font->Color = clWindowText;
		EditMaxResultTINC->Font->Color = clWindowText;

		EditResult->Text = "no result, please, press \"Create object for computation and calculate\"";
		EditMinResultTINC->Text = "no result, please, press \"Create object for computation and calculate\"";
		EditMaxResultTINC->Text = "no result, please, press \"Create object for computation and calculate\"";

		DataChangedForCalculation();
	}
}
//---------------------------------------------------------------------------

void __fastcall TpacevalFormMainCalculation::RadioButtonTINCOffClick(
	TObject *Sender)
{
	RadioButtonTINCOn->Checked = !RadioButtonTINCOff->Checked;
	if (RadioButtonTINCOff->Checked)
	{
		LabelMinResultTINC->Font->Color = clGrayText;
		LabelMaxResultTINC->Font->Color = clGrayText;
		EditMinResultTINC->Font->Color = clGrayText;
		EditMaxResultTINC->Font->Color = clGrayText;

		EditResult->Text = "no result, please, press \"Create object for computation and calculate\"";
		EditMinResultTINC->Text = "use Interval \"off\"";
		EditMaxResultTINC->Text = "use Interval \"off\"";

		DataChangedForCalculation();
	}
}
//---------------------------------------------------------------------------

void __fastcall TpacevalFormMainCalculation::SelectAll1Click(
	TObject *Sender)
{
	RichEditFunction->SelectAll();
}
//---------------------------------------------------------------------------

void __fastcall TpacevalFormMainCalculation::Copy1Click(TObject *Sender)
{
	RichEditFunction->CopyToClipboard();
}
//---------------------------------------------------------------------------

void __fastcall TpacevalFormMainCalculation::Paste1Click(TObject *Sender)
{
	RichEditFunction->PasteFromClipboard();
}
//---------------------------------------------------------------------------

void __fastcall TpacevalFormMainCalculation::StringGridVariablesSelectCell(
	TObject *Sender, int ACol, int ARow, bool &CanSelect)
{
	if (ARow > 0)
	{
		BitBtnDrawForVariable->Caption = "Graph for selected variable '"
										 + StringGridVariables->Rows[ARow]->Strings[0] + "'";
		selectedVariableRow = ARow;
	}
	else
	{
		BitBtnDrawForVariable->Caption = "Graph for variable '<not selected>'";
		selectedVariableRow = -1;
	}
}
//---------------------------------------------------------------------------


void __fastcall TpacevalFormMainCalculation::RichEditFunctionSelectionChange(
	TObject *Sender)
{
	LabelPosition->Caption = RichEditFunction->SelStart;
}
//---------------------------------------------------------------------------

void __fastcall TpacevalFormMainCalculation::StringGridVariablesSetEditText(
	TObject *Sender, int ACol, int ARow, const AnsiString Value)
{
	if (ACol == 0)
	{
		bool CanSelect = true;

		DataChangedForCalculation();
		StringGridVariablesSelectCell(Sender, ACol, ARow, CanSelect);
	}
}
//---------------------------------------------------------------------------

void __fastcall TpacevalFormMainCalculation::ButtonHelpClick(
	TObject *Sender)
{
	AnsiString webPaceval = "http://www.paceval.com/how-to-use-demo-calculation";

	ShellExecute(this->Handle, "open", webPaceval.c_str(), NULL, NULL, SW_SHOW);
}
//---------------------------------------------------------------------------

void __fastcall TpacevalFormMainCalculation::LabelLinkSpecificationClick(
	TObject *Sender)
{
	AnsiString webPaceval = "http://www.paceval.com/product-brief";

	ShellExecute(this->Handle, "open", webPaceval.c_str(), NULL, NULL, SW_SHOW);
}
//---------------------------------------------------------------------------

void TpacevalFormMainCalculation::ResetVariablesAndValuesGrid()
{
	for (unsigned long iCount = 7; iCount < (unsigned long)StringGridVariables->RowCount; iCount++)
	{
		StringGridVariables->Rows[iCount]->Strings[0] = "variable" + AnsiString(iCount);
		StringGridVariables->Rows[iCount]->Strings[1] = "0.0";
	}
}

void __fastcall TpacevalFormMainCalculation::FormShow(TObject *Sender)
{
	PACEVAL_HANDLE handle_pacevalVersionComputation;
	char* pacevalVersionString;
	float pacevalVersionNumber;
	bool success = false;
	int errType;

	if (paceval_available == false)
	{
		Close();
		return;
	}

	if (sizeof(long double) == sizeof(double))
	{
		char charBuffer500[500];

		CreateErrorMessage(charBuffer500, PACEVAL_ERR_COMPUTATION_USER_COMPILER_NOT_SUPPORTS_LONG_DOUBLE, 500);

		if (paceval_fmathv(NULL, &errType, "paceval_LibrarySupportsLongDouble", 0, "", NULL) != 0)
			strcat(charBuffer500, "\n\nYour paceval. library supports long double.");
		else
			strcat(charBuffer500, "\n\nYour paceval. library not supports long double.");

		strcat(charBuffer500, "\n\nE.g. Embarcadero 64-bit Windows does not support long double.");
		strcat(charBuffer500, "\nExcerpt from 'Embarcadero 64-bit Windows Data Types Compared to 32-bit Windows Data Types' :");
		strcat(charBuffer500, "\n'On Intel 64-bit Windows, the Extended type is an alias for a Double, or 8 bytes.'");

		MessageBox(Handle, charBuffer500, "Information - long double", MB_ICONINFORMATION);

		RadioButtonLongDouble->Checked = false;
		RadioButtonLongDouble->Enabled = false;
		RadioButtonDouble->Checked = true;
		RadioButtonFloat->Checked = false;
	}

	RichEditIntroduction->Text = "This demo application shows the capabilities of paceval. in terms of its computational excellence. Please, examine its calculation power and speed for a formula without limitations in length and number of variables and use standard mathematical notations.\r";
	RichEditIntroduction->Text = RichEditIntroduction->Text
								 + "In addition, it demonstrates how precise and reliable paceval. works. The trusted interval computation \"TINC\" shows an interval within the true results can be found. And, finally, you can draw the function for a selected variable.";

	handle_pacevalVersionComputation = NULL;

	success = paceval_SetCallbackUserFunction(1, "my_function1",
			  paceval_callbackUserFunction1);
	success = paceval_SetCallbackUserFunction(2, "my_function2",
			  paceval_callbackUserFunction1);
	success = paceval_SetCallbackUserFunction(3, "my_function3",
			  paceval_callbackUserFunction1);

	pacevalVersionNumber = paceval_fmathv(&handle_pacevalVersionComputation, &errType,
										  "paceval_VersionNumber", 0, "");

	pacevalVersionString = new char[PACEVAL_MAXVER];
	if (handle_pacevalVersionComputation != NULL)
	{
		this->Caption = this->Caption + " with paceval. Version "
						+ paceval_mainVersionString + "." + paceval_subVersionString;

		paceval_GetComputationVersionString(handle_pacevalVersionComputation,
											pacevalVersionString);
		paceval_DeleteComputation(handle_pacevalVersionComputation);
	}
	else
	{
		strcpy(pacevalVersionString, "[Error in detecting version.]");
	}
	LabelVersionString->Caption = pacevalVersionString;
	delete[] pacevalVersionString;

	RichEditFunction->Lines->Clear();
	RichEditFunction->Text = AnsiString("0");
	RichEditInformation->Lines->Clear();

	StringGridVariables->Rows[0]->Strings[0] = "name";
	StringGridVariables->Rows[0]->Strings[1] = "value";

	StringGridVariables->Rows[1]->Strings[0] = "x";
	StringGridVariables->Rows[2]->Strings[0] = "y";
	StringGridVariables->Rows[3]->Strings[0] = "z";
	StringGridVariables->Rows[4]->Strings[0] = "u";
	StringGridVariables->Rows[5]->Strings[0] = "v";
	StringGridVariables->Rows[6]->Strings[0] = "w";

	StringGridVariables->Rows[1]->Strings[1] = "0.0";
	StringGridVariables->Rows[2]->Strings[1] = "0.0";
	StringGridVariables->Rows[3]->Strings[1] = "0.0";
	StringGridVariables->Rows[4]->Strings[1] = "0.0";
	StringGridVariables->Rows[5]->Strings[1] = "0.0";
	StringGridVariables->Rows[6]->Strings[1] = "0.0";

	ResetVariablesAndValuesGrid();

	BitBtnDrawForVariable->Caption = "Graph for selected variable \""
									 + StringGridVariables->Rows[1]->Strings[0] + "\"";

	if (parameterStartStr != "")
	{
		OpenFilename(parameterStartStr.c_str());
	}

	CBEnableLoggingClick(NULL);
	HandleLogFile();
}
//---------------------------------------------------------------------------

void TpacevalFormMainCalculation::HandleLogFile()
{
	TFileName nameOfFile("paceval-Calculation.log");

	if (FileExists(nameOfFile))
	{
		TFileStream *FStream;
		char* buffer_dataLog;
		AnsiString stringBuffer_dataLog;

		FStream = new TFileStream(nameOfFile,
								  fmOpenRead | fmShareExclusive);
		buffer_dataLog = new char[FStream->Size + 1];

		FStream->Read(buffer_dataLog, FStream->Size);
		buffer_dataLog[FStream->Size] = '\0';

		if (FStream->Size > (long)strlen("Start*"))
		{
			AnsiString stringCheckLastLog;

			stringCheckLastLog = &buffer_dataLog[FStream->Size - strlen("Start*")];

			delete FStream;
			FStream = NULL;

			if (stringCheckLastLog == "Start*")
			{
				int posMaskQuestion;

				MessageBox(Handle, defineLogMessageText,
						   AnsiString(pacevalFormMainCalculation->Caption).c_str(),
						   MB_ICONINFORMATION);

				char stringTempDirectry[MAX_PATH + 1];
				AnsiString filenameToCopy;
				AnsiString filenameToAttach;

				GetTempPath(MAX_PATH, stringTempDirectry);
				filenameToCopy = AnsiString(GetCurrentDir()) + "\\" + nameOfFile;
				filenameToAttach = AnsiString(stringTempDirectry) + nameOfFile;

				TMemoryStream* mem = new TMemoryStream();

				mem->LoadFromFile(filenameToCopy);
				mem->SaveToFile(filenameToAttach);

				delete mem;

				bool (*paceval_SendMail)(char* recipient_in, char* subjectText,
										 char* bodyText, char* linkAttachment);
				HINSTANCE handle_pacevalAddOn_DLL = LoadLibrary("paceval_addon.dll");

				paceval_SendMail = (bool(*)(char *, char *, char *, char *))
								   GetProcAddress(handle_pacevalAddOn_DLL, "@paceval_SendMail$qpct1t1t1");

				if (paceval_SendMail("info@paceval.com",
									 AnsiString((pacevalFormMainCalculation->Caption) + " issue").c_str(),
									 "Hi paceval. team, \r\n\r\nI have experienced an issue. Please, find my logging data attached and send me a response about your investigation. \r\n\r\nKind regards, a friendly user",
									 filenameToAttach.c_str()) == false)
				{
					ShellExecute(0, "open", "notepad.exe", filenameToAttach.c_str(), 0, SW_SHOW);

					MessageBox(Handle, "You mail program cannot be started. Maybe you run this program as an administrator and your mail program in a different context, i.e. not as an administrator.\r\nPlease, copy the text of the log and send it to info@paceval.com.",
							   AnsiString(pacevalFormMainCalculation->Caption).c_str(),
							   MB_ICONINFORMATION);
				}
				FreeLibrary(handle_pacevalAddOn_DLL);
			}
		}

		if (FStream != NULL)
			delete FStream;
		delete[] buffer_dataLog;

		DeleteFile(nameOfFile);
	}
}

void __fastcall TpacevalFormMainCalculation::CBEnableLoggingClick(
	TObject *Sender)
{
//
}
//---------------------------------------------------------------------------

void __fastcall TpacevalFormMainCalculation::PageControlMainChanging(
	TObject *Sender, bool &AllowChange)
{
	int errType;

	LabelThreadsUsages->Caption = String((long)(paceval_dmathv(NULL, &errType,
										 "paceval_NumberThreadUsages", 0, "", NULL)));

	LabelSystemCores->Caption = String((long)(paceval_dmathv(NULL, &errType,
									   "paceval_NumberOfCores", 0, "", NULL)));
}
//---------------------------------------------------------------------------


void __fastcall TpacevalFormMainCalculation::RadioButtonLongDoubleClick(
	TObject *Sender)
{
	DataChangedForCalculation();

	precisionType = PACEVAL_CALCULATION_PRECISION_LONG_DOUBLE;

	RadioButtonDouble->Checked = !RadioButtonLongDouble->Checked;
	RadioButtonFloat->Checked = !RadioButtonLongDouble->Checked;
	EditResultPrecision->Text = "long double";
	EditMinResultTINCPrecision->Text = "long double";
	EditMaxResultTINCPrecision->Text = "long double";
}
//---------------------------------------------------------------------------

void __fastcall TpacevalFormMainCalculation::RadioButtonDoubleClick(
	TObject *Sender)
{
	DataChangedForCalculation();

	precisionType = PACEVAL_CALCULATION_PRECISION_DOUBLE;

	RadioButtonLongDouble->Checked = !RadioButtonDouble->Checked;
	RadioButtonFloat->Checked = !RadioButtonDouble->Checked;
	EditResultPrecision->Text = "double";
	EditMinResultTINCPrecision->Text = "double";
	EditMaxResultTINCPrecision->Text = "double";
}
//---------------------------------------------------------------------------

void __fastcall TpacevalFormMainCalculation::RadioButtonFloatClick(
	TObject *Sender)
{
	DataChangedForCalculation();

	precisionType = PACEVAL_CALCULATION_PRECISION_FLOAT;

	RadioButtonLongDouble->Checked = !RadioButtonFloat->Checked;
	RadioButtonDouble->Checked = !RadioButtonFloat->Checked;
	EditResultPrecision->Text = "float";
	EditMinResultTINCPrecision->Text = "float";
	EditMaxResultTINCPrecision->Text = "float";
}
//---------------------------------------------------------------------------

void __fastcall TpacevalFormMainCalculation::BitBtnDrawForVariableClick(
	TObject *Sender)
{
	bool useInterval;
	int errType;

	if (selectedVariableRow == -1)
	{
		MessageBox(Handle, "No variable for graph selected",
				   "Graph for selected variable", MB_ICONINFORMATION);

		return;
	}

	if (RadioButtonTINCOn->Checked)
	{
		useInterval = true;
	}
	else
	{
		useInterval = false;
	}

	if (handle_pacevalComputation == NULL)
	{
		MessageBox(Handle, AnsiString(AnsiString("No object for computation is created. \r\nPlease, press \"")
									  + ButtonCreateCalculate->Caption + "\" first.").c_str(),
				   "Graph for selected variable", MB_ICONINFORMATION);

		return;
	}

	errType = paceval_GetErrorInformation(handle_pacevalComputation, NULL, NULL);

	//We cannot calculate and draw in case of errors
	if ((errType < PACEVAL_ERR_ANALYSIS_BEGIN) || (errType > PACEVAL_ERR_ANALYSIS_END))
	{
		FormGraphForVariable->SetPacevalComputationObject(handle_pacevalComputation,
				StringGridVariables, selectedVariableRow, useInterval, precisionType);
		FormGraphForVariable->Caption = BitBtnDrawForVariable->Caption;
		FormGraphForVariable->ShowModal();
	}
}
//---------------------------------------------------------------------------



void __fastcall TpacevalFormMainCalculation::RichEditInformationChange(
	TObject *Sender)
{
	int currentPos = 0;
	int startPos = 0;
	int endPos = 0;
	TSearchTypes searchType;

	searchType << stMatchCase;
	currentPos = RichEditInformation->SelStart;

	startPos = RichEditInformation->FindTextA("<", startPos,
			   RichEditInformation->Text.Length(), searchType);
	while (startPos > -1)
	{
		endPos = RichEditInformation->FindTextA(">", startPos,
												RichEditInformation->Text.Length(), searchType);

		RichEditInformation->SelStart = startPos;
		RichEditInformation->SelLength = endPos - startPos + 1;
		RichEditInformation->SelAttributes->Style = TFontStyles() << fsBold;

		startPos = RichEditInformation->FindTextA("<", endPos,
				   RichEditInformation->Text.Length(), searchType);
	}

	startPos = RichEditInformation->FindTextA("<function50Characters>", 0,
			   RichEditInformation->Text.Length(), searchType);
	endPos = RichEditInformation->FindTextA("</function50Characters>", 0,
											RichEditInformation->Text.Length(), searchType);
	if ((startPos > -1) && (endPos > -1))
	{
		startPos = startPos + strlen("<function50Characters>");;
		RichEditInformation->SelStart = startPos;
		RichEditInformation->SelLength = endPos - startPos;
		RichEditInformation->SelAttributes->Style = TFontStyles() >> fsBold;
	}
}
//---------------------------------------------------------------------------

const char* CreateErrorMessage(char* messageBuffer, int pacevalErrorType, int lengthBuffer)
{
	int maxMessageDetailsLength;
	char* errMessage;

	maxMessageDetailsLength = paceval_GetErrorTypeMessage(pacevalErrorType,
							  NULL);
	errMessage = new char[maxMessageDetailsLength];
	maxMessageDetailsLength = paceval_GetErrorTypeMessage(pacevalErrorType,
							  errMessage);

	strncpy(messageBuffer, errMessage, lengthBuffer - 1);
	messageBuffer[lengthBuffer - 1] = '\0';
	delete[] errMessage;

	return messageBuffer;
}

