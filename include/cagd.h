/************************************************************************
* Copyright (C) 1996, by Dmitri Bassarab.				*
* Send bugs and/or frames to /dev/null or dima@cs.technion.ac.il	*
*************************************************************************/
#ifndef _CAGD_H_
#define _CAGD_H_

#include <math.h>
#include <windows.h>
#pragma warning(disable: 4136)
#include <gl/gl.h>
#include <gl/glu.h>
#include <gl/glaux.h>

typedef struct { /* 3D point */
  GLdouble x, y, z;
} CAGD_POINT;

enum { /* supported types of segment */
  CAGD_SEGMENT_UNUSED = 0,
  CAGD_SEGMENT_POINT,
  CAGD_SEGMENT_TEXT,
  CAGD_SEGMENT_POLYLINE
};

enum { /* events to register callback functions with */
  CAGD_LBUTTONDOWN = 0,
  CAGD_LBUTTONUP,
  CAGD_MBUTTONDOWN,
  CAGD_MBUTTONUP,
  CAGD_RBUTTONDOWN,
  CAGD_RBUTTONUP,
  CAGD_MOUSEMOVE,
  CAGD_TIMER,
  CAGD_MENU,
  CAGD_LOADFILE,
  CAGD_SAVEFILE,
  CAGD_LAST
};

typedef void (*CAGD_CALLBACK)(int, int, PVOID);
     
enum { /* id's of standard controls */
  CAGD_LOAD = WM_USER,
  CAGD_SAVE,
  CAGD_EXIT,
  CAGD_ORTHO,
  CAGD_PERSP,
  CAGD_CUE,
  CAGD_SENSLESS,
  CAGD_SENSMORE,
  CAGD_FUZZLESS,
  CAGD_FUZZMORE,
  CAGD_RESET, 
  CAGD_HELP,
  CAGD_USER /* use this one to create your own control */
};

#ifdef __cplusplus
extern "C" {
#endif
  
/************************************************************************
* General purpose functions						*
************************************************************************/
/************************************************************************
* DESCRIPTION:								M
*   This function creates drawable CAGD window and initializes all	M
*   internal data structures. It should be invoked PRIOR to any		M
*   cagd* call.								M
*									*
* PARAMETERS:								M
*   title 	text for window's caption;				M
*   width 	width of window in pixels (CW_DEFAULT can be used);	M
*   height	height of window in pixels (CW_DEFAULT can be used);	M
*									*
* RETURN VALUE:								M
*   None;								M
************************************************************************/
void cagdBegin(PCSTR title, int width, int height);
void cagdMainLoop();
void cagdRedraw();
/************************************************************************
* DESCRIPTION:								M
*   Use this function to retrive valid handle of CAGD window.		M
*									*
* PARAMETERS:								M
*   None;								M
*									*
* RETURN VALUE:								M
*   Handle of window;							M
************************************************************************/
HWND cagdGetWindow();
/************************************************************************
* DESCRIPTION:								M
*   Use this function to retrive valid handle of application instance.	M
*									*
* PARAMETERS:								M
*   None;								M
*									*
* RETURN VALUE:								M
*   Handle of instance;							M
************************************************************************/
HMODULE cagdGetModule();
/************************************************************************
* Menu and dialogs functions						*
************************************************************************/
/************************************************************************
* DESCRIPTION:								M
*   Append user defined menu to menu bar of window (before 'Help'). 	M
*									*
* PARAMETERS:								M
*   hMenu	handle of menu to append;				M
*   name 	title of menu;						M
*									*
* RETURN VALUE:								M
*   True if success;							M
************************************************************************/
BOOL cagdAppendMenu(HMENU hMenu, PCSTR name);
/************************************************************************
* DESCRIPTION:								M
*   Remove user defined menu from menu bar of window.		 	M
*									*
* PARAMETERS:								M
*   hMenu	handle of menu to remove;				M
*									*
* RETURN VALUE:								M
*   True if success;							M
************************************************************************/
BOOL cagdRemoveMenu(HMENU);
/************************************************************************
* DESCRIPTION:								M
*   Post user defined menu at some point of window.		 	M
*									*
* PARAMETERS:								M
*   hMenu	handle of menu to post;					M
*   x & y	where to post the menu (window's coordinates);		M
*									*
* RETURN VALUE:								M
*   ID of control that belongs to pop-up menu posted and 		M
************************************************************************/
WORD cagdPostMenu(HMENU hMenu, int x, int y);
void cagdSetHelpText(PCSTR);
BOOL cagdShowHelp();
/************************************************************************
* Geometric transformations and view functions				*
************************************************************************/
void cagdRotate(GLdouble, GLdouble, GLdouble, GLdouble);
void cagdTranslate(GLdouble, GLdouble, GLdouble);
void cagdScale(GLdouble, GLdouble, GLdouble);
void cagdReset();
WORD cagdGetView();
void cagdSetView(WORD);
BOOL cagdGetDepthCue();
void cagdSetDepthCue(BOOL enable);
BOOL cagdToObject(int, int, CAGD_POINT [2]);
BOOL cagdToWindow(CAGD_POINT *, int *, int *);
/************************************************************************
* General segment functions						*
************************************************************************/
void cagdSetColor(BYTE, BYTE, BYTE);
void cagdGetColor(BYTE *, BYTE *, BYTE *);
BOOL cagdSetSegmentColor(UINT, BYTE, BYTE, BYTE);
BOOL cagdGetSegmentColor(UINT, BYTE *, BYTE *, BYTE *);
BOOL cagdShowSegment(UINT);
BOOL cagdHideSegment(UINT);
BOOL cagdIsSegmentVisible(UINT);
BOOL cagdFreeSegment(UINT);
void cagdFreeAllSegments();
UINT cagdGetSegmentType(UINT);
UINT cagdGetSegmentLength(UINT);
BOOL cagdGetSegmentLocation(UINT, CAGD_POINT *);
void cagdPick(int, int);
UINT cagdPickNext();
/************************************************************************
* Point segment functions						*
************************************************************************/
UINT cagdAddPoint(const CAGD_POINT *);
BOOL cagdReusePoint(UINT, const CAGD_POINT *);

/************************************************************************
* Text segment functions						*
************************************************************************/
UINT cagdAddText(const CAGD_POINT *, PCSTR);
BOOL cagdReuseText(UINT, const CAGD_POINT *, PCSTR);
BOOL cagdGetText(UINT, PSTR);

/************************************************************************
* Polyline segment functions						*
***********************************************************************/
UINT cagdAddPolyline(const CAGD_POINT *, UINT);
BOOL cagdReusePolyline(UINT, const CAGD_POINT *, UINT);
BOOL cagdGetVertex(UINT, UINT, CAGD_POINT *);
BOOL cagdSetVertex(UINT, UINT, const CAGD_POINT *);
UINT cagdGetNearestVertex(UINT, int, int);

/************************************************************************
* Callback functions							*
************************************************************************/
BOOL cagdRegisterCallback(UINT, CAGD_CALLBACK, PVOID);

#ifdef __cplusplus
}
#endif

#endif
