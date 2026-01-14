"""
AST to AST transformation


The preprocessing pass replaces all _candidate_ dataflow regions with
calls to PaSh's runtime to let it establish if they are actually dataflow
regions. The pass serializes all candidate dataflow regions:
- A list of ASTs if at the top level or
- an AST subtree if at a lower level

The PaSh runtime then deserializes the(m, compiles them (if safe) and optimizes them.
"""

from ast_util import *
from preprocess_ast_cases import preprocess_node


