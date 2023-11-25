import copy
from enum import Enum

from brewparse import parse_program
from env_v3 import EnvironmentManager, Lambda
from intbase import InterpreterBase, ErrorType
from type_valuev3 import Type, Value, create_value, get_printable


class ExecStatus(Enum):
    CONTINUE = 1
    RETURN = 2


# Main interpreter class
class Interpreter(InterpreterBase):
    # constants
    NIL_VALUE = create_value(InterpreterBase.NIL_DEF)
    TRUE_VALUE = create_value(InterpreterBase.TRUE_DEF)
    COERCE_OPS = {"+", "-", "*", "/"}
    INTBOOL_OPS = {"==", "!=", "||", "&&"}
    BIN_OPS = {"+", "-", "*", "/", "==", "!=", ">", ">=", "<", "<=", "||", "&&"}

    # methods
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)
        self.trace_output = trace_output
        self.__setup_ops()

    # run a program that's provided in a string
    # usese the provided Parser found in brewparse.py to parse the program
    # into an abstract syntax tree (ast)
    def run(self, program):
        ast = parse_program(program)
        self.__set_up_function_table(ast)
        self.env = EnvironmentManager()
        main_func = self.__get_func_by_name("main", 0)
        self.__run_statements(main_func.get("statements"))

    def __set_up_function_table(self, ast):
        self.func_name_to_ast = {}
        for func_def in ast.get("functions"):
            func_name = func_def.get("name")
            num_params = len(func_def.get("args"))
            if func_name not in self.func_name_to_ast:
                self.func_name_to_ast[func_name] = {}
            self.func_name_to_ast[func_name][num_params] = func_def

    def __get_func_by_name(self, name, num_params):
        if name not in self.func_name_to_ast:
            super().error(ErrorType.NAME_ERROR, f"Function {name} not found")
        candidate_funcs = self.func_name_to_ast[name]
        if num_params not in candidate_funcs:
            super().error(
                ErrorType.NAME_ERROR,
                f"Function {name} taking {num_params} params not found",
            )
        return candidate_funcs[num_params]

    def __run_statements(self, statements):
        self.env.push()
        for statement in statements:
            if self.trace_output:
                print(statement)
            status = ExecStatus.CONTINUE
            if statement.elem_type == InterpreterBase.FCALL_DEF:
                self.__call_func(statement)
            elif statement.elem_type == "=":
                self.__assign(statement)
            elif statement.elem_type == InterpreterBase.RETURN_DEF:
                status, return_val = self.__do_return(statement)
            elif statement.elem_type == Interpreter.IF_DEF:
                status, return_val = self.__do_if(statement)
            elif statement.elem_type == Interpreter.WHILE_DEF:
                status, return_val = self.__do_while(statement)

            if status == ExecStatus.RETURN:
                self.env.pop()
                return (status, return_val)

        self.env.pop()
        return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)

    def __call_func(self, call_node):
        lambda_flag = False
        func_name = call_node.get("name")
        if func_name == "print":
            return self.__call_print(call_node)
        if func_name == "inputi":
            return self.__call_input(call_node)
        if func_name == "inputs":
            return self.__call_input(call_node)
        
        actual_args = call_node.get("args")
        
        # Check if the function we've called maps to a lambda
        # Check the environment for the function name
        closure_or_lambda = self.env.get(func_name) # THIS IS THE value object of type lambda
        # print(closure_or_lambda.get("lambda_ast"))
        
        #if isinstance(closure_or_lambda, Lambda): 
        if closure_or_lambda and closure_or_lambda.type() == Type.LAMBDA:
            # need to change the environment here to contain the captured variables
            lambda_flag = True
            #Since we are returning a Value object instead of a Lambda object now, we need to dereference to get the value
            func_ast = closure_or_lambda.value().get("lambda_ast")  
        elif closure_or_lambda and closure_or_lambda.type() == Type.FUNC:
            closure_flag = True
            print(closure_or_lambda.value())

            for key in closure_or_lambda.value().keys():
                func_ast = closure_or_lambda.value()[key]

            print("func_ast", func_ast)
        elif closure_or_lambda:
            super().error(
                ErrorType.TYPE_ERROR,
                "Can't call function with no closure.",)
        else:
            func_ast = self.__get_func_by_name(func_name, len(actual_args))

        # IF WE HAVE A LAMBDA, WE NEED TO EVALUATE THE FUNCTIONS AND GET THE LAMBDA ENVIRONMENT
        if lambda_flag:
            self.env.environment.append(closure_or_lambda.value().get("env")) # This gets the flattened environment with all of the enclosing scopes
        else:
            self.env.push()
            # formal_args = func_ast.get("args")
        
       
        formal_args = func_ast.get("args")
       
        
        if len(actual_args) != len(formal_args):
            if lambda_flag:
                super().error(
                ErrorType.TYPE_ERROR,
                f"Lambda with {len(actual_args)} args not found",
                )
            elif closure_flag:
                super().error(
                ErrorType.TYPE_ERROR,
                f"Function closure with {len(actual_args)} args not found",
                )
            else:
                super().error(
                ErrorType.NAME_ERROR,
                f"Function {func_ast.get('name')} with {len(actual_args)} args not found",
                )

        ref_list = [] # initialize list of references
        for formal_ast, actual_ast in zip(formal_args, actual_args):
            arg_name = formal_ast.get("name")
            result = copy.deepcopy(self.__eval_expr(actual_ast))

            # print("arg_name: ", arg_name)
            # print("result: ", result.value())
            # print ("actual_ast.get(name): ", actual_ast.get("name"))
    
            # Check if we are passing by reference
            if formal_ast.elem_type == Interpreter.REFARG_DEF and actual_ast.elem_type == Interpreter.VAR_DEF: #If our definition is pass by reference and the value passed in is a variable
                result = self.__eval_expr(actual_ast)
                if (self.env.get(actual_ast.get("name")) == None):
                    super().error(
                    ErrorType.NAME_ERROR,
                    f"Variable {actual_ast.get('name')} not found",
                    )
                self.env.create(arg_name, result) # We set the arg_name to the reseult in the environment
                ref_list.append([arg_name, actual_ast.get("name"), result]) # append ref arg, reference, and value to the ref_list
            else:
                self.env.create(arg_name, result)

           
        _, return_val = self.__run_statements(func_ast.get("statements"))

        for ref in ref_list:
            ref[2] = self.env.get(ref[0]) # Set the value to the passed in ref arg value

        self.env.pop()

        for ref in ref_list:
            #print(ref)
            self.env.set(ref[1], ref[2]) # set the value of the actual arg in the environment  

        return return_val

    def __call_print(self, call_ast):
        output = ""
        for arg in call_ast.get("args"):
            result = self.__eval_expr(arg)  # result is a Value object
            output = output + get_printable(result)
        super().output(output)
        return Interpreter.NIL_VALUE

    def __call_input(self, call_ast):
        args = call_ast.get("args")
        if args is not None and len(args) == 1:
            result = self.__eval_expr(args[0])
            super().output(get_printable(result))
        elif args is not None and len(args) > 1:
            super().error(
                ErrorType.NAME_ERROR, "No inputi() function that takes > 1 parameter"
            )
        inp = super().get_input()
        if call_ast.get("name") == "inputi":
            return Value(Type.INT, int(inp))
        if call_ast.get("name") == "inputs":
            return Value(Type.STRING, inp)

    def __assign(self, assign_ast):
        var_name = assign_ast.get("name")
        #print(assign_ast.get("expression"))
        value_obj = self.__eval_expr(assign_ast.get("expression"))
        
        # var_val = self.env.get(var_name) #get the value of the local variable from the environment
        # print ("var_val: ", var_val)
        # if isinstance(var_val, tuple):
        #     var_name = var_val[1]

        # print ("var_name: ", var_name)
        # print ("value_obj: ", value_obj.value())
        self.env.set(var_name, value_obj)

    def __eval_expr(self, expr_ast):
        # print("here expr")
        # print("type: " + str(expr_ast.elem_type))
        if expr_ast.elem_type == InterpreterBase.NIL_DEF:
            # print("getting as nil")
            return Interpreter.NIL_VALUE
        if expr_ast.elem_type == InterpreterBase.INT_DEF:
            return Value(Type.INT, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.STRING_DEF:
            # print("getting as str")
            return Value(Type.STRING, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.BOOL_DEF:
            return Value(Type.BOOL, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.VAR_DEF:
            var_name = expr_ast.get("name")
            # Check if the variable name is also a function name
            # If so, return function variable??
            if var_name in self.func_name_to_ast:
                if self.is_overloaded(var_name):
                    super().error(ErrorType.NAME_ERROR, f"Cannot assign a variable to an overloaded function")
                return Value(Type.FUNC, self.func_name_to_ast[var_name])
            val = self.env.get(var_name)
            ### DEBUGGING REF
            # if isinstance(val, tuple) and val[0] == "ref":
            #     val = val[1]
            if val is None:
                super().error(ErrorType.NAME_ERROR, f"Variable {var_name} not found")
            return val
        if expr_ast.elem_type == InterpreterBase.FCALL_DEF:
            return self.__call_func(expr_ast)
        if expr_ast.elem_type in Interpreter.BIN_OPS:
            return self.__eval_op(expr_ast)
        if expr_ast.elem_type == Interpreter.NEG_DEF:
            #print (expr_ast.get("op1").elem_type)
            return self.__eval_unary(expr_ast, Type.INT, lambda x: -1 * x)
        if expr_ast.elem_type == Interpreter.NOT_DEF:
            return self.__eval_unary(expr_ast, Type.BOOL, lambda x: not x)
        if expr_ast.elem_type == Interpreter.LAMBDA_DEF:
            return self.__set_lambda(expr_ast)
        # We want to check if the element is a lambda
        # if it is, treat it like a function maybe? But we also need to make sure we're instantiating it in the environment

        #BRAINSTORMING:
        # Maybe when calling y(10) on a variable y that is a closure, we need to check if the value of the variable is a lambda node
        # If it is, we turn the variable into a function that takes in the lambda and its parameter(s) as parameters and then evaluates the lambda in the function
        # and returns it.

    def is_overloaded(self, var_name):
        if len(self.func_name_to_ast[var_name]) > 1:
            return True
        else:
            return False
        #     if entry is var_name:
                
        # if count > 1:
        #     return True
        # else:
        #     return False
    


    def __set_lambda(self, lambda_ast):
        #curr_env = self.env[-1] # get the current environment DEEP COPY
        curr_env = copy.deepcopy(self.env)
        # Not sure we need to deepcopy here
        # print ("curr_env: ", curr_env)
        flat_curr_env = self.env.flatten_env(curr_env)
        # print ("flat_curr_env: ", flat_curr_env)
        # return (lambda_ast, curr_env) #return a tuple of the expression ast and the current environment with all the variables
        return Value(Type.LAMBDA, Lambda(lambda_ast, flat_curr_env))
        #return Lambda(lambda_ast, flat_curr_env)


    def __eval_op(self, arith_ast):
        left_value_obj = self.__eval_expr(arith_ast.get("op1"))
        right_value_obj = self.__eval_expr(arith_ast.get("op2"))

        #Handle functions here
        # if right_value_obj = 




        if arith_ast.elem_type in Interpreter.COERCE_OPS:
        ## COERCE BOOL TO INT
            left_value_obj, right_value_obj = self.__coerce_bool(arith_ast, left_value_obj, right_value_obj)
        
        if arith_ast.elem_type in Interpreter.INTBOOL_OPS:
        ## COERCE INT TO BOOL
            left_value_obj, right_value_obj = self.__coerce_int(arith_ast, left_value_obj, right_value_obj)

        if not self.__compatible_types(
            arith_ast.elem_type, left_value_obj, right_value_obj
        ):
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible types for {arith_ast.elem_type} operation",
            )
        if arith_ast.elem_type not in self.op_to_lambda[left_value_obj.type()]:
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible operator {arith_ast.elem_type} for type {left_value_obj.type()}",
            )
        f = self.op_to_lambda[left_value_obj.type()][arith_ast.elem_type]
        # print("here eval")
        # print(arith_ast)
        # print("evaluating " + str(left_value_obj.type()) + " " + str(arith_ast.elem_type))
        # print("obj left: " + str(left_value_obj.value()))
        return f(left_value_obj, right_value_obj)

    def __compatible_types(self, oper, obj1, obj2):
        # DOCUMENT: allow comparisons ==/!= of anything against anything
        if oper in ["==", "!="]:
            return True
        #if oper in ["==", "!="] and obj1.type() == Type.INT
        return obj1.type() == obj2.type()

    def __eval_unary(self, arith_ast, t, f):
        #print (arith_ast.get("op1").get("type"))
        # if arith_ast.get("op1").elem_type == InterpreterBase.FCALL_DEF:
        #     super().error(
        #         ErrorType.TYPE_ERROR,
        #         f"Incompatible type for {arith_ast.elem_type} operation",
        #     )
            
        value_obj = self.__eval_expr(arith_ast.get("op1"))
        
        # INT TO BOOL COERSION
        if arith_ast.elem_type == Interpreter.NOT_DEF and value_obj.type() == Type.INT:
            value_obj = Value(Type.BOOL, True if value_obj.value() != 0 else False)

        #print (value_obj.type())

        if value_obj.type() != t:
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible type for {arith_ast.elem_type} operation",
            )
        return Value(t, f(value_obj.value()))

    def __setup_ops(self):
        self.op_to_lambda = {}
        # set up operations on integers
        self.op_to_lambda[Type.INT] = {}
        self.op_to_lambda[Type.INT]["+"] = lambda x, y: Value(
            x.type(), x.value() + y.value()
        )
        self.op_to_lambda[Type.INT]["-"] = lambda x, y: Value(
            x.type(), x.value() - y.value()
        )
        self.op_to_lambda[Type.INT]["*"] = lambda x, y: Value(
            x.type(), x.value() * y.value()
        )
        self.op_to_lambda[Type.INT]["/"] = lambda x, y: Value(
            x.type(), x.value() // y.value()
        )
        self.op_to_lambda[Type.INT]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.INT]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )
        self.op_to_lambda[Type.INT]["<"] = lambda x, y: Value(
            Type.BOOL, x.value() < y.value()
        )
        self.op_to_lambda[Type.INT]["<="] = lambda x, y: Value(
            Type.BOOL, x.value() <= y.value()
        )
        self.op_to_lambda[Type.INT][">"] = lambda x, y: Value(
            Type.BOOL, x.value() > y.value()
        )
        self.op_to_lambda[Type.INT][">="] = lambda x, y: Value(
            Type.BOOL, x.value() >= y.value()
        )
        #  set up operations on strings
        self.op_to_lambda[Type.STRING] = {}
        self.op_to_lambda[Type.STRING]["+"] = lambda x, y: Value(
            x.type(), x.value() + y.value()
        )
        self.op_to_lambda[Type.STRING]["=="] = lambda x, y: Value(
            Type.BOOL, x.value() == y.value()
        )
        self.op_to_lambda[Type.STRING]["!="] = lambda x, y: Value(
            Type.BOOL, x.value() != y.value()
        )
        #  set up operations on bools
        self.op_to_lambda[Type.BOOL] = {}
        self.op_to_lambda[Type.BOOL]["&&"] = lambda x, y: Value(
            x.type(), x.value() and y.value()
        )
        self.op_to_lambda[Type.BOOL]["||"] = lambda x, y: Value(
            x.type(), x.value() or y.value()
        )
        self.op_to_lambda[Type.BOOL]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.BOOL]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )

        #  set up operations on nil
        self.op_to_lambda[Type.NIL] = {}
        self.op_to_lambda[Type.NIL]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.NIL]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )

        # set up operations on lambda
        self.op_to_lambda[Type.LAMBDA] = {}
        self.op_to_lambda[Type.LAMBDA]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value() #CAN WE COMPARE VALUES OF LAMBDAS
        )
        self.op_to_lambda[Type.LAMBDA]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )

        # set up operations on functions
        self.op_to_lambda[Type.FUNC] = {}
        self.op_to_lambda[Type.FUNC]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value() #CAN WE COMPARE VALUES OF LAMBDAS
        )
        self.op_to_lambda[Type.FUNC]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )


    def __do_if(self, if_ast):
        cond_ast = if_ast.get("condition")
        if cond_ast.elem_type == Type.INT:
            cond_ast = Value
        
        result = self.__eval_expr(cond_ast)

        # COERCE INT TO BOOL
        if result.type() == Type.INT:
            result = Value(Type.BOOL, True if result.value() != 0 else False)

        if result.type() != Type.BOOL:
            super().error(
                ErrorType.TYPE_ERROR,
                "Incompatible type for if condition",
            )
        if result.value():
            statements = if_ast.get("statements")
            status, return_val = self.__run_statements(statements)
            return (status, return_val)
        else:
            else_statements = if_ast.get("else_statements")
            if else_statements is not None:
                status, return_val = self.__run_statements(else_statements)
                return (status, return_val)

        return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)

    def __do_while(self, while_ast):
        cond_ast = while_ast.get("condition")
        run_while = Interpreter.TRUE_VALUE

        while run_while.value():
            run_while = self.__eval_expr(cond_ast)

            #COERCE INT TO BOOL
            if run_while.type() == Type.INT:
                run_while = Value(Type.BOOL, True if run_while.value() != 0 else False)

            if run_while.type() != Type.BOOL:
                super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible type for while condition",
                )
            if run_while.value():
                statements = while_ast.get("statements")
                status, return_val = self.__run_statements(statements)
                if status == ExecStatus.RETURN:
                    return status, return_val

        return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)

    def __do_return(self, return_ast):
        expr_ast = return_ast.get("expression")
        if expr_ast is None:
            return (ExecStatus.RETURN, Interpreter.NIL_VALUE)
        value_obj = copy.deepcopy(self.__eval_expr(expr_ast))
        return (ExecStatus.RETURN, value_obj)
    
    def __coerce_bool(self, arith_ast, left_value_obj, right_value_obj):
        #if arith_ast.elem_type in Interpreter.COERCE_OPS:
            if left_value_obj.type() == Type.BOOL:
                left_value_obj = Value(Type.INT, 1 if left_value_obj.value() == True else 0)
            if right_value_obj.type() == Type.BOOL:
                right_value_obj = Value(Type.INT, 1 if right_value_obj.value() == True else 0)
            return left_value_obj, right_value_obj

    def __coerce_int(self, arith_ast, left_value_obj, right_value_obj):
        #if arith_ast.elem_type in Interpreter.INTBOOL_OPS:
            if left_value_obj.type() == Type.INT:
                left_value_obj = Value(Type.BOOL, True if left_value_obj.value() != 0 else False)
            if right_value_obj.type() == Type.INT:
                right_value_obj = Value(Type.BOOL, True if right_value_obj.value() != 0 else False)
            return left_value_obj, right_value_obj
            # THIS MIGHT BE BUGGY, WHAT HAPPENS IF WE RETURN NONE OR SOMETHING


def main():
    program_source = """
func foo(f) {
 return f;
}


func main() {
 x = foo;
 x(1,2);
}

        
        """

    interpreter = Interpreter()
    interpreter.run(program_source)

if __name__ == "__main__":
    main()


# Test first class functions
# def main():
#     program_source = """
#         func foo() {
#             print("Hello World!");
#         }

#         func main() {
#             x = foo;
#             if (x == foo){
#                 print ("YOOOOO");
#             }
#         }
        
#         """

#     interpreter = Interpreter()
#     interpreter.run(program_source)

# if __name__ == "__main__":
#     main()

# def main():
#     program_source = """
#         func bar(ref c) {
#             c = c + 1;
#         }

#         func foo(ref a) {
#             a = a + 10;
#             bar(a);
#         }

#         func main() {
#             b = 5;
#             foo(b);
#             print(b);
#         }
        
#         """

#     interpreter = Interpreter()
#     interpreter.run(program_source)

# if __name__ == "__main__":
#     main()
# def main():
#     program_source = """
#         func main() {
#             a = "what";
#             x = lambda (ref f) {
#             print(a); 
#             print(f); 
#             f = "something else"; 
#             print(a); 
#             print(f); 
#             };

#             x(a); 
#         }
        
#         """

#     interpreter = Interpreter()
#     interpreter.run(program_source)

# if __name__ == "__main__":
#     main()

# def main():
#     program_source = """
#         func foo(f1, ref f2) {
#             f1(); 
#             f2(); 
#         }

#         func main() {
#             x = 0;
#             lam1 = lambda() { x = x + 1; print(x); };
#             lam2 = lambda() { x = x + 1; print(x); };
#             foo(lam1, lam2);
#             lam1(); 
#             lam2(); 
#         }
        
#         """

#     interpreter = Interpreter()
#     interpreter.run(program_source)

# if __name__ == "__main__":
#     main()

# def main():
#     program_source = """
#         func foo() {
#             return 5;
#         }
        
#         func bar() {
#             x = 20;
#             y = 10;
#         }
        
#         func main() {
#           print("hello");

#           a = true;
#           b = a + 1;
#           print (b);
#           print (b - 3);
#           print (b / 2);
#           print (b * 2);

#           c = 5;
#           print (false || 5);
#           print (true && 1);
#           print (false && 1);
#           print (true == 1);
#           print (false == 0);

#           if (c == true){
#             print ("c = true");
#           }
#           else{
#             print ("c = false");
#           }

#           d = 0;
#           if (!d){
#            print ("IT'S WORKING");
#           }

#           x = foo;
#           print (x);


          
#         }
        
#         """

#     interpreter = Interpreter()
#     interpreter.run(program_source)

# if __name__ == "__main__":
#     main()