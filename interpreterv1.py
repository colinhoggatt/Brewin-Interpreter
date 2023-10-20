from intbase import InterpreterBase
from intbase import ErrorType
from element import Element
from brewparse import parse_program

class Interpreter(InterpreterBase):
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase's constructor
    

# 	func run(program):
# 		ast = parse_program(program)         # parse program into AST
#             this.variable_name_to_value = Map()  # dict to hold variables
# 		main_func_node = get_main_func_node(ast)
# 		run_func(main_func_node)

    def run(self, program):
        #print("run starting")
        ast = parse_program(program)         # parse program into AST
        self.var_map = dict() # dict to hold variables
        main_func_node = ast.get('functions')
        self.run_func(main_func_node)

# 	func run_func(func_node):
# 		for each statement_node in func_node.statements:
# 			run_statement(statement_node)
    def run_func(self, func_node):
        #print ("run_func starting")
        for nodes in func_node: 
            if nodes.get('name') == 'main':
                #print ("in main")
                for statements in nodes.get('statements'): #changed from just 'func_node' ??
                    #print(statements.get('name')) # print check
                    self.run_statement(statements)
            else:
                super().error(ErrorType.NAME_ERROR,"No main() function was found",)


                          

# 	func run_statement(statement_node):
# 		if is_assignment(statement_node):
# 			do_assignment(statement_node);
# 		else if is_func_call(statement_node):
# 			do_func_call(statement_node);
# 		...
    def run_statement(self, statement_node):
        if statement_node.elem_type == '=':
            #print ("This is an assignment")
            self.do_assignment(statement_node)
        elif statement_node.elem_type == 'fcall':
            #print ("This is a function call")
            self.do_func_call(statement_node)
        else:
            super().error(ErrorType.NAME_ERROR,"Unknown Statement",)


	# func do_assignment(statement_node):
	# 	target_var_name = get_target_variable_name(statement_node)
	# 	source_node = get_expression_node(statement_node)
	# 	resulting_value = evaluate_expression(source_node)
	# 	this.variable_name_to_value[target_var_name] = resulting_value

    def do_assignment(self, statement_node):
        var_name = statement_node.get('name') 
        source_node = statement_node.get('expression') 
        result_val = self.evaluate_expression(source_node) #add param for var_name?
        self.var_map[var_name] = result_val #should I be updating self.var_map?
        
    

    def do_func_call(self, statement_node):
        var_name = statement_node.get('name') #this should be "print"
        if (var_name != "print"):
            super().error(ErrorType.NAME_ERROR,"Unknown function call",)
        arg_list = statement_node.get('args')
        self.evaluate_expression(statement_node)



#       func evaluate_expression(expression_node):
#             if is_value_node(expression_node):
#                 return get_value(expression_node)
#             else if is_variable_node(expression_node):
#                 return get_value_of_variable(expression_node)
#             else if is_binary_operator(expression_node):
#                 return evaluate_binary_operator(expression_node)
#             ...
# 	...

    def evaluate_expression(self, source_node): # source_node maps to either exp node, var node, or val node
        source_type = source_node.elem_type
        if source_type == 'int': 
            # update map for type 
            return ("int", source_node.get('val'))
        if source_type == 'string': 
            # update map for type 
            return ("str", source_node.get('val'))
        elif source_type == 'var': # We are accessing a variable node here
            #return source_node.get('name')
            return self.var_map[source_node.get('name')]
        #if an exp node, can have binary operators or function call
        elif source_type == '+':
            # op1 = source_node.get('op1')
            #print ("op1 is a " + str(op1))
            #print (str(op1.get('val')))
            # op2 = source_node.get('op2')
            #print ("op2 is a " + str(op2))
            #print (str(op2.get('val')))
            op1 = self.evaluate_expression(source_node.get('op1'))
            op2 = self.evaluate_expression(source_node.get('op2'))
            print (op1)
            print (op2)
            if (op1[0] == op2[0]): # check the type of operands
                 ans = op1[1] + op2[1] #add the values
                 #print (ans)
                 return ("int", ans)
            else:
                super().error(ErrorType.TYPE_ERROR,"Incompatible types for arithmetic operation",)
           
        elif source_type == '-':
            op1 = self.evaluate_expression(source_node.get('op1'))
            op2 = self.evaluate_expression(source_node.get('op2'))
            # print (str(op1.get('val')))
            # print (str(op2.get('val')))
            if (op1[0] == op2[0]): # check the type of operands
                 ans = op1[1] - op2[1] #add the values
                 #print (ans)
                 return ("int", ans)
            else:
                super().error(ErrorType.TYPE_ERROR,"Incompatible types for arithmetic operation",)

        elif source_type == 'fcall':
            if (source_node.get('name') == 'print'):
                arg_list = source_node.get('args')
                concat = ""
                for x in arg_list: # evaluate the list of nodes, cast to a string, and then concatenate them
                    args = self.evaluate_expression(x)
                    #print(str(args[1]))
                    concat = concat + str(args[1])

                super().output(concat) #concat the list of args

            elif (source_node.get('name') == 'inputi'):
                input_list = source_node.get('args')
                if (len(input_list) > 1):
                    super().error(ErrorType.TYPE_ERROR,"Invalid number of arguments",)
                for x in input_list: #for future if we accept more arguments
                    # print(x)
                    # print( "Name is " + x.get('name'))
                    # print("Exp is " + x.get('expression'))
                    super().output(x.get('val'))
                    input = int(super().get_input())
                    return ("int", input)
                    #eval_input = self.evaluate_expression(input) 
                
            else:
                super().error(ErrorType.NAME_ERROR,"Invalid function call",)
                    
                    
        else:
            super().error(ErrorType.NAME_ERROR,"Unknown Expression",)







            

     
    #   func evaluate_expression(expression_node):
    #         if is_value_node(expression_node):
    #             return get_value(expression_node)
    #         else if is_variable_node(expression_node):
    #             return get_value_of_variable(expression_node)
    #         else if is_binary_operator(expression_node):
    #             return evaluate_binary_operator(expression_node)
    #         ...
	# ...


			     

def main():
    interpreter = Interpreter()
    program1 = """
    func main() {
        x = 5 + 6;
        y = 2 - 1;
        print("The sum is: ", x);
        print("The difference is: ", y);
        foo = inputi("Enter a number: ");
        print(foo);
        }
    """
    interpreter.run(program1)

  
    
if __name__ == "__main__":
    main()	

# def main():
#   # all programs will be provided to your interpreter as a python string, 
#   # just as shown here.
#     program_source = """
#     func main() {
#         x = 5 + 6;
#         print("The sum is: ", x);
#         }
#     """

#     interpreter = Interpreter()
#     interpreter.run(program_source)


# if __name__ == 'main':
#     main()


# def main():
#   # all programs will be provided to your interpreter as a python string, 
#   # just as shown here.
#   interpreter = Interpreter(trace_output = True)
#   program_source = """func main() {
#     x = 5;
#     print("The sum is: ", x);
# }
# """

 
#   # this is how you use our parser to parse a valid Brewin program into 
#   # an AST:
#   parsed_program = parse_program(program_source)
