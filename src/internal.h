/************************************************************************
* Copyright (C) 1996, by Dmitri Bassarab.				*
* Send bugs and/or frames to /dev/null or dima@cs.technion.ac.il	*
*************************************************************************/
#ifndef _INTERNAL_H_
#define _INTERNAL_H_

#ifdef __cplusplus
extern "C" {
#endif
  
void drawSegments(GLenum);
void saveModelView();
void rotateXY(int, int);
void translateXY(int, int);
void rotateZ(int, int);
void translateZ(int, int);
void scale(GLdouble);
void reset();
void createMenu();
void menuSetView();
void menuSetDepthCue();
void moreFuzziness();
void lessFuzziness();
void moreSensitive();
void lessSensitive();

#ifdef __cpluscplus
}
#endif

#endif
