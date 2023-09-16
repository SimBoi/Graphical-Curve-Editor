
/*****************************************************************************
* The global constants - should be available to every body using expr2tree   *
*****************************************************************************/
#define E2T_PARAM_A    0   /* Make life easier is usage */
#define E2T_PARAM_B    1
#define E2T_PARAM_C    2
#define E2T_PARAM_D    3
#define E2T_PARAM_E    4
#define E2T_PARAM_F    5
#define E2T_PARAM_G    6
#define E2T_PARAM_H    7
#define E2T_PARAM_I    8
#define E2T_PARAM_J    9
#define E2T_PARAM_K    10
#define E2T_PARAM_L    11
#define E2T_PARAM_M    12
#define E2T_PARAM_N    13
#define E2T_PARAM_O    14
#define E2T_PARAM_P    15
#define E2T_PARAM_Q    16
#define E2T_PARAM_R    17
#define E2T_PARAM_S    18
#define E2T_PARAM_T    19
#define E2T_PARAM_U    20
#define E2T_PARAM_V    21
#define E2T_PARAM_W    22
#define E2T_PARAM_X    23
#define E2T_PARAM_Y    24
#define E2T_PARAM_Z    25
#define E2T_PARAM_Z1   26  /* Number of variables */
#define E2T_PARAM_ALL  -1  /* Match all E2T_PARAMs is searches */

extern int e2t_parsing_error;

/*****************************************************************************
* The basic expression tree node definition:                                 *
*****************************************************************************/
typedef struct e2t_expr_node {
     struct e2t_expr_node *right, *left;
     int node_kind;
     double data;
} e2t_expr_node;

/*****************************************************************************
* Error numbers as located during the parsing process:                       *
*****************************************************************************/
#define E2T_UNDEF_TOKEN_ERROR  1
#define E2T_PARAMATCH_ERROR    2
#define E2T_EOL_ERROR          3
#define E2T_REAL_MESS_ERROR    4
#define E2T_SYNTAX_ERROR       5
#define E2T_STACK_OV_ERROR     6
#define E2T_ONE_OPERAND_ERROR  7
#define E2T_TWO_OPERAND_ERROR  8
#define E2T_PARAM_EXPECT_ERROR 9

/*****************************************************************************
* Error numbers as located during the derivation creation:                   *
*****************************************************************************/
#define E2T_NONE_CONST_EXP_ERROR 1
#define E2T_NO_ABS_DERIV_ERROR   2

/*****************************************************************************
* Function prototypes:							     *
*****************************************************************************/

#ifdef __cplusplus
extern "C" {
#endif

e2t_expr_node *e2t_expr2tree(const char s[]);
e2t_expr_node *e2t_treereparameter(const e2t_expr_node *tree, const e2t_expr_node *reparameter, int parameter);
void e2t_printtree(const e2t_expr_node *root, char *str);
e2t_expr_node *e2t_copytree(const e2t_expr_node *root);
double     e2t_evaltree(const e2t_expr_node *root);
e2t_expr_node *e2t_derivtree(const e2t_expr_node *root, int param);
int        e2t_cmptree(const e2t_expr_node *root1, const e2t_expr_node *root2);
int        e2t_paramintree(const e2t_expr_node *root, int param);
void       e2t_freetree(e2t_expr_node *root);
int        e2t_parserror();
int        e2t_deriverror();
void       e2t_setparamvalue(double Value, int Number);

e2t_expr_node *e2t_treereparameter(const e2t_expr_node *tree, const e2t_expr_node *reparameter, int parameter);
e2t_expr_node *e2t_trees_op_division(const e2t_expr_node *left_tree, const e2t_expr_node *right_tree);
e2t_expr_node *e2t_trees_op_subtraction(const e2t_expr_node *left_tree, const e2t_expr_node *right_tree);
e2t_expr_node *e2t_trees_op_multiplication(const e2t_expr_node *left_tree, const e2t_expr_node *right_tree);
e2t_expr_node *e2t_trees_op_addition(const e2t_expr_node *left_tree, const e2t_expr_node *right_tree);
e2t_expr_node *e2t_trees_op_power(const e2t_expr_node *left_tree, const e2t_expr_node *right_tree);
e2t_expr_node *e2t_tree_op_sqr(const e2t_expr_node *tree);
e2t_expr_node *e2t_tree_op_sqrt(const e2t_expr_node *tree);
e2t_expr_node *e2t_tree_op_unarminus(const e2t_expr_node *tree);

#ifdef __cplusplus
}
#endif
