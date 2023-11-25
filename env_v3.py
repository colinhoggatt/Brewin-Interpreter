# The EnvironmentManager class keeps a mapping between each variable name (aka symbol)
# in a brewin program and the Value object, which stores a type, and a value.
class EnvironmentManager:
    def __init__(self):
        self.environment = [{}]

    # returns a VariableDef object
    def get(self, symbol):
        for env in reversed(self.environment):
            if symbol in env:
                return env[symbol]
                # if isinstance(value, tuple) and value[0] == "ref":
                #     #value = env[value[1]]  I DON"T THINK THIS WILL WORK
                #     return self.get(value[1])
                #return value

        return None

    def set(self, symbol, value):
        for env in reversed(self.environment):
            if symbol in env:
                # if isinstance(env[symbol], tuple) and (env[symbol][0] == "ref"):
                #     #print ("REFERENCE")
                env[symbol] = value
                        # would this work calling set recursively and passing in value[1]?
                # else: env[symbol] = value
                return

        # symbol not found anywhere in the environment
        self.environment[-1][symbol] = value

    # create a new symbol in the top-most environment, regardless of whether that symbol exists
    # in a lower environment
    def create(self, symbol, value):
        self.environment[-1][symbol] = value

    # used when we enter a nested block to create a new environment for that block
    def push(self):
        self.environment.append({})  # [{}] -> [{}, {}]

    # used when we exit a nested block to discard the environment for that block
    def pop(self):
        self.environment.pop()

    def flatten_env(self, env): #use flattened environment stack for lambda scope
        flat_env = {}
        for scope in reversed(env.environment):
            for symbol in scope:
               flat_env[symbol] = scope[symbol] 
        return flat_env


class Lambda:
    def __init__(self, lambda_ast, lambda_env):
        self.lambda_ast = lambda_ast
        self.env = lambda_env
    
    def get(self, ast):
        if ast == "lambda_ast":
            return self.lambda_ast
        elif ast == "env":
            return self.env
    
    def set(self, ast):
        pass
