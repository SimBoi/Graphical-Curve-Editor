/************************************************************************
* Copyright (C) 1996, by Dmitri Bassarab.				*
* Send bugs and/or frames to /dev/null or dima@cs.technion.ac.il	*
*************************************************************************/
#include "cagd.h"
#include "internal.h"

#define Z_NEAR  0.001
#define Z_SHIFT 2
#define MAX_HITS 100
#define POINT_SIZE 3

static WORD view = CAGD_ORTHO;
static BOOL cue = FALSE;
static GLdouble modelView[16], projection[16];
static GLint viewPort[4] = { 0, 0, 0, 0 };
static GLuint hits[MAX_HITS];
static GLint nHits;
static GLint fuzziness = 4;
static GLdouble sensitive = 1;

void cagdPick(int x, int y)
{
  glMatrixMode(GL_PROJECTION);
  glPushMatrix();
  glLoadIdentity();
  gluPickMatrix(x, viewPort[3] - y, fuzziness * 2, fuzziness * 2, viewPort);
  glMultMatrixd(projection);
  glSelectBuffer(MAX_HITS, hits);
  glRenderMode(GL_SELECT);
  drawSegments(GL_SELECT);
  nHits = glRenderMode(GL_RENDER); 
  glPopMatrix();
  glMatrixMode(GL_MODELVIEW);
}

UINT cagdPickNext()
{
  if(nHits > 0)
    return hits[--nHits * 4 + 3];
  return 0;
}

BOOL cagdToObject(int x, int y, CAGD_POINT where[2])
{
  GLdouble X = x, Y = viewPort[3] - y;
  return 
    gluUnProject(X, Y, 0.,
		 modelView, projection, viewPort,
		 &where[0].x, &where[0].y, &where[0].z) &&
		   gluUnProject(X, Y, 1.,
				modelView, projection, viewPort,
				&where[1].x, &where[1].y, &where[1].z);
  
} 

BOOL cagdToWindow(CAGD_POINT *where, int *x, int *y)
{
  GLdouble X, Y, z;
  BOOL r = gluProject(where->x, where->y, where->z,
		      modelView, projection, viewPort,
		      &X, &Y, &z);
  *x = (int)X;
  *y = viewPort[3] - (int)Y;
  return r;
}

static void CALLBACK reDraw(void)
{
  drawSegments(GL_RENDER);
  auxSwapBuffers();
}

void cagdRedraw()
{
  reDraw();
}

static void CALLBACK resize(GLsizei width, GLsizei height)
{
  GLdouble s = (GLdouble)width / (height? height: 1);
  glViewport(0, 0, viewPort[2] = width, viewPort[3] = height);
  glMatrixMode(GL_PROJECTION);
  glLoadIdentity();
  if(width > height)
    if(view == CAGD_ORTHO)
      glOrtho(-1 * s, 1 * s, -1, 1, Z_NEAR, 1/Z_NEAR);
    else
      glFrustum(-Z_NEAR * s, Z_NEAR * s, -Z_NEAR, Z_NEAR, Z_NEAR, 1/Z_NEAR);
  else
    if(view == CAGD_ORTHO)
      glOrtho(-1, 1, -1 / s, 1 / s, Z_NEAR, 1/Z_NEAR);
    else
      glFrustum(-Z_NEAR, Z_NEAR, -Z_NEAR / s, Z_NEAR / s, Z_NEAR, 1/Z_NEAR);
  glGetDoublev(GL_PROJECTION_MATRIX, projection);
  glMatrixMode(GL_MODELVIEW);
}	

WORD cagdGetView()
{
  return view;
}

void cagdSetView(WORD newView)
{
  if(view == newView)
    return;
  view = newView;
  resize(viewPort[2], viewPort[3]);
  menuSetView(view);
  return;
}

BOOL cagdGetDepthCue()
{
  return cue;
}

void cagdSetDepthCue(BOOL enable)
{
  if(cue == enable)
    return;
  if(cue = enable)
    glEnable(GL_FOG);
  else
    glDisable(GL_FOG);
  menuSetDepthCue(enable);
}

void saveModelView()
{
  glGetDoublev(GL_MODELVIEW_MATRIX, modelView);
}

static void shift()
{
  glLoadIdentity();
  glTranslated(0, 0, -Z_SHIFT - Z_NEAR);
}

static void multModelView()
{
  glTranslated(0, 0,  Z_SHIFT + Z_NEAR);
  glMultMatrixd(modelView);
}


void cagdRotate(GLdouble angle, GLdouble x, GLdouble y, GLdouble z)
{
  shift();
  glRotated(angle, x, y, z);
  multModelView();
  saveModelView();
}

void cagdTranslate(GLdouble x, GLdouble y, GLdouble z)
{
  shift();
  multModelView();
  glTranslated(x, y, z);
  saveModelView();
}

void cagdScale(GLdouble x, GLdouble y, GLdouble z)
{
  shift();
  glScaled(x, y, z);
  multModelView();
  saveModelView();
}

void rotateXY(int dX, int dY)
{
  GLdouble x = 1, y = 0, angle, sign = (dY < 0)? -1: 1;
  shift();
  if(dX){
    x = (GLdouble)dY / dX;
    y = 1;
    sign = (dX < 0)? -1: 1;
  }
  angle = sqrt((GLdouble)dX * dX + dY * dY) * 360
    / min(viewPort[2], viewPort[3]);
  glRotated(sensitive * sign * angle, x, y, 0);
  multModelView();
  reDraw();
}

void translateXY(int dX, int dY)
{
  CAGD_POINT origin, where[2];
  WORD theView = view;
  cagdSetView(CAGD_ORTHO);
  cagdToObject(0, 0, where);
  origin = where[0];
  cagdToObject(dX, dY, where);
  cagdSetView(theView);
  shift();
  multModelView();
  glTranslated(sensitive * (where[0].x - origin.x), 
	       sensitive * (where[0].y - origin.y), 
	       sensitive * (where[0].z - origin.z));
  reDraw();
}

void rotateZ(int dX, int dY)
{
  shift();
  glRotated(sensitive * dX * 180 / min(viewPort[2], viewPort[3]), 0, 0, 1);
  multModelView();
  reDraw();
}

void translateZ(int dX, int dY)
{
  shift();
  glTranslated(0, 0, sensitive * dX / min(viewPort[2], viewPort[3]));
  multModelView();
  reDraw();
}

void scale(GLdouble factor)
{
  cagdScale(factor, factor, factor);
  reDraw();
}

void cagdReset()
{
  glMatrixMode(GL_MODELVIEW);
  glLoadIdentity();
  shift();
  glGetDoublev(GL_MODELVIEW_MATRIX, modelView);
}

void cagdBegin(PCSTR title, int width, int height)
{
  auxInitDisplayMode(AUX_DOUBLE | AUX_RGB);
  auxInitPosition(CW_USEDEFAULT, CW_USEDEFAULT, width, height);
  auxInitWindow(title);
  auxReshapeFunc(resize);
  auxCreateFont();
  glFogi(GL_FOG_MODE, GL_LINEAR);
  glFogf(GL_FOG_START, 1.f);
  glFogf(GL_FOG_END, 2.f * Z_SHIFT);
  glPointSize((GLfloat)POINT_SIZE); 
  cagdReset();
  createMenu();
}

void cagdMainLoop()
{
  auxMainLoop(reDraw);
}

void moreFuzziness()
{
  fuzziness *= 2;
}

void lessFuzziness()
{
  if(fuzziness > 1)
    fuzziness /= 2;
}

void moreSensitive()
{
  sensitive *= 2;
}

void lessSensitive()
{
  sensitive /= 2;
}
