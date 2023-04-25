/************************************************************************
* Copyright (C) 1996, by Dmitri Bassarab.				*
* Send bugs and/or frames to /dev/null or dima@cs.technion.ac.il	*
*************************************************************************/
#include "cagd.h"
#include "internal.h"

#define LOINT(x) ((int)(short)LOWORD(x))
#define HIINT(x) ((int)(short)HIWORD(x))

typedef struct {
  CAGD_CALLBACK callback;
  PVOID data;
} CALLBACK_ENTRY;

static PSTR helpText = NULL;
static PSTR defaultHelpText = 
  "<Ctrl> + Left mouse button -- rotate around X/Y axes;\n"
  "<Ctrl> + Right mouse button -- rotate around Z axe;\n"
  "<Shift> + Left mouse button -- translate along X/Y axes;\n"
  "<Shift> + Right mouse button -- translate along Z axe;\n"
  "<+> -- increase scale;\n"
  "<-> -- decrease scale;";

static CALLBACK_ENTRY list[CAGD_LAST] = { { NULL, NULL } };
static WORD state = 0;

static char fileName[0xffff];
static OPENFILENAME openFileName = {
  sizeof(OPENFILENAME),
  NULL,
  NULL,
  "All files (*.*)\0*.*\0\0",
  NULL,
  0,
  0,
  fileName,
  sizeof(fileName),
  NULL,
  0,
  NULL,
  NULL,
  OFN_HIDEREADONLY,
  0, 
  0,
  NULL,
  0,
  NULL
};

BOOL cagdRegisterCallback(UINT message, CAGD_CALLBACK function, PVOID data)
{
  if(message < CAGD_LAST){
    list[message].callback = function;
    list[message].data = data;
    if(message == CAGD_TIMER)
      if(function)
	SetTimer(auxGetHWND(), 0, 1, NULL);
      else
	KillTimer(auxGetHWND(), 0);
    return TRUE;
  }
  return FALSE;
}

static void callback(UINT message, int x, int y)
{
  if(!list[message].callback)
    return;
  list[message].callback(x, y, list[message].data);
}

/* BUGFIX: mplav@csd 17/12/96: CALLBACK modificator for proper linkage. */
/* Error appeared on WinNT 4.0: menu was not properly redrawn. */ 
static LRESULT CALLBACK command(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam)
{
  static int x, y;
  int id;
  WORD key;
  HMENU hMenu = GetMenu(hWnd);

  switch(message){
    
  case WM_COMMAND:
    switch(id = LOWORD(wParam)){
    case CAGD_LOAD:
      openFileName.hwndOwner = auxGetHWND();
      openFileName.lpstrTitle = "Load File";
      if(GetOpenFileName(&openFileName))
	callback(CAGD_LOADFILE, (int)openFileName.lpstrFile, 0);
      return 0;
    case CAGD_SAVE:
      openFileName.hwndOwner = auxGetHWND();
      openFileName.lpstrTitle = "Save File";
      //Bugfix Octavian + Avishai
      //if(GetOpenFileName(&openFileName))
      if(GetSaveFileName(&openFileName))
	callback(CAGD_SAVEFILE, (int)openFileName.lpstrFile, 0);
      return 0;
    case CAGD_EXIT:
      PostQuitMessage(0);
      KillTimer(hWnd, 0);
      return 0;
    case CAGD_ORTHO:
      cagdSetView(CAGD_ORTHO);
      cagdRedraw();
      return 0;
    case CAGD_PERSP:
      cagdSetView(CAGD_PERSP);
      cagdRedraw();
      return 0;
    case CAGD_CUE:
      cagdSetDepthCue(!cagdGetDepthCue());
      cagdRedraw();
      return 0;
    case CAGD_SENSLESS:
      lessSensitive();
      return 0;
    case CAGD_SENSMORE:
      moreSensitive();
      return 0;
    case CAGD_FUZZLESS:
      lessFuzziness();
      return 0;
    case CAGD_FUZZMORE:
      moreFuzziness();
      return 0;
    case CAGD_RESET:
      cagdReset();
      cagdRedraw();
      return 0;
    case CAGD_HELP:
      cagdShowHelp();
      return 0;
    default:
      if(CAGD_USER <= id){
	callback(CAGD_MENU, id, 0);
	return 0;
      }
      break;
    }
    break;
    
  case WM_LBUTTONDOWN:
    
    if(!(state & (MK_CONTROL | MK_SHIFT))){
      state |= MK_LBUTTON;
      SetCapture(hWnd);
      callback(CAGD_LBUTTONDOWN, LOINT(lParam), HIINT(lParam));
      return 0;
    }
    if(state & (MK_MBUTTON | MK_RBUTTON))
      return 0;
    state |= MK_LBUTTON;
    x = (short)LOWORD(lParam);
    y = (short)HIWORD(lParam);
    SetCapture(hWnd);
    return 0;
    
  case WM_LBUTTONUP:
    
    if(!(state & MK_LBUTTON))
      return 0;
    state &= ~MK_LBUTTON;
    if(state & (MK_CONTROL | MK_SHIFT))
      saveModelView();
    else
      callback(CAGD_LBUTTONUP, LOINT(lParam), HIINT(lParam));
    ReleaseCapture();
    return 0;
    
  case WM_RBUTTONDOWN:
    
    if(!(state & (MK_CONTROL | MK_SHIFT))){
      state |= MK_RBUTTON;
      SetCapture(hWnd);
      callback(CAGD_RBUTTONDOWN, LOINT(lParam), HIINT(lParam));
      return 0;
    }
    if(state & (MK_LBUTTON | MK_MBUTTON))
      return 0;
    state |= MK_RBUTTON;
    x = (short)LOWORD(lParam);
    y = (short)HIWORD(lParam);
    SetCapture(hWnd);
    return 0;
    
  case WM_RBUTTONUP:
    
    if(!(state & MK_RBUTTON))
      return 0;
    state &= ~MK_RBUTTON;
    if(state & (MK_CONTROL | MK_SHIFT))
      saveModelView();
    else
      callback(CAGD_RBUTTONUP, LOINT(lParam), HIINT(lParam));
    ReleaseCapture();
    return 0;
    
  case WM_MBUTTONDOWN:
    
    if(!(state & (MK_CONTROL | MK_SHIFT))){
      state |= MK_MBUTTON;
      SetCapture(hWnd);
      callback(CAGD_MBUTTONDOWN, LOINT(lParam), HIINT(lParam));
      return 0;
    }
    if(state & (MK_LBUTTON | MK_RBUTTON))
      return 0;
    state |= MK_MBUTTON;
    return 0;
    
  case WM_MBUTTONUP:
    
    //Bugfix Octavian + Avishai Dec 01 2002
    //if(!(state & MK_RBUTTON))
      if(!(state & MK_MBUTTON))
      return 0;
    state &= ~MK_MBUTTON;
    if(!(state & (MK_CONTROL | MK_SHIFT)))
    //Bugfix Octavian + Avishai Dec 01 2002
    //callback(CAGD_RBUTTONUP, LOINT(lParam), HIINT(lParam));
    callback(CAGD_MBUTTONUP, LOINT(lParam), HIINT(lParam));
    ReleaseCapture();
    return 0;
    
  case WM_MOUSEMOVE:
    
    if(state & MK_CONTROL) {
      if(state & MK_LBUTTON)
	rotateXY(LOINT(lParam) - x, HIINT(lParam) - y);
      else if(state & MK_RBUTTON)
	rotateZ(LOINT(lParam) - x, HIINT(lParam) - y);
    } else if(state & MK_SHIFT) {
      if(state & MK_LBUTTON)
	translateXY(LOINT(lParam) - x, HIINT(lParam) - y);
      else if(state & MK_RBUTTON)
	translateZ(LOINT(lParam) - x, HIINT(lParam) - y);
    } else
      callback(CAGD_MOUSEMOVE, LOINT(lParam), HIINT(lParam));
    return 0;
    
  case WM_TIMER:
    if(state)
      return 0;
    callback(CAGD_TIMER, 0, 0);
    return 0;
    
  case WM_KEYDOWN:
    switch(wParam){
    case VK_CONTROL:
    case VK_SHIFT:
      if(state)
	return 0;
      state |= (wParam == VK_CONTROL)? MK_CONTROL: MK_SHIFT;
      return 0;
    }
    break;
    
  case WM_KEYUP:
    switch(wParam){
    case VK_CONTROL:
    case VK_SHIFT:
      key = (wParam == VK_CONTROL)? MK_CONTROL: MK_SHIFT;
      if(!(state & key))
	return 0;
      state &= ~key;
      if(state & MK_LBUTTON){
	saveModelView();
	state &= ~MK_LBUTTON;
	ReleaseCapture();
      } else if(state & MK_RBUTTON){
	saveModelView();
	state &= ~MK_RBUTTON;
	ReleaseCapture();
      }
      return 0;
    case VK_SUBTRACT:
    case 0xBD: /* '-' */
      scale(0.9);
      return 0;
    case VK_ADD:
    case 0xBB: /* '+' w/o shift */
      scale(1.1);
      return 0;
    }
    break;

  }
	
  /* BUGFIX: 22/10/2001, Tatiana&Vitaly Surazhsky {tess|vitus}@cs.technion.ac.il  */
  /* BUG: crash on some system, FIX: use CallWindowProc instead of direct function call  */
  return CallWindowProc((WNDPROC)GetWindowLong(hWnd, GWL_USERDATA),
    hWnd, message, wParam, lParam);
}

BOOL cagdAppendMenu(HMENU hMenu, PCSTR name)
{
  HWND hWnd = auxGetHWND();
  if(InsertMenu(GetMenu(hWnd), CAGD_HELP, MF_BYCOMMAND | MF_POPUP, (UINT)hMenu, name))
    return DrawMenuBar(hWnd);
  return FALSE;
}

BOOL cagdRemoveMenu(HMENU hMenu)
{
  HWND hWnd = auxGetHWND();
  if(RemoveMenu(GetMenu(hWnd), (UINT)hMenu, MF_BYCOMMAND))
    return DrawMenuBar(hWnd);
  return FALSE;
}

void menuSetView()
{
  HMENU hMenu = GetMenu(auxGetHWND());
  CheckMenuItem(hMenu, CAGD_ORTHO, MF_UNCHECKED);
  CheckMenuItem(hMenu, CAGD_PERSP, MF_UNCHECKED);
  CheckMenuItem(hMenu, cagdGetView(), MF_CHECKED);
}

void menuSetDepthCue()
{
  HMENU hMenu = GetMenu(auxGetHWND());
  CheckMenuItem(hMenu, CAGD_CUE, cagdGetDepthCue()? MF_CHECKED: MF_UNCHECKED);
}

void cagdSetHelpText(PCSTR newHelpText)
{
  if(helpText)
    free(helpText);
  helpText = _strdup(newHelpText? newHelpText: defaultHelpText);
}

BOOL cagdShowHelp()
{
  if(!helpText)
    return FALSE;
  MessageBox(NULL, helpText, "CAGD Help", MB_OK | MB_TASKMODAL | MB_ICONINFORMATION);
  return TRUE;
}

void createMenu()
{
  HWND hWnd = auxGetHWND();
  HMENU hMenu = CreateMenu();
  HMENU hSubMenu = CreatePopupMenu();
  AppendMenu(hSubMenu, MF_STRING, CAGD_LOAD, "Load...");
  AppendMenu(hSubMenu, MF_STRING, CAGD_SAVE, "Save...");
  AppendMenu(hSubMenu, MF_SEPARATOR, 0, 0);
  AppendMenu(hSubMenu, MF_STRING, CAGD_EXIT, "Exit");
  AppendMenu(hMenu, MF_POPUP, (UINT)hSubMenu, "File");
  hSubMenu = CreatePopupMenu();
  AppendMenu(hSubMenu, MF_STRING, CAGD_ORTHO, "Orthographic");
  AppendMenu(hSubMenu, MF_STRING, CAGD_PERSP, "Perspective");
  AppendMenu(hSubMenu, MF_SEPARATOR, 0, 0);
  AppendMenu(hSubMenu, MF_STRING, CAGD_CUE, "Depth Cue");
  AppendMenu(hSubMenu, MF_SEPARATOR, 0, 0);
  AppendMenu(hSubMenu, MF_STRING, CAGD_SENSLESS, "Less Sensitive Mouse");
  AppendMenu(hSubMenu, MF_STRING, CAGD_SENSMORE, "More Sensitive Mouse");
  AppendMenu(hSubMenu, MF_SEPARATOR, 0, 0);
  AppendMenu(hSubMenu, MF_STRING, CAGD_FUZZLESS, "Less Fuzzy Select");
  AppendMenu(hSubMenu, MF_STRING, CAGD_FUZZMORE, "More Fuzzy Select");
  AppendMenu(hSubMenu, MF_SEPARATOR, 0, 0);
  AppendMenu(hSubMenu, MF_STRING, CAGD_RESET, "Reset");
  AppendMenu(hMenu, MF_POPUP, (UINT)hSubMenu, "View");
  AppendMenu(hMenu, MF_STRING, CAGD_HELP, "Help!");
  SetMenu(hWnd, hMenu);
  menuSetView();
  menuSetDepthCue();
  cagdSetHelpText(NULL);
  SetWindowLong(hWnd, GWL_USERDATA, GetWindowLong(hWnd, GWL_WNDPROC));
  SetWindowLong(hWnd, GWL_WNDPROC, (LONG)command);
}

WORD cagdPostMenu(HMENU hMenu, int x, int y)
{
  MSG message;
  POINT p = { x, y };
  HWND hWnd = auxGetHWND();
  ClientToScreen(hWnd, &p);
  state = 0;
  ReleaseCapture();
  TrackPopupMenu(hMenu,
		 TPM_LEFTALIGN | TPM_RIGHTBUTTON,
		 p.x, p.y,
		 0, hWnd, NULL);
  return PeekMessage(&message, hWnd, WM_COMMAND, WM_COMMAND, PM_REMOVE)?
    LOWORD(message.wParam): 0;
}

HMODULE cagdGetModule()
{
  return GetModuleHandle(NULL);
}

HWND cagdGetWindow()
{
  return auxGetHWND();
}
