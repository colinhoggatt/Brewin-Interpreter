# The EnvironmentManager class keeps a mapping between each variable (aka symbol)
# in a brewin program and the value of that variable - the value that's passed in can be
# anything you like. In our implementation we pass in a Value object which holds a type
# and a value (e.g., Int, 10).
class EnvironmentManager:
    def __init__(self):
        self.environment = {}
        # self.env_stack = []


    # Gets the data associated a variable name
    def get(self, symbol):
        if symbol in self.environment:
            return self.environment[symbol]
        return None

    # Sets the data associated with a variable name
    def set(self, symbol, value):
        self.environment[symbol] = value



#Thought Process:
# We need to create an environment stack to hold the scope of the entire program and each of its blocks
# For each block, we should push a new environment onto the environment stack and store its variables there
# If we don't find a value or variable in the current scope, loop through the stack and check the next most recent scope
class EnvironmentStack:
    def __init__(self, initial):
        self.stack = [initial]
        
    def push(self, environment): # push a new environment(scope) onto the stack
        self.stack.append(environment)
    
    def pop(self): # remove the most recent scope
        try:
            self.stack.pop()
        except:
            raise IndexError
        

    def get(self, symbol): #get the value of the symbol, starting from the most recent scope
        for scope in reversed(self.stack):
            if symbol in scope.environment:
                return scope.environment[symbol]
        return None
        raise NameError # how to raise an error if item is not in any scope??
    
    # need a global set so if variables aren't in current scope, set them in the next closest scope
    def set(self, symbol, value):
        #check if in current scope
        if symbol in self.top().environment: # if the symbol is in current scope, set it
            #self.environment.set(symbol, value)
           # self.stack[-1].environment.set(symbol, value)
           self.stack[-1].environment[symbol] = value
        else:
            found_flag = False
            for scope in reversed(self.stack): #if not in current scope, iterate through the rest of the scopes
                if symbol in scope.environment: # if it's in a different scope, set the value in that scope
                    #self.scope.environment.set(symbol, value)
                    scope.environment[symbol] = value
                    found_flag = True
                    break
            if found_flag is False: # if not in any of the scopes, set it in the current scope
                #self.stack[-1].environment.set(symbol, value)
                self.stack[-1].environment[symbol] = value
                
                


    def top(self): #get the current scope (IDK if we need this)
        if len(self.stack) <= 0:
            return None
        else:
            return self.stack[-1]
        
        