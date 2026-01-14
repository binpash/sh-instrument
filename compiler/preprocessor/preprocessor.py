from datetime import datetime
import os

import config
from shell_ast import transformation_options, ast_to_ast
from parse import parse_shell_to_asts, from_ast_objects_to_shell
from util import *
# Runtime-only mode: no server communication, no speculative execution
# import server_util
# from speculative import util_spec
from cli import PreprocessorParser

LOGGING_PREFIX = "PaSh Preprocessor: "


@logging_prefix(LOGGING_PREFIX)
def preprocess(input_script_path, args):
    ## 1. Execute the POSIX shell parser that returns the AST in JSON
    preprocessing_parsing_start_time = datetime.now()
    ast_objects = parse_shell_to_asts(input_script_path, bash_mode=args.bash)
    preprocessing_parsing_end_time = datetime.now()
    print_time_delta(
        "Preprocessing -- Parsing",
        preprocessing_parsing_start_time,
        preprocessing_parsing_end_time,
    )

    ## 2. Preprocess ASTs by replacing possible candidates for compilation
    ##    with calls to the PaSh runtime.
    preprocessing_pash_start_time = datetime.now()
    preprocessed_asts = preprocess_asts(ast_objects, args)
    preprocessing_pash_end_time = datetime.now()
    print_time_delta(
        "Preprocessing -- PaSh",
        preprocessing_pash_start_time,
        preprocessing_pash_end_time,
    )

    ## 3. Translate the new AST back to shell syntax
    preprocessing_unparsing_start_time = datetime.now()
    preprocessed_shell_script = from_ast_objects_to_shell(preprocessed_asts)

    preprocessing_unparsing_end_time = datetime.now()
    print_time_delta(
        "Preprocessing -- Unparsing",
        preprocessing_unparsing_start_time,
        preprocessing_unparsing_end_time,
    )
    return preprocessed_shell_script


def preprocess_asts(ast_objects, args):
    ## Runtime-only mode: always use standard TransformationState
    ## Speculative and Airflow modes are not supported
    trans_options = transformation_options.TransformationState()

    ## Preprocess ASTs by replacing AST regions with calls to the runtime (jit.sh).
    preprocessed_asts = ast_to_ast.replace_ast_regions(ast_objects, trans_options)

    return preprocessed_asts


def main():
    parser = PreprocessorParser()
    args = parser.parse_args()
    config.set_config_globals_from_pash_args(args)

    ## Initialize the log file
    ## TODO: Can we move this somewhere where there is no need for copy paste?
    config.init_log_file()

    ## Choose the transformation node based on the argument given
    log("Preprocesing mode:", args.preprocess_mode)
    preprocessed_shell_script = preprocess(args.input, args)
    print(preprocessed_shell_script)


if __name__ == "__main__":
    main()
