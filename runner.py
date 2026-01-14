#!/usr/bin/env python3
"""
Runner - Executes preprocessed shell scripts.

This is a standalone executable that takes a preprocessed shell script
and executes it with the appropriate bash flags and arguments.
"""

import sys
import subprocess
import argparse
import logging


# Global state for bash flags
class BashFlags:
    def __init__(self, allexport=False, verbose=False, xtrace=False):
        self.allexport = allexport
        self.verbose = verbose
        self.xtrace = xtrace


bash_flags = None


def log(*args, level=1):
    """Simple logging function"""
    if level >= 1:
        message = " ".join([str(a) for a in args])
        logging.info(f"PaSh: {message}")


def bash_prefix_args():
    """Build bash command prefix with appropriate flags"""
    subprocess_args = ["/usr/bin/env", "bash"]
    ## Add shell specific arguments
    if bash_flags.allexport:
        subprocess_args.append("-a")
    else:
        subprocess_args.append("+a")
    if bash_flags.verbose:
        subprocess_args.append("-v")
    if bash_flags.xtrace:
        subprocess_args.append("-x")
    return subprocess_args


def bash_exec_string(shell_name):
    """Generate bash exec string with appropriate flags"""
    flags = []
    if bash_flags.allexport:
        flags.append("-a")
    if bash_flags.verbose:
        flags.append("-v")
    if bash_flags.xtrace:
        flags.append("-x")
    return "exec -a{} bash {} -s $@\n".format(shell_name, " ".join(flags))


def execute_script(compiled_script_filename, command, arguments, shell_name):
    """Execute a preprocessed shell script"""
    subprocess_args = bash_prefix_args()
    subprocess_args += [
        "-c",
        "source {}".format(compiled_script_filename),
        shell_name,
    ] + arguments
    log(
        "Executing:",
        " ".join(subprocess_args)
    )
    exec_obj = subprocess.run(subprocess_args, close_fds=False)
    return exec_obj.returncode


def parse_args():
    """Parse command-line arguments for the runner"""
    parser = argparse.ArgumentParser(
        description="Execute preprocessed shell scripts for PaSh",
        prog="runner.py",
        prefix_chars="-+"
    )

    parser.add_argument(
        "script_path",
        help="Path to the preprocessed script to execute"
    )

    parser.add_argument(
        "shell_name",
        help="Name to use for $0 in the executed script"
    )

    parser.add_argument(
        "script_args",
        nargs="*",
        default=[],
        help="Arguments to pass to the script"
    )

    parser.add_argument(
        "-a",
        dest="allexport",
        action="store_true",
        default=False,
        help="Enable the allexport shell option"
    )

    parser.add_argument(
        "+a",
        dest="allexport",
        action="store_false",
        help="Disable the allexport shell option"
    )

    parser.add_argument(
        "-v",
        dest="verbose",
        action="store_true",
        default=False,
        help="Print shell input lines as they are read (experimental)"
    )

    parser.add_argument(
        "-x",
        dest="xtrace",
        action="store_true",
        default=False,
        help="Print commands and their arguments as they execute (experimental)"
    )

    parser.add_argument(
        "-d",
        "--debug",
        type=int,
        default=0,
        help="Configure debug level; defaults to 0"
    )

    return parser.parse_args()


def main():
    """Main entry point for the runner"""
    global bash_flags

    args = parse_args()

    # Initialize logging
    logging.basicConfig(format="%(message)s")
    if args.debug == 1:
        logging.getLogger().setLevel(logging.INFO)
    elif args.debug >= 2:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize bash flags
    bash_flags = BashFlags(
        allexport=args.allexport,
        verbose=args.verbose,
        xtrace=args.xtrace
    )

    log("Runner starting...")
    log(f"Script path: {args.script_path}")
    log(f"Shell name: {args.shell_name}")
    log(f"Arguments: {args.script_args}")
    log(f"Flags: a={args.allexport}, v={args.verbose}, x={args.xtrace}")
    log("-" * 40)

    # Execute the script
    try:
        return_code = execute_script(
            args.script_path,
            None,  # command parameter (not used in this flow)
            args.script_args,
            args.shell_name
        )

        log("-" * 40)
        log(f"Script execution completed with return code: {return_code}")
        sys.exit(return_code)

    except Exception as e:
        log(f"ERROR: Script execution failed: {e}", level=0)
        sys.exit(1)


if __name__ == "__main__":
    main()
