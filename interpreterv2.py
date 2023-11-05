from env_v2 import EnvironmentManager, EnvironmentStack
from type_valuev1 import Type, Value, create_value, get_printable
from intbase import InterpreterBase, ErrorType
from brewparse import parse_program


# Main interpreter class
class Interpreter(InterpreterBase):
    # constants
    NIL_VALUE = create_value(InterpreterBase.NIL_DEF)
    BIN_OPS = {"+", "-", "*", "/", "neg", "!"}
    BOOL_OPS = {"==", "!=", ">", "<", ">=", "<=", "||", "&&"}

    # methods
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)
        self.trace_output = trace_output
        self.__setup_ops()
        # self.is_returned = False

    # run a program that's provided in a string
    # usese the provided Parser found in brewparse.py to parse the program
    # into an abstract syntax tree (ast)
    def run(self, program):
        ast = parse_program(program)
        self.__set_up_function_table(ast)
        main_func = self.__get_func_by_name("main", 0)
        self.env = EnvironmentManager()
        self.env_stack = EnvironmentStack(self.env)
        self.__run_statements(main_func.get("statements"))

    def __set_up_function_table(self, ast):
        self.func_name_to_ast = {}
        for func_def in ast.get("functions"):
            if func_def.get("name") in self.func_name_to_ast:
                self.func_name_to_ast[func_def.get("name")].append(func_def)
            else:
                self.func_name_to_ast[func_def.get("name")] = [func_def]

    def __get_func_by_name(self, name, arg_count):
        # print("dict", self.func_name_to_ast)
        # print("name", name)
        if name not in self.func_name_to_ast:
            super().error(ErrorType.NAME_ERROR, f"Function {name} not found")
        else:
            for func in self.func_name_to_ast[name]:
                # print("arg count", len(func.get("args")))
                if len(func.get("args")) == arg_count:
                    return func
                
            super().error(ErrorType.NAME_ERROR, f"Function {name} has wrong number of args")

        #return self.func_name_to_ast[name]

    def __run_statements(self, statements):
      
        # all statements of a function are held in arg3 of the function AST node
        return_val = None
        for statement in statements:
            
            if self.trace_output:
                print(statement)   
            if statement.elem_type == InterpreterBase.FCALL_DEF:
                self.__call_func(statement)
            elif statement.elem_type == "=":
                self.__assign(statement)
            elif statement.elem_type == InterpreterBase.IF_DEF:
                return_val =  self.__run_if(statement)
            elif statement.elem_type == InterpreterBase.WHILE_DEF:
                return_val =  self.__run_while(statement)
            elif statement.elem_type == InterpreterBase.RETURN_DEF:
                return_val =  self.__run_ret(statement)
                #break

            if return_val != None:
                return return_val

    def __run_if(self, statement):
        #ADD SCOPING FOR IF
        self.if_env = EnvironmentManager() # Create the environment for if
        self.env_stack.push(self.if_env) # Push the environment/scope to the stack

        return_if_else = None
        cond = self.__eval_expr(statement.get("condition"))
        if (cond.type() != Type.BOOL):
            super().error(ErrorType.TYPE_ERROR, f"Invalid if condition")
        if cond.value():
            st_list = statement.get("statements")
            return_if_else = self.__run_statements(st_list)
        else:
            # if no else statements, return None
            else_list = statement.get("else_statements") 
            if else_list is not None:
                return_if_else = self.__run_statements(else_list)
        
        #Make sure we have a return value to return (i.e. not assignment)
        if return_if_else is not None:
            self.env_stack.pop() # pop the scope from the stack
            return return_if_else

            #OLD CODE (doesn't work)
            # if statement.get("else_statements") == None:
            #     return 
            # else:
            #     else_list = statement.get("else_statements")
            #     return self.__run_statements(else_list)
        self.env_stack.pop()
    
    def __run_while(self, statement):
        #ADD SCOPING

        self.while_env = EnvironmentManager() # Create the environment for if
        self.env_stack.push(self.while_env) # Push the environment/scope to the stack


        return_val = None
        cond = self.__eval_expr(statement.get("condition"))
        if (cond.type() != Type.BOOL):
            super().error(ErrorType.TYPE_ERROR, f"Invalid while condition")
        while cond.value():
            #print("while loop condition is TRUE")
            st_list = statement.get("statements")
            return_val = self.__run_statements(st_list)
            if return_val != None:
                self.env_stack.pop() # pop the scope from the stack
                return return_val
            cond = self.__eval_expr(statement.get("condition"))
        
        self.env_stack.pop()
            #return return_val
        
    def __run_ret(self, return_st):
        return_val = self.__eval_expr(return_st.get("expression"))
        #print("Returning Val:", return_val.value())
        return return_val
    
        

    def __call_func(self, call_node):
        # #Scoping initialization
        # self.func_env = EnvironmentManager() # Create the environment for func calls
        # self.env_stack.push(self.func_env) # Push the environment/scope to the stack
        #TOO EARLY

        func_name = call_node.get("name")
        if func_name == "print":
            return self.__call_print(call_node)
        if func_name == "inputi" or func_name == "inputs":
            return self.__call_input(call_node)
        
        #Scoping initialization
        self.func_env = EnvironmentManager() # Create the environment for func calls
        self.env_stack.push(self.func_env) # Push the environment/scope to the stack

        num_args = len(call_node.get("args"))
        func_def = self.__get_func_by_name(func_name, num_args)
        func_def_args =  func_def.get('args')
        func_called_args = call_node.get('args')

        # if len(func_def_args) != len(func_called_args):
        #     super().error(ErrorType.NAME_ERROR, f"Invalid argument length")
        
        for d_arg, c_arg in zip(func_def_args, func_called_args): # create a tuple to loop and access both the arguments in the function def and function call at the same time
            def_arg = d_arg.get('name')
            call_arg = self.__eval_expr(c_arg)
            # print(def_arg)
            # print(call_arg)
            self.env_stack.top().set(def_arg, call_arg)
        
        func_statements = func_def.get('statements')
        return_value = self.__run_statements(func_statements)


        if return_value != None:
            self.env_stack.pop()
            return return_value
        
        self.env_stack.pop()
        return Interpreter.NIL_VALUE




    def __call_print(self, call_ast):
        output = ""
        for arg in call_ast.get("args"):
            result = self.__eval_expr(arg)  # result is a Value object
            #print("print result", result)
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
        # we can support inputs here later
        if call_ast.get("name") == "inputs":
            return Value(Type.STRING, str(inp))

    def __assign(self, assign_ast):
        var_name = assign_ast.get("name")
        value_obj = self.__eval_expr(assign_ast.get("expression"))
        self.env_stack.set(var_name, value_obj) #NEW TODAY

    def __eval_expr(self, expr_ast):
        if expr_ast == None:
            return Value(Type.NIL, None)
        if expr_ast.elem_type == InterpreterBase.BOOL_DEF: # NEW
            return Value(Type.BOOL, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.INT_DEF:
            return Value(Type.INT, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.NIL_DEF or expr_ast.elem_type == None:
            return Value(Type.NIL, None)
        if expr_ast.elem_type == InterpreterBase.STRING_DEF:
            return Value(Type.STRING, expr_ast.get("val"))
        
        if expr_ast.elem_type == InterpreterBase.VAR_DEF:
            var_name = expr_ast.get("name")
            val = self.env_stack.get(var_name)
            if val is None:
                super().error(ErrorType.NAME_ERROR, f"Variable {var_name} not found")
            return val
        if expr_ast.elem_type == InterpreterBase.FCALL_DEF:
            return self.__call_func(expr_ast)
        if expr_ast.elem_type in Interpreter.BIN_OPS:
            return self.__eval_op(expr_ast)
        if expr_ast.elem_type in Interpreter.BOOL_OPS:
            return self.__eval_op(expr_ast)
        # if expr_ast.elem_type == InterpreterBase.NEG_DEF:
        #     return self.__eval_op(expr_ast)
         
        
        # if elem type is other operation

    def __eval_op(self, arith_ast):
        left_value_obj = self.__eval_expr(arith_ast.get("op1"))
        op_type = arith_ast.elem_type

        if op_type == "neg" or op_type == "!":
            # Handle incorrect types for negative and logical not operator
            if op_type == "neg" and (left_value_obj.type() != Type.INT): #or isinstance(left_value_obj.value(), bool)): # NEW TODAY but I think this already is checked
                super().error(ErrorType.TYPE_ERROR, f"Cannot take the negative of a non-integer value")
            if op_type == "!" and left_value_obj.type() != Type.BOOL:
                super().error(ErrorType.TYPE_ERROR, f"Cannot perform 'not' operation on a non-boolean value")
            #Just return the left operand for unary operations
            f = self.op_to_lambda[left_value_obj.type()][arith_ast.elem_type]
            return f(left_value_obj)

        right_value_obj = self.__eval_expr(arith_ast.get("op2"))

        # is and not equal comparison handling
        if arith_ast.elem_type == "==" or arith_ast.elem_type == "!=": 
            f = self.op_to_lambda[left_value_obj.type()][arith_ast.elem_type]
            # print (left_value_obj.type())
            # print (right_value_obj.type())
            return f(left_value_obj, right_value_obj)
        if left_value_obj.type() != right_value_obj.type():
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible types for {arith_ast.elem_type} operation",
            )
        # if arith_ast.elem_type == ">" or arith_ast.elem_type == "<" or arith_ast.elem_type == "<=" or arith_ast.elem_type == ">=": #NEW
        #     f = self.op_to_lambda[left_value_obj.type()][arith_ast.elem_type]

        if arith_ast.elem_type not in self.op_to_lambda[left_value_obj.type()]:
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible operator {arith_ast.elem_type} for type {left_value_obj.type()}",
            )
        f = self.op_to_lambda[left_value_obj.type()][arith_ast.elem_type]
        return f(left_value_obj, right_value_obj)

    def __setup_ops(self):
        self.op_to_lambda = {}
        # set up operations on integers
        self.op_to_lambda[Type.INT] = {}
        self.op_to_lambda[Type.BOOL] = {}
        self.op_to_lambda[Type.STRING] = {}
        self.op_to_lambda[Type.NIL] = {}

        self.op_to_lambda[Type.INT]["+"] = lambda x, y: Value(
            x.type(), x.value() + y.value()
        )
        self.op_to_lambda[Type.INT]["-"] = lambda x, y: Value(
            x.type(), x.value() - y.value()
        )
        # add other operators here later for int, string, bool, etc
        self.op_to_lambda[Type.STRING]["+"] = lambda x, y: Value(
            x.type(), x.value() + y.value()
        )
        self.op_to_lambda[Type.STRING]["=="] = lambda x, y: Value(
            Type.BOOL, x.value() == y.value()
            if x.type() == y.type() else False
        )
        self.op_to_lambda[Type.STRING]["!="] = lambda x, y: Value(
            Type.BOOL, x.value() != y.value()
        )
        self.op_to_lambda[Type.INT]["neg"] = lambda x: Value( 
            x.type(), 0 - x.value()
        )
        self.op_to_lambda[Type.INT]["*"] = lambda x, y: Value(
            x.type(), x.value() * y.value()
        )
        self.op_to_lambda[Type.INT]["/"] = lambda x, y: Value(
            x.type(), x.value() // y.value()
        )
        self.op_to_lambda[Type.INT]["<="] = lambda x, y: Value(
            Type.BOOL, x.value() <= y.value()
        )
        self.op_to_lambda[Type.INT][">="] = lambda x, y: Value(
            Type.BOOL, x.value() >= y.value()
        )
        self.op_to_lambda[Type.INT]["<="] = lambda x, y: Value(
            Type.BOOL, x.value() <= y.value()
        )
        self.op_to_lambda[Type.INT]["<"] = lambda x, y: Value(
            Type.BOOL, x.value() < y.value()
        )
        self.op_to_lambda[Type.INT][">"] = lambda x, y: Value(
            Type.BOOL, x.value() > y.value()
        )
        self.op_to_lambda[Type.INT]["=="] = lambda x, y: Value(
            Type.BOOL, x.value() == y.value()
            #if isinstance(x, int) and isinstance(y, int) else False
            if x.type() == y.type() else False
        )
        self.op_to_lambda[Type.INT]["!="] = lambda x, y: Value(
            Type.BOOL, x.value() != y.value()
            #if isinstance(x, int) and isinstance(y, int) else True
            if x.type() == y.type() else True
        )
        self.op_to_lambda[Type.BOOL]["!"] = lambda x: Value(
            Type.BOOL, not x.value()
        )
        self.op_to_lambda[Type.BOOL]["=="] = lambda x, y: Value(
            Type.BOOL, x.value() == y.value()
        )
        self.op_to_lambda[Type.BOOL]["!="] = lambda x, y: Value(
            Type.BOOL, x.value() != y.value()
        )
        self.op_to_lambda[Type.BOOL]["||"] = lambda x, y: Value(
            Type.BOOL, x.value() or y.value()
        )
        self.op_to_lambda[Type.BOOL]["&&"] = lambda x, y: Value(
            Type.BOOL, x.value() and y.value()
        )
        #NIL EDGE CASES
        self.op_to_lambda[Type.NIL]["=="] = lambda x, y: Value(
            Type.BOOL, x.value() == y.value()
            if x.type() == y.type() else False
            #Got rid of this to passs test_nil.br and test_ret2.br
        )
        self.op_to_lambda[Type.NIL]["!="] = lambda x, y: Value(
            Type.BOOL, x.value() != y.value()
            if x.type() == y.type() else True
        )
        






  # all programs will be provided to your interpreter as a python string, 
  # just as shown here.

# def main():
#     program_source = """
#         func foo() { 
#             print("hello");
#         }
#         func bar() {
#             return;
#         }

#         func main() {
#             val = nil;
#             if (foo() == val && bar() == nil) { print("this should print!"); }
#         }

#         """

#     interpreter = Interpreter()
#     interpreter.run(program_source)

# if __name__ == "__main__":
#     main()


# def main():
#     program_source = """
#         func main() {
#             print(foo(true) != nil);
#             print(foo(false) == nil);
#         }

#         func foo(x) {
#             print("hi");
#             if (x) {
#                 print("returning true");
#                 return true;
#             }
#         }

#         """

#     interpreter = Interpreter()
#     interpreter.run(program_source)

# if __name__ == "__main__":
#     main()



def main():
    program_source = """
        
        func main() {
            print (fib(4));
        }

        func fib(x){
            if (x < 3){
                
                return 1;
            }
            else{
                return fib(x-2) + fib(x-1);
            }
        }
        
        
        """

    interpreter = Interpreter()
    interpreter.run(program_source)

if __name__ == "__main__":
    main()

# def main():
#     program_source = """
#         func foo() {
#         i = 0;
#         while (i < 3) {
#             j = 0;
#             while (j < 3) {
#                 k = 0;
#                 while (k < 3) {
#                     if (i * j * k == 1) {
#                         return ans;
#                     } else {
#                         ans = ans + 1;
#                         k = k + 1;
#                     }
#                 }
#                 j = j + 1;
#             }
#             i = i + 1;
#         }
#         }

#         func main() {
#         ans = 0;
#         print(foo());
#         print(ans);
#         }
#         """

#     interpreter = Interpreter(trace_output=False)
#     interpreter.run(program_source)

# if __name__ == "__main__":
#     main()

# def main():
#     program_source = """
#         func foo() {
#             return 5;
#         }
#         func main() {
#             ans = 0;
#             print(foo());
#             print (ans);
#         }
#         """

#     interpreter = Interpreter()
#     interpreter.run(program_source)

# if __name__ == "__main__":
#     main()

# def main():
#     program_source = """
#         func main() {
#             ans = 0;
#             i = 0;
#             while (i < 3) {
#                 print("in while");
#                 if (i == 2){
#                     return ans;
#                 }
#                 ans = ans + 1;
#                 i = i + 1;
#             }
#             print("normal", ans);
#         }
#         """

#     interpreter = Interpreter()
#     interpreter.run(program_source)

# if __name__ == "__main__":
#     main()

# def main():
#     program_source = """
#         func bar(x, y){
#             z = x + y;
#             print(z);
#         }

#         func main() {
            
#         a = 3;
#         if (a < 5){
#             print("if statement working");
#         }
#         else{
#             print("I love Matthew Tsega");
#         }

#         g = 0;

#         while (g < 4){
#             print ("g = ", g);
#             g = g+1;

#             return 
#         }

#         h = nil;
#         if (h == nil){
#             print("NIL WORKS");
#         }

#         bar(9, 10);

#         }
#         """

#     interpreter = Interpreter()
#     interpreter.run(program_source)

# if __name__ == "__main__":
#     main()


# def main():
#     program_source = """
#         func main() {
            
#         a = -5;
#         print(a);
#         b = false;
#         print(!b);

#         print (1 > 0);
#         print (0 < 1);
#         print (5 >= 3);
#         print (5 != 3);
#         print (4 <= 8);
#         print (7 == 7);
#         x = "abc" == "abc";
#         y = "abc" != "def";
#         print ("abc"+"def");
#         print (x);
#         print (y);
#         print (true || false);
#         print (false && false);
#         z = inputs("Enter a name: ");
#         print ("Hello ", z, "!");
            
#         }
#         """

#     interpreter = Interpreter()
#     interpreter.run(program_source)

# if __name__ == "__main__":
#     main()


