import copy

from enum import Enum
from intbase import InterpreterBase
from env_v4 import EnvironmentManager


# Enumerated type for our different language data types
class Type(Enum):
    INT = 1
    BOOL = 2
    STRING = 3
    CLOSURE = 4
    NIL = 5
    OBJECT = 6


class Closure:
    def __init__(self, func_ast, env):
        # Need to change this so we don't deep copy everything (only primitives)
        
        self.captured_env = copy.deepcopy(env)
        self.closure_capture(self.captured_env, env)

        self.func_ast = func_ast
        self.type = Type.CLOSURE

    def closure_capture(self, env, original_environment):
        for copied_scope, actual_scope in zip(env.environment, original_environment.environment):
            for name, obj in copied_scope.items():
                if obj.type() == Type.OBJECT or obj.type() == Type.CLOSURE:
                    copied_scope[name] = actual_scope[name]

class Object:
    def __init__(self):
        self.fields = {"proto": None}
        self.proto = None # __proto__ ???
        self.type = Type.OBJECT
    
    def get_member(self, member_name):
        # First search current object members

       
        if member_name in self.fields:
            return self.fields[member_name]
        # Then search prototype's members
        proto = self.fields["proto"]
        #print (proto.v)
        if proto is not None:
            #proto_obj = self.proto
            while proto and proto.value() != InterpreterBase.NIL_DEF:
                print("proto", proto.value())
                if member_name in proto.v.fields:
                    return proto.v.fields[member_name] # Be careful, does this work on recursive calls to proto? and will it call fields correctly from derived object?
                proto = proto.v.fields["proto"]
        # obj_proto = proto_dict[self]
        # while obj_proto is not None and obj_proto != InterpreterBase.NIL_DEF:
        #     if member_name in obj_proto.fields:
        #         return obj_proto.fields[member_name] # same as finding a member of a normal object, but just for its proto
        #     else:
        #         obj_proto = proto_dict[obj_proto] # If not found in this proto, check the proto's proto
        return None
    
    def set_member(self, member_name, field_or_obj):
        self.fields[member_name] = field_or_obj






# Represents a value, which has a type and its value
class Value:
    def __init__(self, t, v=None):
        self.t = t
        self.v = v

    def value(self):
        return self.v

    def type(self):
        return self.t

    def set(self, other):
        self.t = other.t
        self.v = other.v


def create_value(val):
    if val == InterpreterBase.TRUE_DEF:
        return Value(Type.BOOL, True)
    elif val == InterpreterBase.FALSE_DEF:
        return Value(Type.BOOL, False)
    elif isinstance(val, str):
        return Value(Type.STRING, val)
    elif isinstance(val, int):
        return Value(Type.INT, val)
    elif val == InterpreterBase.NIL_DEF:
        return Value(Type.NIL, None)
    else:
        raise ValueError("Unknown value type")


def get_printable(val):
    if val.type() == Type.INT:
        return str(val.value())
    if val.type() == Type.STRING:
        return val.value()
    if val.type() == Type.BOOL:
        if val.value() is True:
            return "true"
        return "false"
    return None
