//---------------------------------------------------------------------------
#ifndef mainH
#define mainH
//---------------------------------------------------------------------------
#include <Classes.hpp>
#include <Controls.hpp>
#include <StdCtrls.hpp>
#include <Forms.hpp>
#include <ExtCtrls.hpp>
#include <ComCtrls.hpp>
#include <Mask.hpp>
#include <jpeg.hpp>
#include <Dialogs.hpp>
#include <OleCtrls.hpp>
#include <vcfi.hpp>
#include <Menus.hpp>
#include <Grids.hpp>
#include <Graphics.hpp>
#include <Buttons.hpp>
//---------------------------------------------------------------------------

class TpacevalFormMainCalculation : public TForm
{
__published:
    TPanel *PMainLeft;
    TPanel *PanelMainRight;
    TPanel *PanelTop;
    TRichEdit *RichEditIntroduction;
    TPanel *PanelLeft;
    TPanel *PanelRight;
    TPageControl *PageControlMain;
    TTabSheet *TabSheetFunction;
    TPanel *PanelFuncLeft;
    TLabel *LabelFunction;
    TPanel *PanelFuncTop;
    TLabel *LabelPositionFunction;
    TLabel *LabelPosition;
    TPanel *PanelLengthFunction;
    TPanel *PanelFuncRight;
    TLabel *Label4;
    TStringGrid *StringGridVariables;
    TPanel *PanelFuncBottom;
    TLabel *LabelHintCalculationTime;
    TLabel *LabelCalculationTime;
    TLabel *LabelResult;
    TLabel *Label3;
    TEdit *EditResult;
    TPanel *Panel9;
    TRichEdit *RichEditFunction;
    TTabSheet *TabSheetInformation;
    TPanel *Panel2;
    TPanel *Panel6;
    TPanel *Panel7;
    TPanel *Panel8;
    TScrollBox *ScrollBox1;
    TImage *Image5;
    TImage *Image4;
    TImage *Image3;
    TSaveDialog *SaveDialogPaceval;
    TOpenDialog *OpenDialogPaceval;
    TPanel *PanelBottom;
    TButton *ButtonExit;
    TButton *ButtonOpen;
    TButton *ButtonSave;
    TImage *Image2;
    TPanel *Panel10;
    TLabel *LabelInfoPaceval;
    TLabel *LabelLinkPaceval;
    TPopupMenu *PopupMenuRichEdit;
    TMenuItem *Copy;
    TMenuItem *SelectAll1;
    TMenuItem *Paste1;
    TLabel *Label5;
    TLabel *Label6;
    TGroupBox *GBUseTINC;
    TRadioButton *RadioButtonTINCOff;
    TRadioButton *RadioButtonTINCOn;
    TLabel *LabelMinResultTINC;
    TLabel *LabelMaxResultTINC;
    TLabel *Label1;
    TLabel *Label2;
    TEdit *EditMinResultTINC;
    TEdit *EditMaxResultTINC;
    TRichEdit *MemoCSV;
    TButton *ButtonHelp;
    TLabel *LabelVersionString;
    TLabel *LabelLinkSpecification;
    TLabel *Label9;
    TImage *Image6;
    TImage *Image7;
    TLabel *Label8;
    TLabel *Label10;
    TLabel *LabelHintCreationTime;
    TLabel *LabelCreationTime;
    TLabel *LabelLengthFunction;
    TLabel *LabelLength;
    TLabel *Label11;
    TLabel *LabelStatus;
    TCheckBox *CBEnableLogging;
    TImage *Image1;
    TBitBtn *ButtonCreateCalculate;
    TLabel *LabelHintThreadsUsages;
    TLabel *LabelThreadsUsages;
    TLabel *Label12;
    TLabel *Label13;
    TLabel *LabelHintSystemCores;
    TLabel *LabelSystemCores;
    TLabel *LabelHintInformation;
    TRichEdit *RichEditInformation;
    TRadioButton *RadioButtonLongDouble;
    TRadioButton *RadioButtonDouble;
    TRadioButton *RadioButtonFloat;
    TLabel *LabelPrecision;
    TBitBtn *BitBtnDrawForVariable;
    TEdit *EditMinResultTINCPrecision;
    TEdit *EditMaxResultTINCPrecision;
    TEdit *EditResultPrecision;
    TLabel *Label7;
    TLabel *LabelNumberOfVariables;
    TLabel *Label14;
    TLabel *LabelHintCacheHits;
    TLabel *LabelCacheHits;
    void __fastcall ButtonExitClick(TObject *Sender);
    void __fastcall RichEditFunctionChange(TObject *Sender);
    void __fastcall FormCreate(TObject *Sender);
    void __fastcall FormDestroy(TObject *Sender);
    void __fastcall LabelInfoPacevalClick(TObject *Sender);
    void __fastcall LabelLinkPacevalClick(TObject *Sender);
    void __fastcall ButtonOpenClick(TObject *Sender);
    void __fastcall RadioButtonTINCOnClick(TObject *Sender);
    void __fastcall RadioButtonTINCOffClick(TObject *Sender);
    void __fastcall SelectAll1Click(TObject *Sender);
    void __fastcall Copy1Click(TObject *Sender);
    void __fastcall Paste1Click(TObject *Sender);
    void __fastcall StringGridVariablesSelectCell(TObject *Sender,
            int ACol, int ARow, bool &CanSelect);
    void __fastcall RichEditFunctionSelectionChange(TObject *Sender);
    void __fastcall StringGridVariablesSetEditText(TObject *Sender,
            int ACol, int ARow, const AnsiString Value);
    void __fastcall ButtonHelpClick(TObject *Sender);
    void __fastcall LabelLinkSpecificationClick(TObject *Sender);
    void __fastcall FormShow(TObject *Sender);
    void __fastcall ButtonCreateCalculateClick(TObject *Sender);
    void __fastcall ButtonSaveClick(TObject *Sender);
    void __fastcall CBEnableLoggingClick(TObject *Sender);
    void __fastcall PageControlMainChanging(TObject *Sender,
                                            bool &AllowChange);
    void __fastcall RadioButtonLongDoubleClick(TObject *Sender);
    void __fastcall RadioButtonDoubleClick(TObject *Sender);
    void __fastcall RadioButtonFloatClick(TObject *Sender);
    void __fastcall BitBtnDrawForVariableClick(TObject *Sender);
    void __fastcall RichEditInformationChange(TObject *Sender);

private:
    PACEVAL_HANDLE handle_pacevalComputation;
    long selectedVariableRow;
    AnsiString parameterStartStr;
    bool paceval_available;
    paceval_eCalculationPrecisionTypes precisionType;

    void __fastcall doCreate_pacevalCalculation();
    void __fastcall doCalculate_pacevalCalculation(bool creationHandled);
    bool OpenFilename(const char* fileName);
    void ResetVariablesAndValuesGrid();

    void DataChangedForCalculation();

    unsigned long CreateXMLData(char** buffer_dataXML);
    void SaveToFile(const char* buffer_dataXML, unsigned long dataXMLsize);
    void AddToLogFile(bool logEnd);
    void HandleLogFile();

public:
    __fastcall TpacevalFormMainCalculation(TComponent* Owner);

    bool Handle_pacevalCallbackStatus(const int paceval_eStatus, const int percentageDone);
    void DoFormUpdate();
};
//---------------------------------------------------------------------------
extern PACKAGE TpacevalFormMainCalculation *pacevalFormMainCalculation;
//---------------------------------------------------------------------------

#define defineLogMessageText "You experienced an issue in your last session. If you allow\
 we would like to make further investigations. Please,\
 send us the email we will open now containing details of the issue.\r\nYou will have, of\
 course, the chance to see and edit the mail before sending."

#endif
