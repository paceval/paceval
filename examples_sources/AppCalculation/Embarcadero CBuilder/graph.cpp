//---------------------------------------------------------------------------
// Author(s) : paceval®, http://www.paceval.com
// File      : paceval-calculation graph.cpp
//---------------------------------------------------------------------------

#include <vcl.h>
#pragma hdrstop

#include "..\system-independent\source_public\inc\paceval_main.h" //We include the paceval header

#include <Grids.hpp>

#if (__BORLANDC__)
#else
#include <Vcl.Controls.hpp>
#endif //#if (__BORLANDC__)

#include "graph.h"

#include <math.h>
#include <stdlib.h>

//---------------------------------------------------------------------------
#pragma package(smart_init)
#pragma resource "*.dfm"
TFormGraphForVariable *FormGraphForVariable;
//---------------------------------------------------------------------------

__fastcall TFormGraphForVariable::TFormGraphForVariable(TComponent* Owner)
    : TForm(Owner)
{
    drawAreaMinX = -10;
    drawAreaMaxX = 10;
    drawAreaMinFX = -10;
    drawAreaMaxFX = 10;

    handle_pacevalComputation = NULL;
    StringGridVariables = NULL;

    ldResults = NULL;
    dResults = NULL;
    fResults = NULL;

    ldMinResultIntervals = NULL;
    dMinResultIntervals = NULL;
    fMinResultIntervals = NULL;

    ldMaxResultIntervals = NULL;
    dMaxResultIntervals = NULL;
    fMaxResultIntervals = NULL;

    errorTypes = NULL;
}
//---------------------------------------------------------------------------

void __fastcall TFormGraphForVariable::ButtonExitClick(TObject *Sender)
{
    Close();
}
//---------------------------------------------------------------------------

void TFormGraphForVariable::SetPacevalComputationObject(PACEVAL_HANDLE handle_pacevalComputation_in,
        TStringGrid* StringGridVariables_in, long selectedVariableRow_in,
        bool useInterval_in, paceval_eCalculationPrecisionTypes precisionType_in)
{
    handle_pacevalComputation = handle_pacevalComputation_in;
    StringGridVariables = StringGridVariables_in;
    selectedVariableRow = selectedVariableRow_in;
    useInterval = useInterval_in;
    precisionType = precisionType_in;
}

void TFormGraphForVariable::DoTransformation(long double theXvalue_in, long double theFXvalue_in,
        long double *theTransXvalue, long double *theTransFXvalue, bool inverseTransformation)
{
    long double scalarX;
    long double scalarFX;

    scalarX = PaintBoxArea->Width / (drawAreaMaxX - drawAreaMinX);
    scalarFX = PaintBoxArea->Height / (drawAreaMaxFX - drawAreaMinFX);

    if (inverseTransformation == false)
    {
        *theTransXvalue = (theXvalue_in - drawAreaMinX) * scalarX;
        *theTransFXvalue = PaintBoxArea->Height - (theFXvalue_in - drawAreaMinFX) * scalarFX;
    }
    else
    {
        *theTransXvalue = (theXvalue_in + drawAreaMinX * scalarX) / scalarX;
        *theTransFXvalue = (long double)(PaintBoxArea->Height)/scalarFX - theFXvalue_in/scalarFX + drawAreaMinFX;
    }
}


void __fastcall TFormGraphForVariable::ButtonUpClick(TObject *Sender)
{
    long double moveBy;

    moveBy = (drawAreaMaxFX - drawAreaMinFX) * 0.1;
    drawAreaMinFX = drawAreaMinFX + moveBy;
    drawAreaMaxFX = drawAreaMaxFX + moveBy;
    UpdateInformation();
    PaintBoxArea->Invalidate();
}
//---------------------------------------------------------------------------

void __fastcall TFormGraphForVariable::ButtonDownClick(TObject *Sender)
{
    long double moveBy;

    moveBy = (drawAreaMaxFX - drawAreaMinFX) * 0.1;
    drawAreaMinFX = drawAreaMinFX - moveBy;
    drawAreaMaxFX = drawAreaMaxFX - moveBy;
    UpdateInformation();
    PaintBoxArea->Invalidate();
}
//---------------------------------------------------------------------------

void __fastcall TFormGraphForVariable::ButtonLeftClick(TObject *Sender)
{
    long double moveBy;

    moveBy = (drawAreaMaxX - drawAreaMinX) * 0.1;
    drawAreaMinX = drawAreaMinX - moveBy;
    drawAreaMaxX = drawAreaMaxX - moveBy;
    UpdateInformation();
    PaintBoxArea->Invalidate();
}
//---------------------------------------------------------------------------

void __fastcall TFormGraphForVariable::ButtonRightClick(TObject *Sender)
{
    long double moveBy;

    moveBy = (drawAreaMaxX - drawAreaMinX) * 0.1;
    drawAreaMinX = drawAreaMinX + moveBy;
    drawAreaMaxX = drawAreaMaxX + moveBy;
    UpdateInformation();
    PaintBoxArea->Invalidate();
}
//---------------------------------------------------------------------------

void TFormGraphForVariable::UpdateInformation()
{
    int precision;
    char strcRestult[100];

    switch (precisionType)
    {
    case PACEVAL_CALCULATION_PRECISION_LONG_DOUBLE:
    {
        precision = paceval_ldConvertFloatToString(strcRestult, drawAreaMinX);
        EditMinX->Text = strcRestult;

        precision = paceval_ldConvertFloatToString(strcRestult, drawAreaMaxX);
        EditMaxX->Text = strcRestult;

        precision = paceval_ldConvertFloatToString(strcRestult, drawAreaMinFX);
        EditMinFX->Text = strcRestult;

        precision = paceval_ldConvertFloatToString(strcRestult, drawAreaMaxFX);
        EditMaxFX->Text = strcRestult;
    }
    break;
    case PACEVAL_CALCULATION_PRECISION_DOUBLE:
    {
        precision = paceval_dConvertFloatToString(strcRestult, drawAreaMinX);
        EditMinX->Text = strcRestult;

        precision = paceval_dConvertFloatToString(strcRestult, drawAreaMaxX);
        EditMaxX->Text = strcRestult;

        precision = paceval_dConvertFloatToString(strcRestult, drawAreaMinFX);
        EditMinFX->Text = strcRestult;

        precision = paceval_dConvertFloatToString(strcRestult, drawAreaMaxFX);
        EditMaxFX->Text = strcRestult;
    }
    break;
    case PACEVAL_CALCULATION_PRECISION_FLOAT:
    {
        precision = paceval_fConvertFloatToString(strcRestult, drawAreaMinX);
        EditMinX->Text = strcRestult;

        precision = paceval_fConvertFloatToString(strcRestult, drawAreaMaxX);
        EditMaxX->Text = strcRestult;

        precision = paceval_fConvertFloatToString(strcRestult, drawAreaMinFX);
        EditMinFX->Text = strcRestult;

        precision = paceval_fConvertFloatToString(strcRestult, drawAreaMaxFX);
        EditMaxFX->Text = strcRestult;
    }
    }
}

void __fastcall TFormGraphForVariable::ButtonZoomInClick(TObject *Sender)
{
	long double zoomByX;

	zoomByX = (drawAreaMaxX - drawAreaMinX) * 0.25;
	drawAreaMinX = drawAreaMinX - zoomByX;
	drawAreaMaxX = drawAreaMaxX + zoomByX;
	drawAreaMinFX = drawAreaMinFX - zoomByX;
	drawAreaMaxFX = drawAreaMaxFX + zoomByX;
	UpdateInformation();
	PaintBoxArea->Invalidate();
}
//---------------------------------------------------------------------------

void __fastcall TFormGraphForVariable::ButtonZoomOutClick(TObject *Sender)
{
	long double zoomByX;

	zoomByX = (drawAreaMaxX - drawAreaMinX) * 1/6;
	drawAreaMinX = drawAreaMinX + zoomByX;
	drawAreaMaxX = drawAreaMaxX - zoomByX;
	drawAreaMinFX = drawAreaMinFX + zoomByX;
	drawAreaMaxFX = drawAreaMaxFX - zoomByX;
	UpdateInformation();
	PaintBoxArea->Invalidate();
}
//---------------------------------------------------------------------------

void __fastcall TFormGraphForVariable::PaintBoxAreaMouseMove(
	TObject *Sender, TShiftState Shift, int X, int Y)
{
	TimerPaintBoxAreaMouse->Enabled = true;
}
//---------------------------------------------------------------------------




void __fastcall TFormGraphForVariable::FormShow(TObject *Sender)
{
	int errType;

	EditHorizontal->Text = "";
	EditVertical->Text = "";
	EditResult->Text = "";
	EditMaxResultTINC->Text = "";
	EditMinResultTINC->Text = "";
	LabelErrorMessage->Caption = "";

	switch (precisionType)
	{
	case PACEVAL_CALCULATION_PRECISION_LONG_DOUBLE:
	{
		EditPaintBoxAreaPrecision->Text = "long double";
		EditHorizontalPrecision->Text = "long double";
		EditVerticalPrecision->Text = "long double";
		EditResultPrecision->Text = "long double";
		EditMinResultTINCPrecision->Text = "long double";
		EditMaxResultTINCPrecision->Text = "long double";
		EditDrawAreaPrecision->Text = "long double";
	}
	break;
	case PACEVAL_CALCULATION_PRECISION_DOUBLE:
	{
		EditPaintBoxAreaPrecision->Text = "double";
		EditHorizontalPrecision->Text = "double";
		EditVerticalPrecision->Text = "double";
		EditResultPrecision->Text = "double";
		EditMinResultTINCPrecision->Text = "double";
		EditMaxResultTINCPrecision->Text = "double";
		EditDrawAreaPrecision->Text = "double";
	}
	break;
	case PACEVAL_CALCULATION_PRECISION_FLOAT:
	{
		EditPaintBoxAreaPrecision->Text = "float";
		EditHorizontalPrecision->Text = "float";
		EditVerticalPrecision->Text = "float";
		EditResultPrecision->Text = "float";
		EditMinResultTINCPrecision->Text = "float";
		EditMaxResultTINCPrecision->Text = "float";
		EditDrawAreaPrecision->Text = "float";
	}
	}

	if (!useInterval)
	{
		LabelStatusTINC->Caption = "off";
		LabelStatusTINC->Font->Color = clGrayText;
	}
	else
	{
		LabelStatusTINC->Caption = "on";
		LabelStatusTINC->Font->Color = clWindowText;
	}

	LabelThreadsUsages->Caption = String((long)(paceval_dmathv(NULL, &errType,
										 "paceval_NumberThreadUsages", 0, "", NULL)));
}
//---------------------------------------------------------------------------

void __fastcall TFormGraphForVariable::CheckBoxTINCClick(TObject *Sender)
{
	if (!useInterval)
	{
		LabelStatusTINC->Caption = "off";
		LabelStatusTINC->Font->Color = clGrayText;
	}
	else
	{
		LabelStatusTINC->Caption = "on";
		LabelStatusTINC->Font->Color = clWindowText;
	}
}
//---------------------------------------------------------------------------

void __fastcall TFormGraphForVariable::TimerPaintBoxAreaRefreshTimer(
	TObject *Sender)
{
	long double theXValue;
	long double theFXValue;
	long double transferXValue;
	long double transferFXValue;
	long double scalarX;
	long double ldResult;
	double dResult;
	float fResult;
	long double minResultInterval;
	long double maxResultInterval;
	long double* ldValuesVariablesArray;
	double* dValuesVariablesArray;
	float* fValuesVariablesArray;
	long double* ldValuesVariablesArrayExt;
	double* dValuesVariablesArrayExt;
	float* fValuesVariablesArrayExt;
	char* endptr;
	bool hasError = false;
	TRect drawErrorRect;
	int lastDrawX_Result;
	int lastDrawFX_Result;
	bool lastDraw_ResultValid;
	int lastDrawX_minResult;
	int lastDrawFX_minResult;
	int lastDrawX_maxResult;
	int lastDrawFX_maxResult;
	bool lastDraw_minResultValid;
	bool lastDraw_maxResultValid;
	TColor oldBrushColor;
	int numberOfVariables;
	AnsiString stringValueVariable;
	long ctime;
	int errType;

	TimerPaintBoxAreaRefresh->Enabled = false;
	LabelCalculationTime->Caption = "0ms";

	TPaintBox *thePBPlot = PaintBoxArea;

	scalarX = thePBPlot->Width / (drawAreaMaxX - drawAreaMinX);

	numberOfVariables = StringGridVariables->RowCount - 1;

	switch (precisionType)
	{
	case PACEVAL_CALCULATION_PRECISION_LONG_DOUBLE:
	{
		ldValuesVariablesArray = new long double[numberOfVariables];
	}
	break;
	case PACEVAL_CALCULATION_PRECISION_DOUBLE:
	{
		dValuesVariablesArray = new double[numberOfVariables];
	}
	break;
	case PACEVAL_CALCULATION_PRECISION_FLOAT:
	{
		fValuesVariablesArray = new float[numberOfVariables];
	}
	}

	for (unsigned long iCount = 0; iCount < (unsigned long)numberOfVariables; iCount++)
	{
		int errType;

		stringValueVariable = StringGridVariables->Rows[iCount + 1]->Strings[1];

		switch (precisionType)
		{
		case PACEVAL_CALCULATION_PRECISION_LONG_DOUBLE:
		{
			ldValuesVariablesArray[iCount] =
				paceval_ldConvertStringToFloat(stringValueVariable.c_str(),
											   &errType, NULL, false, NULL, NULL);
		}
		break;
		case PACEVAL_CALCULATION_PRECISION_DOUBLE:
		{
			dValuesVariablesArray[iCount] =
				paceval_dConvertStringToFloat(stringValueVariable.c_str(),
											  &errType, NULL, false, NULL, NULL);
		}
		break;
		case PACEVAL_CALCULATION_PRECISION_FLOAT:
		{
			fValuesVariablesArray[iCount] =
				paceval_fConvertStringToFloat(stringValueVariable.c_str(),
											  &errType, NULL, false, NULL, NULL);
		}
		}

		if (errType != PACEVAL_ERR_NO_ERROR)
			hasError = true;
	}

	if (hasError == true)
	{
		return;
	}

	oldBrushColor = thePBPlot->Canvas->Brush->Color;
	thePBPlot->Canvas->Brush->Color = clRed;
	thePBPlot->Canvas->Pen->Style = psSolid;

	switch (precisionType)
	{
	case PACEVAL_CALCULATION_PRECISION_LONG_DOUBLE:
	{
		ldValuesVariablesArrayExt = new long double[(thePBPlot->Width + 1) * numberOfVariables];
	}
	break;
	case PACEVAL_CALCULATION_PRECISION_DOUBLE:
	{
		dValuesVariablesArrayExt = new double[(thePBPlot->Width + 1) * numberOfVariables];
	}
	break;
	case PACEVAL_CALCULATION_PRECISION_FLOAT:
	{
		fValuesVariablesArrayExt = new float[(thePBPlot->Width + 1) * numberOfVariables];
	}
	}

	for (long iCount = 0; iCount <= thePBPlot->Width; iCount++)
	{
		for (long jCount = 0; jCount < numberOfVariables; jCount++)
		{
			if (jCount == selectedVariableRow - 1)
			{
				switch (precisionType)
				{
				case PACEVAL_CALCULATION_PRECISION_LONG_DOUBLE:
				{
					ldValuesVariablesArrayExt[iCount * numberOfVariables + jCount] = drawAreaMinX + iCount * 1 / scalarX;
				}
				break;
				case PACEVAL_CALCULATION_PRECISION_DOUBLE:
				{
					dValuesVariablesArrayExt[iCount * numberOfVariables + jCount] = drawAreaMinX + iCount * 1 / scalarX;
				}
				break;
				case PACEVAL_CALCULATION_PRECISION_FLOAT:
				{
					fValuesVariablesArrayExt[iCount * numberOfVariables + jCount] = drawAreaMinX + iCount * 1 / scalarX;
				}
				}
			}
			else
			{
				switch (precisionType)
				{
				case PACEVAL_CALCULATION_PRECISION_LONG_DOUBLE:
				{
					ldValuesVariablesArrayExt[iCount * numberOfVariables + jCount] = ldValuesVariablesArray[jCount];
				}
				break;
				case PACEVAL_CALCULATION_PRECISION_DOUBLE:
				{
					dValuesVariablesArrayExt[iCount * numberOfVariables + jCount] = dValuesVariablesArray[jCount];
				}
				break;
				case PACEVAL_CALCULATION_PRECISION_FLOAT:
				{
					fValuesVariablesArrayExt[iCount * numberOfVariables + jCount] = fValuesVariablesArray[jCount];
				}
				}
			}
		}
	}

	if (errorTypes != NULL)
		delete[] errorTypes;
	errorTypes = new int[(thePBPlot->Width + 1)];

	ctime = GetCurrentTime();

	switch (precisionType)
	{
	case PACEVAL_CALCULATION_PRECISION_LONG_DOUBLE:
	{
		if (ldResults != NULL)
			delete[] ldResults;
		if (ldMinResultIntervals != NULL)
			delete[] ldMinResultIntervals;
		if (ldMaxResultIntervals != NULL)
			delete[] ldMaxResultIntervals;

		ldResults = new long double[(thePBPlot->Width + 1)];
		ldMinResultIntervals = new long double[(thePBPlot->Width + 1)];
		ldMaxResultIntervals = new long double[(thePBPlot->Width + 1)];
		hasError = paceval_ldGetComputationResultExt(handle_pacevalComputation,
				   ldValuesVariablesArrayExt,
				   thePBPlot->Width,
				   &ldResults[0],
				   &ldMinResultIntervals[0],
				   &ldMaxResultIntervals[0],
				   &errorTypes[0]);
	}
	break;
	case PACEVAL_CALCULATION_PRECISION_DOUBLE:
	{
		if (dResults != NULL)
			delete[] dResults;
		if (dMinResultIntervals != NULL)
			delete[] dMinResultIntervals;
		if (dMaxResultIntervals != NULL)
			delete[] dMaxResultIntervals;

		dResults = new double[(thePBPlot->Width + 1)];
		dMinResultIntervals = new double[(thePBPlot->Width + 1)];
		dMaxResultIntervals = new double[(thePBPlot->Width + 1)];
		hasError = paceval_dGetComputationResultExt(handle_pacevalComputation,
				   dValuesVariablesArrayExt,
				   thePBPlot->Width,
				   &dResults[0],
				   &dMinResultIntervals[0],
				   &dMaxResultIntervals[0],
				   &errorTypes[0]);
	}
	break;
	case PACEVAL_CALCULATION_PRECISION_FLOAT:
	{
		if (fResults != NULL)
			delete[] fResults;
		if (fMinResultIntervals != NULL)
			delete[] fMinResultIntervals;
		if (fMaxResultIntervals != NULL)
			delete[] fMaxResultIntervals;

		fResults = new float[(thePBPlot->Width + 1)];
		fMinResultIntervals = new float[(thePBPlot->Width + 1)];
		fMaxResultIntervals = new float[(thePBPlot->Width + 1)];
		hasError = paceval_fGetComputationResultExt(handle_pacevalComputation,
				   fValuesVariablesArrayExt,
				   thePBPlot->Width,
				   &fResults[0],
				   &fMinResultIntervals[0],
				   &fMaxResultIntervals[0],
				   &errorTypes[0]);
	}
	}

	ctime = GetCurrentTime() - ctime + 1;

	if (useInterval)
	{
		lastDraw_minResultValid = false;
		lastDraw_maxResultValid = false;
		for (unsigned long iCount = 0; iCount < (unsigned long)thePBPlot->Width; iCount++)
		{
			switch (precisionType)
			{
			case PACEVAL_CALCULATION_PRECISION_LONG_DOUBLE:
			{
				ldValuesVariablesArray[selectedVariableRow - 1] = drawAreaMinX + iCount * 1 / scalarX;
			}
			break;
			case PACEVAL_CALCULATION_PRECISION_DOUBLE:
			{
				dValuesVariablesArray[selectedVariableRow - 1] = drawAreaMinX + iCount * 1 / scalarX;
			}
			break;
			case PACEVAL_CALCULATION_PRECISION_FLOAT:
			{
				fValuesVariablesArray[selectedVariableRow - 1] = drawAreaMinX + iCount * 1 / scalarX;
			}
			}

			if (errorTypes[iCount] != PACEVAL_ERR_NO_ERROR)
			{
				drawErrorRect = TRect(iCount, thePBPlot->Height - 2,
									  iCount + 1, thePBPlot->Height);
				thePBPlot->Canvas->FillRect(drawErrorRect);

				lastDraw_minResultValid = false;
				lastDraw_maxResultValid = false;
			}
			else
			{
				switch (precisionType)
				{
				case PACEVAL_CALCULATION_PRECISION_LONG_DOUBLE:
				{
					ldResult = ldResults[iCount];
					minResultInterval = ldMinResultIntervals[iCount];
					maxResultInterval = ldMaxResultIntervals[iCount];
					DoTransformation(ldValuesVariablesArray[selectedVariableRow - 1], minResultInterval,
									 &transferXValue, &transferFXValue, false);
				}
				break;
				case PACEVAL_CALCULATION_PRECISION_DOUBLE:
				{
					dResult = dResults[iCount];
					minResultInterval = dMinResultIntervals[iCount];
					maxResultInterval = dMaxResultIntervals[iCount];
					DoTransformation(dValuesVariablesArray[selectedVariableRow - 1], minResultInterval,
									 &transferXValue, &transferFXValue, false);
				}
				break;
				case PACEVAL_CALCULATION_PRECISION_FLOAT:
				{
					fResult = fResults[iCount];
					minResultInterval = fMinResultIntervals[iCount];
					maxResultInterval = fMaxResultIntervals[iCount];
					DoTransformation(fValuesVariablesArray[selectedVariableRow - 1], minResultInterval,
									 &transferXValue, &transferFXValue, false);
				}
				}

				transferFXValue = ceill(transferFXValue);
				if (lastDraw_minResultValid == true)
				{
					thePBPlot->Canvas->Pen->Color = TColor(0x006FB7FF);
					thePBPlot->Canvas->MoveTo(lastDrawX_minResult, lastDrawFX_minResult);
					if (transferFXValue < 0)
						transferFXValue = -1;
					if (transferFXValue > thePBPlot->Height)
						transferFXValue = thePBPlot->Height;
					transferFXValue = ceill(transferFXValue);
					if (fabsl(lastDrawFX_minResult - transferFXValue) >= thePBPlot->Height)
						thePBPlot->Canvas->MoveTo(iCount, transferFXValue);
					else
						thePBPlot->Canvas->LineTo(iCount, transferFXValue);
				}
				lastDrawX_minResult = iCount;
				if (transferFXValue < -10000)
					lastDrawFX_minResult = -10000;
				else if (transferFXValue > 10000)
					lastDrawFX_minResult = 10000;
				else
					lastDrawFX_minResult = transferFXValue;

				switch (precisionType)
				{
				case PACEVAL_CALCULATION_PRECISION_LONG_DOUBLE:
				{
					DoTransformation(ldValuesVariablesArray[selectedVariableRow - 1], maxResultInterval,
									 &transferXValue, &transferFXValue, false);
				}
				break;
				case PACEVAL_CALCULATION_PRECISION_DOUBLE:
				{
					DoTransformation(dValuesVariablesArray[selectedVariableRow - 1], maxResultInterval,
									 &transferXValue, &transferFXValue, false);
				}
				break;
				case PACEVAL_CALCULATION_PRECISION_FLOAT:
				{
					DoTransformation(fValuesVariablesArray[selectedVariableRow - 1], maxResultInterval,
									 &transferXValue, &transferFXValue, false);
				}
				}

				transferFXValue = floorl(transferFXValue);
				if (lastDraw_maxResultValid == true)
				{
					thePBPlot->Canvas->Pen->Color = TColor(0x006FB7FF);
					thePBPlot->Canvas->MoveTo(lastDrawX_maxResult, lastDrawFX_maxResult);
					if (transferFXValue < 0)
						transferFXValue = -1;
					if (transferFXValue > thePBPlot->Height)
						transferFXValue = thePBPlot->Height;
					transferFXValue = floorl(transferFXValue);
					if (fabsl(lastDrawFX_maxResult - transferFXValue) >= thePBPlot->Height)
						thePBPlot->Canvas->MoveTo(iCount, transferFXValue);
					else
					{
						thePBPlot->Canvas->LineTo(iCount, transferFXValue);
						thePBPlot->Canvas->LineTo(iCount, lastDrawFX_minResult);
					}
				}
				lastDrawX_maxResult = iCount;
				if (transferFXValue < -10000)
					lastDrawFX_maxResult = -10000;
				else if (transferFXValue > 10000)
					lastDrawFX_maxResult = 10000;
				else
					lastDrawFX_maxResult = transferFXValue;
				lastDraw_maxResultValid = true;
			}
		}
	}

	thePBPlot->Canvas->Brush->Color = oldBrushColor;
	thePBPlot->Canvas->Pen->Color = clMaroon;
	thePBPlot->Canvas->Pen->Style = psDot;
	DoTransformation(drawAreaMinX, 0,
					 &transferXValue, &transferFXValue, false);
	thePBPlot->Canvas->MoveTo(transferXValue, transferFXValue);

	DoTransformation(drawAreaMaxX, 0,
					 &transferXValue, &transferFXValue, false);
	thePBPlot->Canvas->LineTo(transferXValue, transferFXValue);

	DoTransformation(0, drawAreaMinFX,
					 &transferXValue, &transferFXValue, false);
	thePBPlot->Canvas->MoveTo(transferXValue, transferFXValue);

	DoTransformation(0, drawAreaMaxFX,
					 &transferXValue, &transferFXValue, false);
	thePBPlot->Canvas->LineTo(transferXValue, transferFXValue);

	oldBrushColor = thePBPlot->Canvas->Brush->Color;
	thePBPlot->Canvas->Brush->Color = clRed;
	thePBPlot->Canvas->Pen->Style = psSolid;
	lastDraw_ResultValid = false;

	for (unsigned long iCount = 0; iCount < (unsigned long)thePBPlot->Width; iCount++)
	{
		switch (precisionType)
		{
		case PACEVAL_CALCULATION_PRECISION_LONG_DOUBLE:
		{
			ldValuesVariablesArray[selectedVariableRow - 1] = drawAreaMinX + iCount * 1 / scalarX;
			ldResult = ldResults[iCount];
		}
		break;
		case PACEVAL_CALCULATION_PRECISION_DOUBLE:
		{
			dValuesVariablesArray[selectedVariableRow - 1] = drawAreaMinX + iCount * 1 / scalarX;
			dResult = dResults[iCount];
		}
		break;
		case PACEVAL_CALCULATION_PRECISION_FLOAT:
		{
			fValuesVariablesArray[selectedVariableRow - 1] = drawAreaMinX + iCount * 1 / scalarX;
			fResult = fResults[iCount];
		}
		}

		if (errorTypes[iCount] != PACEVAL_ERR_NO_ERROR)
		{
			drawErrorRect = TRect(iCount, thePBPlot->Height - 2,
								  iCount + 1, thePBPlot->Height);
			thePBPlot->Canvas->FillRect(drawErrorRect);

			lastDraw_ResultValid = false;
		}
		else
		{
			switch (precisionType)
			{
			case PACEVAL_CALCULATION_PRECISION_LONG_DOUBLE:
			{
				DoTransformation(ldValuesVariablesArray[selectedVariableRow - 1], ldResult,
								 &transferXValue, &transferFXValue, false);
			}
			break;
			case PACEVAL_CALCULATION_PRECISION_DOUBLE:
			{
				DoTransformation(dValuesVariablesArray[selectedVariableRow - 1], dResult,
								 &transferXValue, &transferFXValue, false);
			}
			break;
			case PACEVAL_CALCULATION_PRECISION_FLOAT:
			{
				DoTransformation(fValuesVariablesArray[selectedVariableRow - 1], fResult,
								 &transferXValue, &transferFXValue, false);
			}
			}

			if (lastDraw_ResultValid == true)
			{
				thePBPlot->Canvas->Pen->Color = clBlack;
				thePBPlot->Canvas->MoveTo(lastDrawX_Result, lastDrawFX_Result);
				if (transferFXValue < 0)
					transferFXValue = -1;
				if (transferFXValue > thePBPlot->Height)
					transferFXValue = thePBPlot->Height;
				if (fabsl(lastDrawFX_Result - transferFXValue) >= thePBPlot->Height)
					thePBPlot->Canvas->MoveTo(iCount, transferFXValue);
				else
					thePBPlot->Canvas->LineTo(iCount, transferFXValue);
			}
			lastDrawX_Result = iCount;
			if (transferFXValue < -10000)
				lastDrawFX_Result = -10000;
			else if (transferFXValue > 10000)
				lastDrawFX_Result = 10000;
			else
				lastDrawFX_Result = transferFXValue;
			lastDraw_ResultValid = true;
		}
	}

	switch (precisionType)
	{
	case PACEVAL_CALCULATION_PRECISION_LONG_DOUBLE:
	{
		delete[] ldValuesVariablesArray;
		delete[] ldValuesVariablesArrayExt;
	}
	break;
	case PACEVAL_CALCULATION_PRECISION_DOUBLE:
	{
		delete[] dValuesVariablesArray;
		delete[] dValuesVariablesArrayExt;
	}
	break;
	case PACEVAL_CALCULATION_PRECISION_FLOAT:
	{
		delete[] fValuesVariablesArray;
		delete[] fValuesVariablesArrayExt;
	}
	}

	LabelCalculationTime->Caption = "<" + String(ctime) + "ms";

	LabelThreadsUsages->Caption = String((long)(paceval_dmathv(NULL, &errType,
										 "paceval_NumberThreadUsages", 0, "", NULL)));
}
//---------------------------------------------------------------------------


void __fastcall TFormGraphForVariable::PaintBoxAreaPaint(TObject *Sender)
{
	TimerPaintBoxAreaRefresh->Enabled = false;
	TimerPaintBoxAreaRefresh->Enabled = true;

	LabelCalculationTime->Caption = "updating";
}
//---------------------------------------------------------------------------

void __fastcall TFormGraphForVariable::TimerPaintBoxAreaMouseTimer(
	TObject *Sender)
{
	int precision;
	char strcRestult[100];
	long double ldResult;
	double dResult;
	float fResult;
	long double ldMinResultInterval;
	long double ldMaxResultInterval;
	double dMinResultInterval;
	double dMaxResultInterval;
	float fMinResultInterval;
	float fMaxResultInterval;

	TimerPaintBoxAreaMouse->Enabled = false;

	TPoint pointMousePos = Mouse->CursorPos;
	TPoint pointRelPaintBox = PaintBoxArea->ScreenToClient(pointMousePos);
	int xPosition = (int)pointRelPaintBox.x - 1;
	int yPosition = (int)pointRelPaintBox.y - 1;

	if ((xPosition > 0) && (xPosition < PaintBoxArea->Width)
			&& (yPosition > 0)&& (yPosition < PaintBoxArea->Height))
	{
		long double transferXValue;
		long double transferFXValue;

		DoTransformation(xPosition, yPosition,
						 &transferXValue, &transferFXValue, true);

		switch (precisionType)
		{
		case PACEVAL_CALCULATION_PRECISION_LONG_DOUBLE:
		{
			precision = paceval_ldConvertFloatToString(strcRestult, transferXValue);
			EditHorizontal->Text = strcRestult;

			precision = paceval_ldConvertFloatToString(strcRestult, transferFXValue);
			EditVertical->Text = strcRestult;
		}
		break;
		case PACEVAL_CALCULATION_PRECISION_DOUBLE:
		{
			precision = paceval_dConvertFloatToString(strcRestult, transferXValue);
			EditHorizontal->Text = strcRestult;

			precision = paceval_dConvertFloatToString(strcRestult, transferFXValue);
			EditVertical->Text = strcRestult;
		}
		break;
		case PACEVAL_CALCULATION_PRECISION_FLOAT:
		{
			precision = paceval_fConvertFloatToString(strcRestult, transferXValue);
			EditHorizontal->Text = strcRestult;

			precision = paceval_fConvertFloatToString(strcRestult, transferFXValue);
			EditVertical->Text = strcRestult;
		}
		}

		if (errorTypes[xPosition] != PACEVAL_ERR_NO_ERROR)
		{
			int maxMessageDetailsLength;
			char* errMessage;

			EditResult->Font->Color = clRed;
			EditResult->Text = "error - see text";
			if (useInterval)
			{
				EditMinResultTINC->Font->Color = clRed;
				EditMinResultTINC->Text = "error - see text";
				EditMaxResultTINC->Font->Color = clRed;
				EditMaxResultTINC->Text = "error - see text";
			}

			maxMessageDetailsLength = paceval_GetErrorTypeMessage(errorTypes[xPosition],
									  NULL);
			errMessage = new char[maxMessageDetailsLength];

			maxMessageDetailsLength = paceval_GetErrorTypeMessage(errorTypes[xPosition],
									  errMessage);
			LabelErrorMessage->Caption = errMessage;
			delete[] errMessage;
		}
		else
		{
			LabelErrorMessage->Caption = "";
			EditResult->Font->Color = clWindowText;
			EditMinResultTINC->Font->Color = clWindowText;
			EditMaxResultTINC->Font->Color = clWindowText;

			switch (precisionType)
			{
			case PACEVAL_CALCULATION_PRECISION_LONG_DOUBLE:
			{
				precision = paceval_ldConvertFloatToString(strcRestult, ldResults[xPosition]);
				EditResult->Text = strcRestult;

				if (useInterval)
				{
					precision = paceval_ldConvertFloatToString(strcRestult, ldMinResultIntervals[xPosition]);
					EditMinResultTINC->Text = strcRestult;

					precision = paceval_ldConvertFloatToString(strcRestult, ldMaxResultIntervals[xPosition]);
					EditMaxResultTINC->Text = strcRestult;
				}
			}
			break;
			case PACEVAL_CALCULATION_PRECISION_DOUBLE:
			{
				precision = paceval_dConvertFloatToString(strcRestult, dResults[xPosition]);
				EditResult->Text = strcRestult;

				if (useInterval)
				{
					precision = paceval_dConvertFloatToString(strcRestult, dMinResultIntervals[xPosition]);
					EditMinResultTINC->Text = strcRestult;

					precision = paceval_dConvertFloatToString(strcRestult, dMaxResultIntervals[xPosition]);
					EditMaxResultTINC->Text = strcRestult;
				}
			}
			break;
			case PACEVAL_CALCULATION_PRECISION_FLOAT:
			{
				precision = paceval_fConvertFloatToString(strcRestult, fResults[xPosition]);
				EditResult->Text = strcRestult;

				if (useInterval)
				{
					precision = paceval_fConvertFloatToString(strcRestult, fMinResultIntervals[xPosition]);
					EditMinResultTINC->Text = strcRestult;

					precision = paceval_fConvertFloatToString(strcRestult, fMaxResultIntervals[xPosition]);
					EditMaxResultTINC->Text = strcRestult;
				}
			}
			}
		}
	}
	else
	{
		EditHorizontal->Text = "none";
		EditResult->Text = "none";
	}
}
//---------------------------------------------------------------------------

void __fastcall TFormGraphForVariable::FormDestroy(TObject *Sender)
{
	if (ldResults != NULL)
		delete[] ldResults;
	if (dResults != NULL)
		delete[] dResults;
	if (fResults != NULL)
		delete[] fResults;

	if (ldMinResultIntervals != NULL)
		delete[] ldMinResultIntervals;
	if (dMinResultIntervals != NULL)
		delete[] dMinResultIntervals;
	if (fMinResultIntervals != NULL)
		delete[] fMinResultIntervals;

	if (ldMaxResultIntervals != NULL)
		delete[] ldMaxResultIntervals;
	if (dMaxResultIntervals != NULL)
		delete[] dMaxResultIntervals;
	if (fMaxResultIntervals != NULL)
		delete[] fMaxResultIntervals;

	if (errorTypes != NULL)
		delete[] errorTypes;
}
//---------------------------------------------------------------------------


