from abc import ABC, abstractmethod
from enum import Enum
# Runtime-only mode: No pickle needed (no IR serialization)
# import pickle

from shell_ast.ast_util import *
from shasta.json_to_ast import to_ast_node
# Runtime-only mode: No speculative execution
# from speculative import util_spec
from parse import from_ast_objects_to_shell


## Runtime-only mode: only PASH transformation supported
class TransformationType(Enum):
    PASH = "pash"
    # SPECULATIVE and AIRFLOW modes removed - not supported in runtime-only mode


class AbstractTransformationState(ABC):
    def __init__(self):
        self._node_counter = 0
        self._loop_counter = 0
        self._loop_contexts = []

    def get_mode(self):
        return TransformationType.PASH

    ## Node id related
    def get_next_id(self):
        new_id = self._node_counter
        self._node_counter += 1
        return new_id

    def get_current_id(self):
        return self._node_counter - 1

    def get_number_of_ids(self):
        return self._node_counter

    ## Loop id related
    def get_next_loop_id(self):
        new_id = self._loop_counter
        self._loop_counter += 1
        return new_id

    def get_current_loop_context(self):
        ## We want to copy that
        return self._loop_contexts[:]

    def get_current_loop_id(self):
        if len(self._loop_contexts) == 0:
            return None
        else:
            return self._loop_contexts[0]

    def enter_loop(self):
        new_loop_id = self.get_next_loop_id()
        self._loop_contexts.insert(0, new_loop_id)
        return new_loop_id

    def exit_loop(self):
        self._loop_contexts.pop(0)

    @abstractmethod
    def replace_df_region(
        self, asts, disable_parallel_pipelines=False, ast_text=None
    ) -> AstNode:
        pass


## Use this object to pass options inside the preprocessing
## trasnformation.
class TransformationState(AbstractTransformationState):
    def replace_df_region(
        self, asts, disable_parallel_pipelines=False, ast_text=None
    ) -> AstNode:
        # Runtime-only mode: Create ONLY the sequential script file (no IR pickle)
        sequential_script_file_name = ptempfile()
        text_to_output = get_shell_from_ast(asts, ast_text=ast_text)
        with open(sequential_script_file_name, "w", encoding="utf-8") as script_file:
            script_file.write(text_to_output)

        # Call jit.sh instead of pash_runtime.sh
        replaced_node = TransformationState.make_call_to_jit_runtime(
            sequential_script_file_name
        )

        return to_ast_node(replaced_node)

    ## This function makes a command that calls jit.sh runtime
    ## to execute the sequential script with proper shell state management.
    ##
    ## Runtime-only mode: No IR file, no compilation, just direct execution.
    @staticmethod
    def make_call_to_jit_runtime(sequential_script_file_name) -> AstNode:
        """
        Creates AST node that calls jit.sh to execute sequential script.

        Generates: JIT_INPUT=<file> JIT_SCRIPT_TO_EXECUTE=<file> source jit.sh
        """
        assignments = [
            ["JIT_INPUT", string_to_argument(sequential_script_file_name)],
            ["JIT_SCRIPT_TO_EXECUTE", string_to_argument(sequential_script_file_name)]
        ]

        # Path to jit.sh (uses RUNTIME_EXECUTABLE from config)
        arguments = [
            string_to_argument("source"),
            string_to_argument(config.RUNTIME_EXECUTABLE),
        ]
        runtime_node = make_command(arguments, assignments=assignments)
        return runtime_node


## Runtime-only mode: Speculative and Airflow transformations not supported
## These classes are removed since they are never instantiated in runtime-only mode


def get_shell_from_ast(asts, ast_text=None) -> str:
    ## If we don't have the original ast text, we need to unparse the ast
    if ast_text is None:
        text_to_output = from_ast_objects_to_shell(asts)
    else:
        text_to_output = ast_text
    return text_to_output
