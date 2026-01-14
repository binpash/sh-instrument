"""Stub for ast_to_ir - compilation not supported in runtime-only mode"""
import os
import sys

# Minimal initialization for imports
class BashExpansionState:
    def __init__(self):
        pass

    def close(self):
        pass

BASH_EXP_STATE = BashExpansionState()

def compile_node(*args, **kwargs):
    raise NotImplementedError("Compilation not supported in runtime-only mode")

def compile_asts(*args, **kwargs):
    raise NotImplementedError("Compilation not supported in runtime-only mode")
