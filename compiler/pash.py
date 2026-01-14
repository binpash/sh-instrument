import sys
import os
import subprocess
from datetime import datetime

import config
from config import log, ptempfile, logging_prefix, print_time_delta
from cli import RunnerParser, PreprocessorParser
import ast_to_ast
from parse import parse_shell_to_asts, from_ast_objects_to_shell
from ast_util import string_to_argument, make_command
from shasta.json_to_ast import to_ast_node

LOGGING_PREFIX = "PaSh: "


class TransformationState:
    """Manages state during AST transformation and region replacement"""

    def __init__(self):
        self._node_counter = 0

    def get_next_id(self):
        new_id = self._node_counter
        self._node_counter += 1
        return new_id

    def get_current_id(self):
        return self._node_counter - 1

    def get_number_of_ids(self):
        return self._node_counter

    def replace_df_region(self, asts, disable_parallel_pipelines=False, ast_text=None):
        """Replace a dataflow region with a call to jit.sh runtime"""
        # Create sequential script file
        sequential_script_file_name = ptempfile()

        # Get shell text from ASTs
        if ast_text is None:
            text_to_output = from_ast_objects_to_shell(asts)
        else:
            text_to_output = ast_text

        # Write script to file
        with open(sequential_script_file_name, "w", encoding="utf-8") as script_file:
            script_file.write(text_to_output)

        # Create AST node that calls jit.sh
        # Generates: JIT_INPUT=<file> JIT_SCRIPT_TO_EXECUTE=<file> source jit.sh
        assignments = [
            ["JIT_INPUT", string_to_argument(sequential_script_file_name)],
            ["JIT_SCRIPT_TO_EXECUTE", string_to_argument(sequential_script_file_name)]
        ]

        arguments = [
            string_to_argument("source"),
            string_to_argument(config.RUNTIME_EXECUTABLE),
        ]
        runtime_node = make_command(arguments, assignments=assignments)

        return to_ast_node(runtime_node)


@logging_prefix(LOGGING_PREFIX)
def main():
    ## Parse arguments
    args, shell_name = parse_args()
    ## If it is interactive we need a different execution mode
    ##
    ## The user can also ask for an interactive mode irregardless of whether pash was invoked in interactive mode.
    if len(args.input) == 0 or args.interactive:
        log("ERROR: --interactive option is not supported!", level=0)
        assert False
    else:
        input_script_path = args.input[0]
        input_script_arguments = args.input[1:]

        ## Preprocess and execute the parsed ASTs
        return_code = preprocess_and_execute_asts(
            input_script_path, args, input_script_arguments, shell_name
        )

        log("-" * 40)  # log end marker
        ## Return the exit code of the executed script
        sys.exit(return_code)


def preprocess(input_script_path, args):
    """Preprocess a shell script by parsing, transforming, and unparsing ASTs"""
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
    """Transform AST objects by replacing regions with JIT runtime calls"""
    trans_state = TransformationState()
    preprocessed_asts = ast_to_ast.replace_ast_regions(ast_objects, trans_state)
    return preprocessed_asts


def preprocess_and_execute_asts(
    input_script_path, args, input_script_arguments, shell_name
):
    preprocessed_shell_script = preprocess(input_script_path, args)
    if args.output_preprocessed:
        log("Preprocessed script:")
        log(preprocessed_shell_script)

    ## Write the new shell script to a file to execute
    fname = ptempfile()
    log("Preprocessed script stored in:", fname)
    with open(fname, "wb") as new_shell_file:
        preprocessed_shell_script = preprocessed_shell_script.encode(
            "utf-8", errors="replace"
        )
        new_shell_file.write(preprocessed_shell_script)

    ## 4. Execute the preprocessed version of the input script
    if not args.preprocess_only:
        return_code = execute_script(
            fname, args.command, input_script_arguments, shell_name
        )
    else:
        return_code = 0
    return return_code


def parse_args():
    prog_name = sys.argv[0]
    if "PASH_FROM_SH" in os.environ:
        prog_name = os.environ["PASH_FROM_SH"]
    ## We need to set `+` as a prefix char too
    parser = RunnerParser(prog_name, prefix_chars="-+")
    args = parser.parse_args()
    config.set_config_globals_from_pash_args(args)

    ## Initialize the log file
    config.init_log_file()

    ## Print all the arguments before they are modified below
    log("Arguments:")
    for arg_name, arg_val in vars(args).items():
        log(arg_name, arg_val)
    log("-" * 40)

    ## TODO: We might need to have a better default (like $0 of pa.sh)
    shell_name = "pash"

    if args.command is not None:
        fname = ptempfile()
        with open(fname, "w") as f:
            f.write(args.command)
        ## If the shell is invoked with -c and arguments after it, then these arguments
        ## need to be assigned to $0, $1, $2, ... and not $1, $2, $3, ...
        if len(args.input) > 0:
            ## Assign $0
            shell_name = args.input[0]
            args.input = args.input[1:]
        args.input = [fname] + args.input
    elif len(args.input) > 0:
        shell_name = args.input[0]

    return args, shell_name


def shell_env(shell_name: str):
    new_env = os.environ.copy()
    new_env["PASH_TMP_PREFIX"] = config.PASH_TMP_PREFIX
    new_env["pash_shell_name"] = shell_name
    return new_env


## The following two functions need to correspond completely
def bash_prefix_args():
    subprocess_args = ["/usr/bin/env", "bash"]
    ## Add shell specific arguments
    if config.pash_args.a:
        subprocess_args.append("-a")
    else:
        subprocess_args.append("+a")
    if config.pash_args.v:
        subprocess_args.append("-v")
    if config.pash_args.x:
        subprocess_args.append("-x")
    return subprocess_args


def bash_exec_string(shell_name):
    flags = []
    if config.pash_args.a:
        flags.append("-a")
    if config.pash_args.v:
        flags.append("-v")
    if config.pash_args.x:
        flags.append("-x")
    return "exec -a{} bash {} -s $@\n".format(shell_name, " ".join(flags))


def execute_script(compiled_script_filename, command, arguments, shell_name):
    new_env = shell_env(shell_name)
    subprocess_args = bash_prefix_args()
    subprocess_args += [
        "-c",
        "source {}".format(compiled_script_filename),
        shell_name,
    ] + arguments
    # subprocess_args = ["/usr/bin/env", "bash", compiled_script_filename] + arguments
    log(
        "Executing:",
        "PASH_TMP_PREFIX={} pash_shell_name={} {}".format(
            config.PASH_TMP_PREFIX, shell_name, " ".join(subprocess_args)
        ),
    )
    exec_obj = subprocess.run(subprocess_args, env=new_env, close_fds=False)
    return exec_obj.returncode


if __name__ == "__main__":
    main()
