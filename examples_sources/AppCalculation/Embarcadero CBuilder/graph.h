//---------------------------------------------------------------------------
#ifndef graphH
#define graphH

#define PACEVAL_DEMO_USE_MAX_NUMBER_OF_VARIABLES   1000
//---------------------------------------------------------------------------
#include <Classes.hpp>
#include <Controls.hpp>
#include <StdCtrls.hpp>
#include <Forms.hpp>
#include <ExtCtrls.hpp>
//---------------------------------------------------------------------------

class TFormGraphForVariable : public TForm
{
__published:	// IDE-managed Components
    TPanel *PanelLeft;
    TPanel *PanelTop;
    TPanel *PanelBottomButtons;
    TPanel *PanelRight;
    TButton *ButtonExit;
    TPanel *PanelInfo;
    TPanel *PanelBottom;
    TButton *ButtonUp;
    TButton *ButtonDown;
    TButton *Button1;
    TButton *ButtonLeft;
    TButton *ButtonRight;
    TLabel *LabelZoom;
    TButton *ButtonZoomIn;
    TButton *ButtonZoomOut;
    TPanel *PanelPaintArea;
    TPaintBox *PaintBoxArea;
    TLabel *LabelDrawingSize;
    TEdit *EditMaxFX;
    TEdit *EditMinFX;
    TEdit *EditMinX;
    TEdit *EditMaxX;
    TGroupBox *GroupBoxMousePosition;
    TLabel *Label6;
    TLabel *LabelHintCalculationTime;
    TLabel *LabelCalculationTime;
    TEdit *EditPaintBoxAreaPrecision;
    TLabel *LabelHintThreadsUsages;
    TLabel *LabelThreadsUsages;
    TLabel *Label3;
    TLabel *Label4;
    TEdit *EditMaxResultTINC;
    TEdit *EditMinResultTINCPrecision;
    TEdit *EditMinResultTINC;
    TEdit *EditMaxResultTINCPrecision;
    TTimer *TimerPaintBoxAreaRefresh;
    TTimer *TimerPaintBoxAreaMouse;
    TLabel *Label1;
    TEdit *EditHorizontal;
    TEdit *EditHorizontalPrecision;
    TLabel *Label2;
    TEdit *EditResult;
    TEdit *EditResultPrecision;
    TLabel *Label5;
    TEdit *EditVertical;
    TEdit *EditVerticalPrecision;
    TEdit *EditDrawAreaPrecision;
    TLabel *LabelErrorMessage;
    TLabel *Label7;
    TLabel *LabelStatusTINC;
    void __fastcall ButtonExitClick(TObject *Sender);
    void __fastcall ButtonUpClick(TObject *Sender);
    void __fastcall ButtonDownClick(TObject *Sender);
    void __fastcall ButtonLeftClick(TObject *Sender);
    void __fastcall ButtonRightClick(TObject *Sender);
    void __fastcall ButtonZoomInClick(TObject *Sender);
    void __fastcall ButtonZoomOutClick(TObject *Sender);
    void __fastcall PaintBoxAreaMouseMove(TObject *Sender,
                                          TShiftState Shift, int X, int Y);
    void __fastcall FormShow(TObject *Sender);
    void __fastcall CheckBoxTINCClick(TObject *Sender);
    void __fastcall TimerPaintBoxAreaRefreshTimer(TObject *Sender);
    void __fastcall PaintBoxAreaPaint(TObject *Sender);
    void __fastcall TimerPaintBoxAreaMouseTimer(TObject *Sender);
    void __fastcall FormDestroy(TObject *Sender);

private:
    long double drawAreaMinX;
    long double drawAreaMaxX;
    long double drawAreaMinFX;
    long double drawAreaMaxFX;
    PACEVAL_HANDLE handle_pacevalComputation;
    TStringGrid* StringGridVariables;
    long selectedVariableRow;
    bool useInterval;
    paceval_eCalculationPrecisionTypes precisionType;

    long double* ldResults;
    double* dResults;
    float* fResults;
    long double* ldMinResultIntervals;
    double* dMinResultIntervals;
    float* fMinResultIntervals;
    long double* ldMaxResultIntervals;
    double* dMaxResultIntervals;
    float* fMaxResultIntervals;
    int* errorTypes;

    void UpdateInformation();
    void DoTransformation(long double theXvalue_in, long double theFXvalue_in,
                          long double *theTransXvalue, long double *theTransFXvalue, bool inverseTransformation);

public:
    __fastcall TFormGraphForVariable(TComponent* Owner);

    void SetPacevalComputationObject(PACEVAL_HANDLE handle_pacevalComputation_in,
                                     TStringGrid* StringGridVariables_in, long selectedVariableRow_in,
                                     bool useInterval_in, paceval_eCalculationPrecisionTypes precisionType_in);
};
//---------------------------------------------------------------------------
extern PACKAGE TFormGraphForVariable *FormGraphForVariable;
//---------------------------------------------------------------------------
#endif
