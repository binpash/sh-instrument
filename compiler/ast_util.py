from shasta.ast_node import *
from shasta.json_to_ast import *

## This class is used by the preprocessor in ast_to_ir
class PreprocessedAST:
    def __init__(
        self, ast, replace_whole, non_maximal, something_replaced=True, last_ast=False
    ):
        assert isinstance(ast, AstNode)
        self.ast = ast
        self.replace_whole = replace_whole
        self.non_maximal = non_maximal
        self.something_replaced = something_replaced
        self.last_ast = last_ast

    def should_replace_whole_ast(self):
        return self.replace_whole

    def is_non_maximal(self):
        return self.non_maximal

    def will_anything_be_replaced(self):
        return self.something_replaced

    def is_last_ast(self):
        return self.last_ast


## This class represents text that was not modified at all by preprocessing, and therefore does not
## need to be unparsed.
class UnparsedScript:
    def __init__(self, text):
        self.text = text


##
## Pattern matching for the AST
##


def format_arg_chars(arg_chars):
    chars = [format_arg_char(arg_char) for arg_char in arg_chars]
    return "".join(chars)


def format_arg_char(arg_char: ArgChar) -> str:
    return arg_char.format()


def string_to_argument(string):
    ret = [char_to_arg_char(char) for char in string]
    return ret


def concat_arguments(arg1, arg2):
    ## Arguments are simply `arg_char list` and therefore can just be concatenated
    return arg1 + arg2


## FIXME: This is certainly not complete. It is used to generate the
## AST for the call to the distributed planner. It only handles simple
## characters
def char_to_arg_char(char):
    return ["C", ord(char)]


def make_command(arguments, redirections=None, assignments=None):
    redirections = [] if redirections is None else redirections
    assignments = [] if assignments is None else assignments
    lineno = 0
    node = make_kv("Command", [lineno, assignments, arguments, redirections])
    return node


def make_nop():
    return make_command([string_to_argument(":")])

def make_kv(key, val):
    return [key, val]