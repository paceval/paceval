//---------------------------------------------------------------------------
// Copyright 1997-2014. Version 1.x Joerg Koenning - All rights reserved.
// Copyright 2015-2018. Version 2.x, 3.x, 4.x Joerg Koenning & Claudia Weidner
//                             - All rights reserved. (paceval®)
// Author(s) : Joerg Koenning & Claudia Weidner, http://www.paceval.com
// File      : paceval_addon.h
//---------------------------------------------------------------------------

//---------------------------------------------------------------------------
#ifndef paceval_addonH
#define paceval_addonH

bool _export paceval_SendMail(char* recipient_in, char* subjectText,
                              char* bodyText, char* linkAttachment);

//---------------------------------------------------------------------------
#endif //paceval_addonH
