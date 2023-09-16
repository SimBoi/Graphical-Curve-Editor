/*****************************************************************************
*   (C) Copywrite, Gershon Elber 1989,		All rights reserved.	     *
*   Free usage for non commercial programs only.			     *
*									     *
*   Module to convert infix expression given as a string into a binary tree. *
* Evaluate trees, and make symbolic derivation of such trees.                *
*                                                                            *
* Main routines (all names are prefixed with e2t_):                          *
* 1. e2t_expr_node *expr2tree(s) - main routine to perform conversion.       *
*    int parserror()         - return error number (expr2tree.h), 0 o.k.     *
* 2. printtree(root,0)       - routine to print in infix form content of tree*
* 3. e2t_expr_node *copytree(root) - returns a new copy of root pointed tree.*
* 4. double evaltree(root)    - evaluate expression for a given param.       *
* 5. e2t_expr_node *derivtree(root,prm) - returns new tree, rep. its         *
*                               derivative according to parameter prm.       *
*    int deriverror()           - return error number (expr2tree.h), 0 o.k.  *
* 6. int setparamvalue(Value,Number) - set that parameter value...           *
*                                                                            *
* In addition:                                                               *
* 7. int cmptree(root1,root2) - compere symbolically two trees.              *
* 8. int paramintree(root,parameter) - return TRUE if parameter in tree.     *
* 9. freetree(root) - release memory allocated for tree root.                *
*                                                                            *
* Written by:  Gershon Elber                           ver 1.0, Jan. 1988    *
*                                                                            *
* Ver 0.2 modifications: replace old inc. notation (=+) with new (+=).       *
* Ver 0.3 modifications: parameter can be T or X (was only T).               *
*                        printtree(root,String) print the tree into String   *
*                          or to screen (as it was) if String address in null*
*                        setparamchar(c) - set the parameter char, t default *
* Ver 0.4 modifications: split expr2tree.h into local and globals consts.    *
*                                                                            *
* Ver 1.0 modifications: multiple variables is now supported, meaning        *
*                        functions of few variables can new be evaluated and *
*                        derivated!. Note that for some of the functions,    *
*                        the parameter of them were modified/added.          *
*                        Now integer power of negative numbers is supported. *
* Ver 1.1 modifications: the parser was modified to use operator precedence  *
*                        and the associativity of the operators is correct.  *
*****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <math.h>
#include "expr2tree.h"

#define  LINELEN   255
#define  TAB       9
#define  TRUE      1
#define  FALSE     0

#define  MAX_PARSER_STRACK   100
   
#define ABS         10 /* Functions */
#define ARCCOS      11
#define ARCSIN      12
#define ARCTAN      13
#define COS         14
#define EXP         15
#define LN          16
#define LOG         17
#define SIN         18
#define SQR         19
#define SQRT        20
#define TAN         21

#define PLUS        30 /* Operators */
#define MINUS       31
#define MULT        32
#define DIV         33
#define POWER       34
#define UNARMINUS   35

#define OPENPARA    40 /* Paranthesis */
#define CLOSPARA    41

#define NUMBER      50 /* Numbers (or parameter t) */
#define PARAMETER   51

#define TOKENERROR  -1
#define TOKENSTART  100
#define TOKENEND    101 

int    e2t_parsing_error;                   /* Globals used by the parser */
static int glbl_token, glbl_last_token;
static int glbl_deriv_error;                 /* Globals used by derivations */
static double GlobalParam[E2T_PARAM_Z1];     /* The parameters are save here */

static e2t_expr_node *e2t_malloc(unsigned size);
static void e2t_free(e2t_expr_node *Ptr);
static void make_upper(char s[]);
static e2t_expr_node *operator_precedence(const char s[], int *i);
static int test_preceeding(int token1, int token2);
static void un_get_token(int token);
static int get_token(const char s[], int *i, double *data);
static void localprinttree(const e2t_expr_node *root, int level, char *str);
static e2t_expr_node *derivtree1(const e2t_expr_node *root, int prm);
static e2t_expr_node *gen1u2tree(int sign1,
				 int sign2,
				 double exponent,
				 e2t_expr_node *expr);
static e2t_expr_node *optimize(e2t_expr_node *root, int *flag);

/*****************************************************************************
*  Routine to return one expression node from free list or allocate new one: *
*****************************************************************************/
static e2t_expr_node *e2t_malloc(unsigned size)
{
    return (e2t_expr_node *) malloc(size);
}

/*****************************************************************************
*  Routine to return one expression node from free list or allocate new one: *
*****************************************************************************/
static void e2t_free(e2t_expr_node *Ptr)
{
    free((char *) Ptr);
}

/*****************************************************************************
*  Routine to convert lower case chars into upper one in the given string:   *
*****************************************************************************/
static void make_upper(char s[])
{
    int i;
   
    i=0;
    while (s[i] != 0) {
         if (islower(s[i])) s[i] = toupper(s[i]);
         i++;
    }
}

/*****************************************************************************
*   Routine to convert the expression in string S into a binary tree.        *
* Algorithm: Using operator precedence with the following grammer:           *
* EXPR    ::= EXPR    |  EXPR + EXPR    |  EXPR - EXPR                       *
* EXPR    ::= EXPR    |  EXPR * EXPR    |  EXPR / EXPR                       *
* EXPR    ::= EXPR    |  EXPR ^ EXPR                                         *
* EXPR    ::= NUMBER  |  -EXPR          |  (EXPR)        |  FUNCTION         *
* FUCTION ::= SIN(EXPR)    | COS(EXPR)    | TAN(EXPR)                        *
*             ARCSIN(EXPR) | ARCCOS(EXPR) | ARCTAN(EXPR)                     *
*             SQRT(EXPR)   | SQR(EXPR)    | ABS(EXPR)                        *
*             LN(EXPR)     | LOG(EXPR)    | EXP(EXPR)                        *
*                                                                            *
* And left associativity for +, -, *, /, ^.                                  *
* Precedence of operators is as usual:                                       *
*     <Highest> {unar minus}   {^}   {*,/}   {+,-} <Lowest>                  *
*                                                                            *
* Returns NULL if an error was found, and error is in e2t_parsing_error      *
*****************************************************************************/
e2t_expr_node *e2t_expr2tree(const char s[])
{
    e2t_expr_node *root;
    int i;
    char
        *s2 = (char *) malloc(strlen(s) + 1);

    strcpy(s2, s);

    make_upper(s2);
    glbl_token = 0;           /* Used to save unget token (one level stack) */
    glbl_last_token = 0;        /* Used to hold last token read from stream */
    e2t_parsing_error = 0;                          /* No errors so far ... */
    i = 0;
    root = operator_precedence(s2, &i);    

    free(s2);
 
    if (e2t_parsing_error)
        return (e2t_expr_node *) NULL;				 /* Error ! */
    else
        return root;
}

/*****************************************************************************
*   Routine to actually parse using operator precedence:                     *
* Few Notes:                                                                 *
* 1. Parse the string s with the help of get_token routine. i holds current  *
*    position in string s.                                                   *
* 2. All tokens must be in the range of 0..999 as we use the numbers above   *
*    it (adding 1000) to deactivate them in the handle searching (i.e. when  *
*    they were reduced to sub.-expression).                                  *
* 3. Returns NULL pointer in case of an error (see gexpr2tree.h for errors   *
* 4. See "Compilers - principles, techniques and tools" by Aho, Sethi &      *
*    Ullman, pages 207-210.                                                  *
*****************************************************************************/
static e2t_expr_node *operator_precedence(const char s[], int *i)
{
    int token, low_handle, temp1, temp2, stack_pointer = 0;
    double data;
    e2t_expr_node *stack[MAX_PARSER_STRACK];

    /* Push the start symbol on stack (node pointer points on tos): */
    stack[stack_pointer] = e2t_malloc(sizeof(e2t_expr_node));
    stack[stack_pointer] -> node_kind = TOKENSTART;
    stack[stack_pointer] -> right = 
    stack[stack_pointer] -> left = (e2t_expr_node *) NULL;
    token = get_token(s, i, &data);/* Get one look ahead token to start with */
    do {
	if (e2t_parsing_error) return (e2t_expr_node *) NULL;
        temp1 = stack_pointer;    /* Find top active token (less than 1000) */
        while (stack[temp1] -> node_kind >= 1000) temp1--;
        /* Now test to see if the new token completes an handle: */
        if (test_preceeding(stack[temp1] -> node_kind, token) > 0) {
            switch (token) {
		case CLOSPARA:
                    if (stack[temp1] -> node_kind == OPENPARA) {
                        if (stack_pointer-temp1 != 1) {
                            e2t_parsing_error = E2T_PARAMATCH_ERROR;
			    return (e2t_expr_node *) NULL;
			}
                        switch (stack[temp1-1] -> node_kind) {
			    case ABS:    /* If it is of the form Func(Expr) */
			    case ARCCOS: /* Then reduce it directly to that */
			    case ARCSIN: /* function, else (default) reduce */
			    case ARCTAN: /* to sub-expression.              */
			    case COS:
			    case EXP:
			    case LN:
			    case LOG:
			    case SIN:
			    case SQR:
			    case SQRT:
			    case TAN:
                                free(stack[temp1]); /* Free the open paran. */
				stack[stack_pointer] -> node_kind -= 1000;
				stack[temp1-1] -> node_kind += 1000;
			        stack[temp1-1] -> right = stack[stack_pointer];
				stack_pointer -= 2;
				break;
			    default:
                                free(stack[temp1]); /* Free the open paran. */
                                stack[temp1] = stack[stack_pointer--];
				break;
			}
                        token = get_token(s, i, &data); /* Get another token */
                        continue;
		    }
                    else if (stack[temp1] -> node_kind == TOKENSTART) {
			/* No match for this one! */
                        e2t_parsing_error = E2T_PARAMATCH_ERROR;
			return (e2t_expr_node *) NULL;
		    }
		    break;
                case TOKENEND:
                    if (stack[temp1] -> node_kind == TOKENSTART) {
                        if (stack_pointer != 1) {
                            e2t_parsing_error = E2T_SYNTAX_ERROR;
			    return (e2t_expr_node *) NULL;
			}
			if (stack[0] != NULL)
			  free(stack[0]);
			stack[1] -> node_kind -= 1000;
			return stack[1];
		    }
		}

            temp2 = temp1-1;              /* Find the lower bound of handle */
            while (stack[temp2] -> node_kind >= 1000) temp2--;
            low_handle = temp2 + 1;
            if (low_handle < 1) {                 /* No low bound was found */
                e2t_parsing_error = E2T_SYNTAX_ERROR;
	        return (e2t_expr_node *) NULL;   /* We ignore data till now */
            }
	    switch (stack_pointer - low_handle + 1) {
		case 1: /* Its a scalar one - mark it as used (add 1000) */
		    switch (stack[stack_pointer] -> node_kind) {
			case NUMBER:
			case PARAMETER:
		            stack[stack_pointer] -> node_kind += 1000;
			    break;
			default:
			    e2t_parsing_error = E2T_PARAM_EXPECT_ERROR;
			    return (e2t_expr_node *) NULL;
		            break;
		    }
		    break;
		case 2: /* Its a nmonadic operator - create the subtree */
		    switch (stack[stack_pointer-1] -> node_kind) {
		        case UNARMINUS:
		            stack[stack_pointer-1] -> right =
                                                        stack[stack_pointer];
		            stack[stack_pointer] -> node_kind -= 1000;
		            stack[stack_pointer-1] -> node_kind += 1000;
		            stack_pointer --;
		            break;
		        case OPENPARA:
			    e2t_parsing_error = E2T_PARAMATCH_ERROR;
			    return (e2t_expr_node *) NULL;
		            break;
		        default:
			    e2t_parsing_error = E2T_ONE_OPERAND_ERROR;
			    return (e2t_expr_node *) NULL;
		            break;
		    }
		    break;
		case 3: /* Its a diadic operator - create the subtree */
		    switch (stack[stack_pointer-1] -> node_kind) {
		        case PLUS:
		        case MINUS:
		        case MULT:
		        case DIV:
		        case POWER:
		            stack[stack_pointer-1] -> right =
                                  stack[stack_pointer];
                            stack[stack_pointer-1] -> left =
                                  stack[stack_pointer-2];
		            stack[stack_pointer-2] -> node_kind -= 1000;
		            stack[stack_pointer] -> node_kind -= 1000;
		            stack[stack_pointer-1] -> node_kind += 1000;
		            stack[stack_pointer-2] = stack[stack_pointer-1];
		            stack_pointer -= 2;
                            break;
                        default:
			    e2t_parsing_error = E2T_TWO_OPERAND_ERROR;
			    return (e2t_expr_node *) NULL;
		            break;
		    }
		    break;
	    }
        }
        else {           /* Push that token on stack - it is not handle yet */
	    stack[++stack_pointer] = e2t_malloc(sizeof(e2t_expr_node));
            if (stack_pointer == MAX_PARSER_STRACK-1) {
                e2t_parsing_error = E2T_STACK_OV_ERROR;
		return (e2t_expr_node *) NULL;   /* We ignore data till now */
	    }
            stack[stack_pointer] -> node_kind = token;
            stack[stack_pointer] -> data = data;   /* We might need that... */
	    stack[stack_pointer] -> right = 
	    stack[stack_pointer] -> left = (e2t_expr_node *) NULL;
            token = get_token(s, i, &data);/* And get new token from stream */
	}
    }
    while (TRUE);
}

/*****************************************************************************
*   Routine to test precedence of two tokens. returns 0, <0 or >0 according  *
* to comparison results:                                                     *
*****************************************************************************/
static int test_preceeding(int token1, int token2)
{
    int preced1, preced2;

    if ((token1 >= 1000) || (token2 >= 1000)) return 0; /* Ignore sub-expr */

    switch (token1) {
	case ABS:
	case ARCCOS:
	case ARCSIN:
	case ARCTAN:
	case COS:
	case EXP:
	case LN:
	case LOG:
	case SIN:
	case SQR:
	case SQRT:
	case TAN:        preced1 =100; break;
	case NUMBER:
	case PARAMETER:  preced1 =120; break;
	case PLUS:
	case MINUS:      preced1 = 20; break;
	case MULT:
	case DIV:        preced1 = 40; break;
	case POWER:      preced1 = 60; break;
	case UNARMINUS:  preced1 = 65; break;
	case OPENPARA:   preced1 =  5; break;
	case CLOSPARA:   preced1 =120; break;
	case TOKENSTART:
	case TOKENEND:   preced1 =  5; break;
    }

    switch (token2) {
	case ABS:
	case ARCCOS:
	case ARCSIN:
	case ARCTAN:
	case COS:
	case EXP:
	case LN:
	case LOG:
	case SIN:
	case SQR:
	case SQRT:
	case TAN:        preced2 = 90; break;
	case NUMBER:
	case PARAMETER:  preced2 =110; break;
	case PLUS:
	case MINUS:      preced2 = 10; break;
	case MULT:
	case DIV:        preced2 = 30; break;
	case POWER:      preced2 = 50; break;
	case UNARMINUS:  preced2 = 70; break;
	case OPENPARA:   preced2 =110; break;
	case CLOSPARA:   preced2 =  0; break;
	case TOKENSTART:
	case TOKENEND:   preced2 =  0; break;
    }

    return preced1-preced2;
}

/*****************************************************************************
*   Routine to unget one token (stack of level one!)                         *
*****************************************************************************/
static void un_get_token(int token)
{
    glbl_token = token; /* none zero glbl_token means it exists */
}

/*****************************************************************************
*   Routine to get the next token out of the expression.                     *
* Gets the expression in S, and current position in i.                       *
* Returns the next token found, set data to the returned value (if any),     *
* and update i to one char ofter the new token found.                        *
*   Note that in minus sign case, it is determined whether it is monadic or  *
* diadic minus by the last token - if the last token was operator or '('     *
* it is monadic minus.                                                       *
*****************************************************************************/
static int get_token(const char s[], int *i, double *data)
{
    int j;
    char number[LINELEN], c;
	
    if (glbl_token) { /* get first the un_get_token */
        j = glbl_token;
        glbl_token = 0;
        glbl_last_token = j;
        return j;
    }

    while ((s[*i]==' ')||(s[*i]==TAB)) (*i)++;
    if (*i>= strlen(s)) return TOKENEND;   /* No more tokens around here... */

    /* Check is next token is one char - if so its a parameter */
    if ((islower(s[*i]) || isupper(s[*i])) &&
       !(islower(s[(*i)+1]) || isupper(s[(*i)+1]))) {
        if (islower(c = s[(*i)++])) c = toupper(c); /* make paramter upcase */
        *data = c - 'A'; /* A = 0, B = 1, ... */
        glbl_last_token = PARAMETER;
        return PARAMETER;
    }
        
    if (isdigit(s[*i])||(s[*i]=='.')) {
        j=0;
        while (isdigit(s[*i])||(s[*i]=='.')) number[j++]=s[(*i)++];
        number[j] = 0;
        (void) sscanf(number, "%lf", data);
        glbl_last_token = NUMBER;
        return NUMBER;
    }

    switch(s[(*i)++])
    {
    case (uintptr_t)NULL : glbl_last_token = 0; return 0;
    case '+' : glbl_last_token = PLUS; return PLUS;
    case '-' : switch (glbl_last_token) {
	           case (uintptr_t)NULL:  /* If first token (no last token yet) */
	           case PLUS:
	           case MINUS:
	           case MULT:
	           case DIV:
	           case POWER:
	           case UNARMINUS:
	           case OPENPARA:
                        glbl_last_token= UNARMINUS; return UNARMINUS;
		   default:
                        glbl_last_token= MINUS; return MINUS;
	       }
    case '*' : glbl_last_token = MULT; return MULT;
    case '/' : glbl_last_token = DIV; return DIV;
    case '^' : glbl_last_token = POWER; return POWER;
    case '(' : glbl_last_token = OPENPARA; return OPENPARA;
    case ')' : glbl_last_token = CLOSPARA; return CLOSPARA;
    case 'A' : if ((s[*i]=='R')&&(s[*i+1]=='C')) {
                   (*i)+=2;
                   switch(get_token(s, i, data))
                   {
                   case SIN : glbl_last_token = ARCSIN; return ARCSIN;
                   case COS : glbl_last_token = ARCCOS; return ARCCOS;
                   case TAN : glbl_last_token = ARCTAN; return ARCTAN;
                   default :  e2t_parsing_error = E2T_UNDEF_TOKEN_ERROR;
                              return TOKENERROR;
                   }
               }
               else  if ((s[*i]=='B')&&(s[*i+1]=='S')) {
                   (*i)+=2;
                   glbl_last_token = ABS;
                   return ABS;
               }
               else {
                   e2t_parsing_error = E2T_UNDEF_TOKEN_ERROR;
                   return TOKENERROR;
               }
    case 'C' : if ((s[*i]=='O')&&(s[*i+1]=='S')) {
                   (*i)+=2;
                   glbl_last_token = COS;
                   return COS;
               }
               else {
                   e2t_parsing_error = E2T_UNDEF_TOKEN_ERROR;
                   return TOKENERROR;
               }
    case 'E' : if ((s[*i]=='X')&&(s[*i+1]=='P')) {
                   (*i)+=2;
                   glbl_last_token = EXP;
                   return EXP;
               }
               else {
                   e2t_parsing_error = E2T_UNDEF_TOKEN_ERROR;
                   return TOKENERROR;
               }
    case 'L' : if ((s[*i]=='O')&&(s[*i+1]=='G')) {
                   (*i)+=2;
                   glbl_last_token = LOG;
                   return LOG;
               }
               else if (s[*i]=='N') {
                   (*i)++;
                   glbl_last_token = LN;
                   return LN;
               }
               else {
                   e2t_parsing_error = E2T_UNDEF_TOKEN_ERROR;
                   return TOKENERROR;
               }
    case 'S' : if ((s[*i]=='I')&&(s[*i+1]=='N')) {
                   (*i)+=2;
                   glbl_last_token = SIN;
                   return SIN;
               }
               else if ((s[*i]=='Q')&&(s[*i+1]=='R')) {
                   (*i)+=2;
                   if (s[*i]=='T') {
                       (*i)++;
                       glbl_last_token = SQRT;
                       return SQRT;
                   }
                   else {
                       glbl_last_token = SQR;
                       return SQR;
		   }
               }
               else {
                   e2t_parsing_error = E2T_UNDEF_TOKEN_ERROR;
                   return TOKENERROR;
               }
    case 'T' : if ((s[*i]=='A')&&(s[*i+1]=='N')) {
                   (*i)+=2;
                   glbl_last_token = TAN;
                   return TAN;
               }
               else return TOKENERROR;
    default :  e2t_parsing_error = E2T_UNDEF_TOKEN_ERROR;
               return TOKENERROR;
    }
}

/*****************************************************************************
*   Routine to print a content of ROOT (using inorder traversal) :           *
* level holds: 0 for lowest level +/-, 1 for *,/, 2 for ^ operations.        *
* If *str = NULL print on stdout, else on given string str.                  *
*****************************************************************************/
void e2t_printtree(const e2t_expr_node *root, char *str)
{

    char LocalStr[255];

    (void) strcpy(LocalStr, ""); /* Make the string empty */

    if (str == NULL) {
         localprinttree(root, 0, LocalStr); /* Copy to local str. */
         printf(LocalStr);                      /* and print... */
    }
    else {
         (void) strcpy(str, ""); /* Make the string empty */
         localprinttree(root, 0, str); /* Dont print to stdout - copy to str */
    }
}

/*****************************************************************************
*   Routine to print a content of ROOT (using inorder traversal) :           *
* level holds: 0 for lowest level +/-, 1 for *,/, 2 for ^ operations.        *
*****************************************************************************/
static void localprinttree(const e2t_expr_node *root, int level, char *str)
{
    int closeflag = FALSE;

    if (!root) return;

    switch(root->node_kind) {
    case ABS :     (void) strcat(str, "abs(");
                   level = 0;        /* Paranthesis are opened */
                   closeflag = TRUE; /* must close paranthesis */
                   break;
    case ARCCOS :  (void) strcat(str, "arccos(");
                   level = 0;        /* Paranthesis are opened */
                   closeflag = TRUE; /* must close paranthesis */
                   break;
    case ARCSIN :  (void) strcat(str, "arcsin(");
                   level = 0;        /* Paranthesis are opened */
                   closeflag = TRUE; /* must close paranthesis */
                   break;
    case ARCTAN :  (void) strcat(str, "arctan(");
                   level = 0;        /* Paranthesis are opened */
                   closeflag = TRUE; /* must close paranthesis */
                   break;
    case COS :     (void) strcat(str, "cos(");
                   level = 0;        /* Paranthesis are opened */
                   closeflag = TRUE; /* must close paranthesis */
                   break;
    case EXP :     (void) strcat(str, "exp(");
                   level = 0;        /* Paranthesis are opened */
                   closeflag = TRUE; /* must close paranthesis */
                   break;
    case LN  :     (void) strcat(str, "ln(");
                   level = 0;        /* Paranthesis are opened */
                   closeflag = TRUE; /* must close paranthesis */
                   break;
    case LOG :     (void) strcat(str, "log(");
                   level = 0;        /* Paranthesis are opened */
                   closeflag = TRUE; /* must close paranthesis */
                   break;
    case SIN :     (void) strcat(str, "sin(");
                   level = 0;        /* Paranthesis are opened */
                   closeflag = TRUE; /* must close paranthesis */
                   break;
    case SQR :     (void) strcat(str, "sqr(");
                   level = 0;        /* Paranthesis are opened */
                   closeflag = TRUE; /* must close paranthesis */
                   break;
    case SQRT :    (void) strcat(str, "sqrt(");
                   level = 0;        /* Paranthesis are opened */
                   closeflag = TRUE; /* must close paranthesis */
                   break;
    case TAN :     (void) strcat(str, "tan(");
                   level = 0;        /* Paranthesis are opened */
                   closeflag = TRUE; /* must close paranthesis */
                   break;

    case DIV :     if (level > 1) {
                        (void) strcat(str, "(");
                        closeflag = TRUE; /* must close paranthesis */
                   }
                   level = 1;        /* Div level */
                   localprinttree(root->left, level, str);
                   (void) strcat(str, "/");
                   break;
    case MINUS :   if (level > 0) {
                        (void) strcat(str, "(");
                        closeflag = TRUE; /* must close paranthesis */
                   }
                   level = 0;        /* Minus level */
                   localprinttree(root->left, level, str);
                   (void) strcat(str, "-");
                   break;
    case MULT :    if (level > 1) {
                        (void) strcat(str, "(");
                        closeflag = TRUE; /* must close paranthesis */
                   }
                   level = 1;        /* Mul level */
                   localprinttree(root->left, level, str);
                   (void) strcat(str, "*");
                   break;
    case PLUS :    if (level > 0) {
                        (void) strcat(str, "(");
                        closeflag = TRUE; /* must close paranthesis */
                   }
                   level = 0;        /* Plus level */
                   localprinttree(root->left, level, str);
                   (void) strcat(str, "+");
                   break;
    case POWER :   level = 2;        /* Power level */
                   localprinttree(root->left, level, str);
                   (void) strcat(str, "^");
                   break;
    case UNARMINUS : (void) strcat(str, "(-");
                   level = 0;        /* Unarminus level ! */
                   closeflag = TRUE; /* must close paranthesis */
                   break;

    case NUMBER :  (void) sprintf(&str[strlen(str)], "%lg", root->data);
                   break;
    case PARAMETER : (void) sprintf(&str[strlen(str)], "%c", 
                                               (int) (root->data + 'A'));
                   break;
    }
    localprinttree(root->right, level, str);
    if (closeflag) (void) strcat(str, ")");
}

/*****************************************************************************
*  Routine to create a new copy of a given tree:                  	     *
*****************************************************************************/
e2t_expr_node *e2t_copytree(const e2t_expr_node *root)
{
    e2t_expr_node *node;

    if (!root) return (e2t_expr_node *) NULL;

    node = e2t_malloc(sizeof(e2t_expr_node));
    switch(root->node_kind) {
    case ABS :
    case ARCSIN :
    case ARCCOS :
    case ARCTAN :
    case COS :
    case EXP :
    case LN :
    case LOG :
    case SIN :
    case SQR :
    case SQRT :
    case TAN : node -> node_kind = root -> node_kind;
               node -> right = e2t_copytree(root -> right);
               node -> left = NULL;
               return node;

    case DIV :
    case MINUS :
    case MULT :
    case NUMBER :
    case PARAMETER :
    case PLUS :
    case POWER :
    case UNARMINUS :
               node -> node_kind = root -> node_kind;
               if ((root -> node_kind == PARAMETER) ||
                   (root -> node_kind == NUMBER)) node -> data = root -> data;
               node -> right = e2t_copytree(root -> right);
               node -> left  = e2t_copytree(root -> left );
               return node;
    }
    return (e2t_expr_node *) NULL; /* Never get here (make lint quite...) */
}

/*****************************************************************************
*   Routine to evaluate a value of a given tree root and parameter.          *
*****************************************************************************/
double e2t_evaltree(const e2t_expr_node *root)
{
    double temp;

    switch(root->node_kind) {
    case ABS :    temp = e2t_evaltree(root->right);
                  return temp > 0 ? temp : -temp;
    case ARCSIN : return asin(e2t_evaltree(root->right));
    case ARCCOS : return acos(e2t_evaltree(root->right));
    case ARCTAN : return atan(e2t_evaltree(root->right));
    case COS :    return cos(e2t_evaltree(root->right));
    case EXP :    return exp(e2t_evaltree(root->right));
    case LN :     return log(e2t_evaltree(root->right));
    case LOG :    return log10(e2t_evaltree(root->right));
    case SIN :    return sin(e2t_evaltree(root->right));
    case SQR :    temp = e2t_evaltree(root->right); return temp*temp;
    case SQRT :   return sqrt(e2t_evaltree(root->right));
    case TAN :    return tan(e2t_evaltree(root->right));

    case DIV :    return e2t_evaltree(root->left) / e2t_evaltree(root->right);
    case MINUS :  return e2t_evaltree(root->left) - e2t_evaltree(root->right);
    case MULT :   return e2t_evaltree(root->left) * e2t_evaltree(root->right);
    case PLUS :   return e2t_evaltree(root->left) + e2t_evaltree(root->right);
    case POWER :  return pow(e2t_evaltree(root->left),
			     e2t_evaltree(root->right));
    case UNARMINUS : return -e2t_evaltree(root->right);

    case NUMBER :    return root->data;
    case PARAMETER : return GlobalParam[(int) (root->data)];
    }
    return 0; /* Never get here (only make lint quite...) */
}

/*****************************************************************************
*  Routine to generate the tree represent the derivative of tree root:       *
*****************************************************************************/
e2t_expr_node *e2t_derivtree(const e2t_expr_node *root, int param)
{
    int i, flag = TRUE;
    e2t_expr_node *node, *newnode;

    node = derivtree1(root, param);

    if (!glbl_deriv_error) {
        while (flag) {
            flag = FALSE;
            newnode = optimize(node, &flag);
            e2t_freetree(node); /* Release old tree area */
            node = newnode;
        }
        for (i=0; i<10; i++) { /* Do more loops - might optimize by shift */
            flag = FALSE;
            newnode = optimize(node, &flag);
            e2t_freetree(node); /* Release old tree area */
            node = newnode;
        }
    }
    return newnode;
}

/*****************************************************************************
*  Routine to generate non optimal derivative of the tree root :             *
*****************************************************************************/
static e2t_expr_node *derivtree1(const e2t_expr_node *root, int prm)
{
    e2t_expr_node *node1, *node2, *node3, *node4, *node_mul;

    node_mul = e2t_malloc(sizeof(e2t_expr_node));
    node_mul -> node_kind = MULT;

    switch(root->node_kind) {
    case ABS :    glbl_deriv_error = E2T_NO_ABS_DERIV_ERROR;
                  return NULL; /* No derivative ! */
    case ARCSIN : node_mul->left = gen1u2tree(PLUS , MINUS, -0.5,
					      e2t_copytree(root->right));
                  node_mul->right = derivtree1(root->right, prm);
                  return node_mul;
    case ARCCOS : node_mul->left = gen1u2tree(MINUS, MINUS, -0.5,
					      e2t_copytree(root->right));
                  node_mul->right = derivtree1(root->right, prm);
                  return node_mul;
    case ARCTAN : node_mul->left = gen1u2tree(PLUS , PLUS , -1.0,
					      e2t_copytree(root->right));
                  node_mul->right = derivtree1(root->right, prm);
                  return node_mul;
    case COS :    node1 = e2t_malloc(sizeof(e2t_expr_node));
                  node2 = e2t_malloc(sizeof(e2t_expr_node));
                  node1 -> node_kind = UNARMINUS;
                  node2 -> node_kind = SIN;
                  node2 -> right = e2t_copytree(root->right);
                  node1 -> left = node2 -> left = NULL;
                  node1 -> right = node2;
                  node_mul -> left = node1;
                  node_mul -> right = derivtree1(root->right, prm);
                  return node_mul;
    case EXP :    node1 = e2t_malloc(sizeof(e2t_expr_node));
                  node1 -> node_kind = EXP;
                  node1 -> left = NULL;
                  node1 -> right = e2t_copytree(root->right);
                  node_mul -> left = node1;
                  node_mul -> right = derivtree1(root->right, prm);
                  return node_mul;
    case LN :     node_mul -> node_kind = DIV; /* Not nice, but work ! */
                  node_mul -> right = e2t_copytree(root->right);
                  node_mul -> left = derivtree1(root->right, prm);
                  return node_mul;
    case LOG :    node1 = e2t_malloc(sizeof(e2t_expr_node));   
                  node2 = e2t_malloc(sizeof(e2t_expr_node));   
                  node1 -> node_kind = DIV;
                  node1 -> right = e2t_copytree(root->right);
                  node1 -> left = derivtree1(root->right, prm);
                  node2 -> node_kind = NUMBER;;
                  node2 -> data = log10(exp(1.0));
                  node_mul -> left = node1;
                  node_mul -> right = node2;
                  return node_mul;
    case SIN :    node1 = e2t_malloc(sizeof(e2t_expr_node));
                  node1 -> node_kind = COS;
                  node1 -> right = e2t_copytree(root->right);
                  node1 -> left = NULL;
                  node_mul -> left = node1;
                  node_mul -> right = derivtree1(root->right, prm);
                  return node_mul;
    case SQR :    node1 = e2t_malloc(sizeof(e2t_expr_node));   
                  node2 = e2t_malloc(sizeof(e2t_expr_node));   
                  node1 -> node_kind = NUMBER;
                  node1 -> right = node1 -> left = NULL;
                  node1 -> data = 2.0;
                  node2 -> node_kind = MULT;;
                  node2 -> right = derivtree1(root->right, prm);
                  node2 -> left  = e2t_copytree(root->right);
                  node_mul -> left = node1;
                  node_mul -> right = node2;
                  return node_mul;
    case SQRT :   node1 = e2t_malloc(sizeof(e2t_expr_node));   
                  node2 = e2t_malloc(sizeof(e2t_expr_node));   
                  node3 = e2t_malloc(sizeof(e2t_expr_node));   
                  node4 = e2t_malloc(sizeof(e2t_expr_node));   
                  node1 -> node_kind = NUMBER;
                  node1 -> right = node1 -> left = NULL;
                  node1 -> data = -0.5;
                  node2 -> node_kind = POWER;
                  node2 -> right = node1;
                  node2 -> left  = e2t_copytree(root->right);
                  node3 -> node_kind = NUMBER;
                  node3 -> right = node3 -> left = NULL;
                  node3 -> data = 0.5;
                  node4 -> node_kind = MULT;
                  node4 -> right = node2;
                  node4 -> left  = node3;
                  node_mul -> left = node4;
                  node_mul -> right = derivtree1(root->right, prm);
                  return node_mul;
    case TAN :    node1 = e2t_malloc(sizeof(e2t_expr_node));   
                  node2 = e2t_malloc(sizeof(e2t_expr_node));   
                  node1 -> node_kind = COS;
                  node1 -> left = NULL;
                  node1 -> right = e2t_copytree(root->right);
                  node2 -> node_kind = SQR;
                  node2 -> left = NULL;
                  node2 -> right = node1;
                  node_mul -> node_kind = DIV; /* Not noce, but work ! */
                  node_mul -> right = node2;
                  node_mul -> left = derivtree1(root->right, prm);
                  return node_mul;
    case DIV :    node1 = e2t_malloc(sizeof(e2t_expr_node));   
                  node2 = e2t_malloc(sizeof(e2t_expr_node));   
                  node3 = e2t_malloc(sizeof(e2t_expr_node));   
                  node4 = e2t_malloc(sizeof(e2t_expr_node));   
                  node1 -> node_kind = MULT;
                  node1 -> left  = e2t_copytree(root->left);
                  node1 -> right = derivtree1(root->right, prm);
                  node2 -> node_kind = MULT;
                  node2 -> left  = derivtree1(root->left, prm);
                  node2 -> right = e2t_copytree(root->right);
                  node3 -> node_kind = MINUS;
                  node3 -> right = node1;
                  node3 -> left = node2;
                  node4 -> node_kind = SQR;
                  node4 -> right = e2t_copytree(root->right);
                  node4 -> left  = NULL;
                  node_mul -> node_kind = DIV; /* Not nice, but work */
                  node_mul -> left = node3;
                  node_mul -> right = node4;
                  return node_mul;
    case MINUS :  node_mul -> node_kind = MINUS; /* Not nice, but work */
                  node_mul -> left = derivtree1(root->left, prm);
                  node_mul -> right = derivtree1(root->right, prm);
                  return node_mul;
    case MULT :   node1 = e2t_malloc(sizeof(e2t_expr_node));   
                  node2 = e2t_malloc(sizeof(e2t_expr_node));   
                  node1 -> node_kind = MULT;
                  node1 -> left  = e2t_copytree(root->left);
                  node1 -> right = derivtree1(root->right, prm);
                  node2 -> node_kind = MULT;
                  node2 -> left  = derivtree1(root->left, prm);
                  node2 -> right = e2t_copytree(root->right);
                  node_mul -> node_kind = PLUS; /* Not nice, but work */
                  node_mul -> left = node1;
                  node_mul -> right = node2;
                  return node_mul;
    case PLUS :   node_mul -> node_kind = PLUS; /* Not nice, but work */
                  node_mul -> left = derivtree1(root->left, prm);
                  node_mul -> right = derivtree1(root->right, prm);
                  return node_mul;
    case POWER :  if (root -> right -> node_kind != NUMBER) {
                      glbl_deriv_error = E2T_NONE_CONST_EXP_ERROR;
                      return NULL;
                  }
                  node1 = e2t_malloc(sizeof(e2t_expr_node));   
                  node2 = e2t_malloc(sizeof(e2t_expr_node));   
                  node3 = e2t_malloc(sizeof(e2t_expr_node));   
                  node4 = e2t_malloc(sizeof(e2t_expr_node));   
                  node1 -> node_kind = NUMBER;
                  node1 -> left  = node1 -> right = NULL;
                  node1 -> data = root -> right -> data - 1;
                  node2 -> node_kind = POWER;
                  node2 -> left  = e2t_copytree(root->left);
                  node2 -> right = node1;
                  node3 -> node_kind = NUMBER;
                  node3 -> left  = node3 -> right = NULL;
                  node3 -> data = root -> right -> data;
                  node4 -> node_kind = MULT;
                  node4 -> right = node2;
                  node4 -> left  = node3;
                  node_mul -> left = node4;
                  node_mul -> right = derivtree1(root->left, prm);
                  return node_mul;
                  
    case UNARMINUS :
                  node_mul -> node_kind = UNARMINUS;/* Not nice, but work ! */
                  node_mul -> right = derivtree1(root->right, prm);
                  node_mul -> left  = NULL;
                  return node_mul;

    case NUMBER : node_mul -> node_kind = NUMBER; /* Not nice, but work ! */
                  node_mul -> left = node_mul -> right = NULL;
                  node_mul -> data = 0.0;
                  return node_mul;
    case PARAMETER :
                  node_mul -> node_kind = NUMBER; /* Not nice, but work ! */
                  node_mul -> left = node_mul -> right = NULL;
                  if ((int) (root->data) == prm) 
                       node_mul -> data = 1.0;
                  else node_mul -> data = 0.0;
                  return node_mul;
    }
    return (e2t_expr_node *) NULL; /* Never get here (make lint quite...) */
}

/*****************************************************************************
*  Routine to generate a tree to the expression:                             *
*      SIGN1(1 SIGN2 SQR (EXPR)) ^ EXPONENT                                  *
*****************************************************************************/
static e2t_expr_node *gen1u2tree(int sign1, 
				 int sign2, 
				 double exponent, 
				 e2t_expr_node *expr)
{
    e2t_expr_node *node1, *node2, *node3, *node4, *node5, *node6;
    
    node1 = e2t_malloc(sizeof(e2t_expr_node));   
    node2 = e2t_malloc(sizeof(e2t_expr_node));   
    node3 = e2t_malloc(sizeof(e2t_expr_node));   
    node4 = e2t_malloc(sizeof(e2t_expr_node));   
    node5 = e2t_malloc(sizeof(e2t_expr_node));   
    node1 -> node_kind = NUMBER;
    node1 -> left  = node1 -> right = NULL;
    node1 -> data = 1.0;
    node2 -> node_kind = SQR;
    node2 -> right  = e2t_copytree(expr);
    node2 -> left = NULL;
    node3 -> node_kind = sign2;
    node3 -> left = node1;
    node3 -> right = node2;
    node4 -> node_kind = NUMBER;
    node4 -> data = exponent;
    node4 -> right = node4 -> left = NULL;
    node5 -> node_kind = POWER;
    node5 -> right = node4;
    node5 -> left = node3;
    if (sign1 == PLUS) return node5;
    else { /* Must be MINUS */
        node6 = e2t_malloc(sizeof(e2t_expr_node));   
        node6 -> node_kind = UNARMINUS;
        node6 -> left = NULL;
        node6 -> right = node5;
        return node6;
    }
}

/*****************************************************************************
*  Routine to optimize the binary tree :                                     *
* Note: the old tree is NOT modified. flag returns TRUE if optimized.        *
*****************************************************************************/
static e2t_expr_node *optimize(e2t_expr_node *root, int *flag)
{
    e2t_expr_node *node, *node2;

    if (!root) return NULL;
    if ((root -> node_kind != NUMBER) &&
        (!e2t_paramintree(root, E2T_PARAM_ALL))) { /* Expression is constant */
        *flag = TRUE;
        node = e2t_malloc(sizeof(e2t_expr_node));
        node -> node_kind = NUMBER;
        node -> data = e2t_evaltree(root);
        node -> right = node -> left = NULL;
        return node;
    }
    /* Shift in Mult or Plus: A+(B+C) -->  C+(A+B) */
    if (((root -> node_kind == PLUS) || (root -> node_kind == MULT)) &&
	(root -> node_kind == root -> right -> node_kind)) {
        node = root -> left;
	root -> left = root -> right -> right;
	root -> right -> right = root -> right -> left;
	root -> right -> left = node;
    }

    /* Shift in Mult or Plus: (A+B)+C -->  (C+A)+B */
    if (((root -> node_kind == PLUS) || (root -> node_kind == MULT)) &&
	(root -> node_kind == root -> left -> node_kind)) {
        node = root -> right;
	root -> right = root -> left -> left;
	root -> left -> left = root -> left -> right;
	root -> left -> right = node;
    }

    switch(root->node_kind) {
    case DIV :   if ((root -> right -> node_kind == NUMBER) &&
                     (root -> right -> data == 1.0)) {
                     *flag = TRUE;
                     return optimize(root -> left, flag);  /* Div by 1 */
                 }
                 if ((root -> left  -> node_kind == NUMBER) &&
                     (root -> left  -> data == 0.0)) {
                     *flag = TRUE;
                     return optimize(root -> left, flag);/* Div 0 - return 0 */
                 }
                 if (e2t_cmptree(root -> left, root -> right)) {
                     *flag = TRUE;
                     node = e2t_malloc(sizeof(e2t_expr_node));
                     node -> node_kind = NUMBER;
                     node -> data = 1.0;
                     node -> right = node -> left = NULL;
                     return node; /* f/f == 1 */
                 }
                 break;
    case MINUS : if ((root -> right -> node_kind == NUMBER) &&
                     (root -> right -> data == 0.0)) {
                     *flag = TRUE;
                     return optimize(root -> left, flag); /* Sub 0 */
                 }
                 if (e2t_cmptree(root -> left, root -> right)) {
                     *flag = TRUE;
                     node = e2t_malloc(sizeof(e2t_expr_node));
                     node -> node_kind = NUMBER;
                     node -> data = 0.0;
                     node -> right = node -> left = NULL;
                     return node; /* f-f == 0.0 */
                 }
                 if (root -> right -> node_kind == UNARMINUS) {
                     *flag = TRUE;
                     node = e2t_malloc(sizeof(e2t_expr_node));
                     node -> node_kind = PLUS;
                     node -> left = optimize(root -> left, flag);
                     node -> right = optimize(root -> right -> right, flag);
                     node2 = optimize(node, flag);  /* a-(-b) --> a+b */
		     e2t_freetree(node);
		     return node2;
                 }
                 break;
    case MULT :  if ((root -> right -> node_kind == NUMBER) &&
                     ((root -> right -> data == 1.0) ||
                      (root -> right -> data == 0.0))) {
                     *flag = TRUE;
                     if (root -> right -> data == 1.0)
                          return optimize(root -> left , flag);  /* Mul by 1 */
                     else return optimize(root -> right, flag);  /* Mul by 0 */
                 }
                 if ((root -> left  -> node_kind == NUMBER) &&
                     ((root -> left  -> data == 1.0) ||
                      (root -> left  -> data == 0.0))) {
                     *flag = TRUE;
                     if (root -> left -> data == 1.0)
		          return optimize(root -> right, flag);  /* Mul by 1 */
                     else return optimize(root -> left , flag);  /* Mul by 0 */
                 }
                 if (e2t_cmptree(root -> left, root -> right)) {
                     *flag = TRUE;
                     node = e2t_malloc(sizeof(e2t_expr_node));
                     node -> node_kind = SQR;
                     node -> right = optimize(root -> right, flag);
                     node -> left = NULL;
                     return node; /* f*f = f^2 */
                 }
                 break;
    case PLUS :	 if ((root -> right -> node_kind == NUMBER) &&
                     (root -> right -> data == 0.0)) {
                     *flag = TRUE;
                     return optimize(root -> left, flag);  /* Add 0 */
                 }
                 if ((root -> left  -> node_kind == NUMBER) &&
                     (root -> left  -> data == 0.0)) {
                     *flag = TRUE;
                     return optimize(root -> right, flag);  /* Add 0 */
                 }
                 if (e2t_cmptree(root -> left, root -> right)) {
                     *flag = TRUE;
                     node = e2t_malloc(sizeof(e2t_expr_node));
                     node -> node_kind = MULT;
                     node -> left = optimize(root -> right, flag);
                     node -> right = e2t_malloc(sizeof(e2t_expr_node));
                     node -> right -> node_kind = NUMBER;
                     node -> right -> data = 2.0;
                     node -> right -> left = node -> right -> right = NULL;
                     return node; /* f+f = f*2 */
                 }
                 if (root -> right -> node_kind == UNARMINUS) {
                     *flag = TRUE;
                     node = e2t_malloc(sizeof(e2t_expr_node));
                     node -> node_kind = MINUS;
                     node -> left = optimize(root -> left, flag);
                     node -> right = optimize(root -> right -> right, flag);
		     node2 = optimize(node, flag);  /* a+(-b) --> a-b */
		     e2t_freetree(node);
                     return node2;

                 }
                 if (root -> left  -> node_kind == UNARMINUS) {
                     *flag = TRUE;
                     node = e2t_malloc(sizeof(e2t_expr_node));
                     node -> node_kind = MINUS;
                     node -> left = optimize(root -> right, flag);
                     node -> right = optimize(root -> left -> right, flag);
                     node2 = optimize(node, flag);  /* (-a)+b --> b-a */
		     e2t_freetree(node);
                     return node2;
                 }
                 break;
    case POWER : if ((root -> right -> node_kind == NUMBER) &&
                     (root -> right -> data == 0.0)) {
                     *flag = TRUE;
                     node = e2t_malloc(sizeof(e2t_expr_node));
                     node -> node_kind = NUMBER;
                     node -> data = 1.0;
                     node -> right = node -> left = NULL;
                     return node; /* f^0 == 1 */
                 }
                 if ((root -> right -> node_kind == NUMBER) &&
                     (root -> right -> data == 1.0)) {
                     *flag = TRUE;
                     return optimize(root -> left, flag);  /* f^1 = f */
                 }
                 break;
    case UNARMINUS :
                 if (root -> right -> node_kind == UNARMINUS) {
                     *flag = TRUE;
                     return optimize(root -> right -> right, flag); /* --a=a */
                 }
                 break;
    default :;
    }

    /* If we are here - no optimization took place : */
    node = e2t_malloc(sizeof(e2t_expr_node));
    node -> node_kind = root -> node_kind;
    if ((root -> node_kind == PARAMETER) ||
        (root -> node_kind == NUMBER)) node -> data = root -> data;
    node -> right = optimize(root -> right, flag);
    node -> left  = optimize(root -> left , flag);
    return node;
}

/*****************************************************************************
*   Routine to compere two trees - for equality:                             *
* The trees are compered to be symbolically equal i.e. A*B == B*A !          *
*****************************************************************************/
int e2t_cmptree(const e2t_expr_node *root1, const e2t_expr_node *root2)
{
    if (root1->node_kind != root2->node_kind) return FALSE;

    switch(root1->node_kind) {
    case ABS :
    case ARCSIN :
    case ARCCOS :
    case ARCTAN :
    case COS :
    case EXP :
    case LN :
    case LOG :
    case SIN :
    case SQR :
    case SQRT :
    case TAN :
    case UNARMINUS : return e2t_cmptree(root1->right, root2->right);

    case MULT :      /* Note that A*B = B*A ! */
    case PLUS :      return ((e2t_cmptree(root1->right, root2->right) &&
                              e2t_cmptree(root1->left , root2->left )) ||
                             (e2t_cmptree(root1->right, root2->left ) &&
                              e2t_cmptree(root1->left , root2->right)));

    case DIV :
    case MINUS :
    case POWER :     return (e2t_cmptree(root1->right, root2->right) &&
                             e2t_cmptree(root1->left , root2->left ));

    case NUMBER :
    case PARAMETER : return (root1->data == root2->data);
    }
    return FALSE;           /* Never get here (only make lint quite...) */
}

/*****************************************************************************
*   Routine to test if the parameter is in the tree :                        *
* If parameter == E2T_PARAM_ALL then any parameter return TRUE.              *
*****************************************************************************/
int e2t_paramintree(const e2t_expr_node *root, int param)
{
    if (!root) return FALSE;

    switch(root->node_kind) {
    case ABS :
    case ARCSIN :
    case ARCCOS :
    case ARCTAN :
    case COS :
    case EXP :
    case LN :
    case LOG :
    case SIN :
    case SQR :
    case SQRT :
    case TAN :
    case UNARMINUS : return e2t_paramintree(root->right, param);

    case DIV :
    case MINUS :
    case MULT :
    case PLUS :
    case POWER :     return e2t_paramintree(root->right, param) ||
                            e2t_paramintree(root->left, param);

    case NUMBER :    return FALSE;
    case PARAMETER : if (param != E2T_PARAM_ALL)
                         return ((int) (root->data) == param);
                     else return TRUE;
    }
    return FALSE;           /* Never get here (only make lint quite...) */
}

/*****************************************************************************
*   Routine to free a tree - release all memory allocated by it.             *
*****************************************************************************/
void e2t_freetree(e2t_expr_node *root)
{
    if (!root) return;
    switch(root->node_kind) {
    case ABS :
    case ARCSIN :
    case ARCCOS :
    case ARCTAN :
    case COS :
    case EXP :
    case LN :
    case LOG :
    case SIN :
    case SQR :
    case SQRT :
    case TAN :
    case UNARMINUS : e2t_freetree(root->right);
                     e2t_free(root);
                     break;

    case DIV :
    case MINUS :
    case MULT :
    case PLUS :
    case POWER :     e2t_freetree(root->right);
                     e2t_freetree(root->left);
                     e2t_free(root);
                     break;

    case NUMBER :
    case PARAMETER : e2t_free(root);
                     break;
    }
}

/*****************************************************************************
*   Routine to return parsing error if happen one, zero elsewhere            *
*****************************************************************************/
int e2t_parserror(void)
{
    int temp;

    temp = e2t_parsing_error;
    e2t_parsing_error = 0;
    return temp;
}

/*****************************************************************************
*   Routine to return derivate error if happen one, zero elsewhere           *
*****************************************************************************/
int e2t_deriverror(void)
{
    int temp;

    temp = glbl_deriv_error;
    glbl_deriv_error = 0;
    return temp;
}

/*****************************************************************************
*  Routine to set the value of a parameter before evaluating it.             *
*****************************************************************************/
void e2t_setparamvalue(double Value, int Number)
{
    if ((Number >= 0) && (Number <= E2T_PARAM_Z)) GlobalParam[Number] = Value;
}

/*****************************************************************************
  Routine re parametrize tree.                                               *
*****************************************************************************/
static e2t_expr_node *reparametrize_tree(e2t_expr_node *tree, const e2t_expr_node *reparameter, int parameter) {
    if (!tree){
        return NULL;
    }

    if ((tree->node_kind == PARAMETER) & (tree->data == parameter)) {
        e2t_freetree(tree);
        return e2t_copytree(reparameter);
    } else {
        tree->left = reparametrize_tree(tree->left, reparameter, parameter);
        tree->right = reparametrize_tree(tree->right, reparameter, parameter);
        return tree;
    }
}
e2t_expr_node *e2t_treereparameter(const e2t_expr_node *tree, const e2t_expr_node *reparameter, int parameter) {
    e2t_expr_node * new_tree = e2t_copytree(tree);
    new_tree = reparametrize_tree(new_tree, reparameter, parameter);
    return new_tree;
}


/*****************************************************************************
  operations between trees                                                    *
*****************************************************************************/
// TREE op TREE
e2t_expr_node *e2t_trees_operation(const e2t_expr_node *left_tree, const e2t_expr_node *right_tree, int op_node_kind) {
    e2t_expr_node *root = e2t_malloc(sizeof(e2t_expr_node));
    root->node_kind = op_node_kind;
    root->left = e2t_copytree(left_tree);
    root->right = e2t_copytree(right_tree);
    return root;
}
// op(TREE)
e2t_expr_node *e2t_tree_operation(const e2t_expr_node *tree, int op_node_kind) {
    e2t_expr_node *root = e2t_malloc(sizeof(e2t_expr_node));
    root->node_kind = op_node_kind;
    root->right = e2t_copytree(tree);
    return root;
}

////////// TREE op TREE

e2t_expr_node *e2t_trees_op_division(const e2t_expr_node *left_tree, const e2t_expr_node *right_tree) {
    return e2t_trees_operation(left_tree, right_tree, DIV);
}

e2t_expr_node *e2t_trees_op_subtraction(const e2t_expr_node *left_tree, const e2t_expr_node *right_tree) {
    return e2t_trees_operation(left_tree, right_tree, MINUS);
}

e2t_expr_node *e2t_trees_op_multiplication(const e2t_expr_node *left_tree, const e2t_expr_node *right_tree) {
    return e2t_trees_operation(left_tree, right_tree, MULT);
}

e2t_expr_node *e2t_trees_op_addition(const e2t_expr_node *left_tree, const e2t_expr_node *right_tree) {
    return e2t_trees_operation(left_tree, right_tree, PLUS);
}

e2t_expr_node *e2t_trees_op_power(const e2t_expr_node *left_tree, const e2t_expr_node *right_tree) {
    return e2t_trees_operation(left_tree, right_tree, POWER);
}

////////// op(TREE)

e2t_expr_node *e2t_tree_op_sqr(const e2t_expr_node *tree) {
    return e2t_tree_operation(tree, SQR);
}

e2t_expr_node *e2t_tree_op_sqrt(const e2t_expr_node *tree) {
    return e2t_tree_operation(tree, SQRT);
}

e2t_expr_node *e2t_tree_op_unarminus(const e2t_expr_node *tree) {
    return e2t_tree_operation(tree, UNARMINUS);
}
