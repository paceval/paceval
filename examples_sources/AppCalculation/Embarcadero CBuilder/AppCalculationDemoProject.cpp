//---------------------------------------------------------------------------

#include <vcl.h>
#include <windows.h>
#pragma hdrstop
USERES("AppCalculationDemoProject.res");
USEFORM("main.cpp", pacevalFormMainCalculation);
USEFORM("graph.cpp", FormGraphForVariable);
USEUNIT("..\system-independent\source_public\paceval_main.cpp");
//---------------------------------------------------------------------------
#if !defined(_WIN64)
WINAPI WinMain(HINSTANCE, HINSTANCE, LPSTR, int)
#else
int WINAPI _tWinMain(HINSTANCE, HINSTANCE, LPTSTR, int)
#endif
{
		try
		{
				 Application->Initialize();
				 Application->CreateForm(__classid(TpacevalFormMainCalculation), &pacevalFormMainCalculation);
				 Application->CreateForm(__classid(TFormGraphForVariable), &FormGraphForVariable);
				 Application->Run();
		}
		catch (Exception &exception)
		{
				 Application->ShowException(&exception);
		}
		return 0;
}
//---------------------------------------------------------------------------
