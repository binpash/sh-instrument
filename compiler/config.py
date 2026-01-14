import logging
import os
import subprocess

from util import *


## Global
__version__ = "0.12.2-runtime"
GIT_TOP_CMD = [
    "git",
    "rev-parse",
    "--show-toplevel",
    "--show-superproject-working-tree",
]
if "PASH_TOP" in os.environ:
    PASH_TOP = os.environ["PASH_TOP"]
else:
    PASH_TOP = subprocess.run(
        GIT_TOP_CMD,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    ).stdout.rstrip()

PYTHON_VERSION = "python3"
RUNTIME_EXECUTABLE = os.path.join(PASH_TOP, "jit.sh")

## Ensure that PASH_TMP_PREFIX is set by pa.sh
assert not os.getenv("PASH_TMP_PREFIX") is None
PASH_TMP_PREFIX = os.getenv("PASH_TMP_PREFIX")

BASH_VERSION = tuple(int(i) for i in os.getenv("PASH_BASH_VERSION").split(" "))


##
## Global configuration used by all pash components
##
LOGGING_PREFIX = ""
OUTPUT_TIME = False
DEBUG_LEVEL = 0
LOG_FILE = ""

pash_args = None


## This function sets the global configuration
##
## TODO: Actually move everything outside of pash_args to configuration.
def set_config_globals_from_pash_args(given_pash_args):
    global pash_args, OUTPUT_TIME, DEBUG_LEVEL, LOG_FILE
    pash_args = given_pash_args
    DEBUG_LEVEL = pash_args.debug
    LOG_FILE = pash_args.log_file

    ## Also set logging here
    # Format logging
    # ref: https://docs.python.org/3/library/logging.html#formatter-objects
    ## TODO: When we add more logging levels bring back the levelname+time
    if given_pash_args.log_file == "":
        logging.basicConfig(format="%(message)s")
    else:
        logging.basicConfig(
            format="%(message)s",
            filename=f"{os.path.abspath(given_pash_args.log_file)}",
            filemode="w",
        )

    # Set debug level
    if given_pash_args.debug == 1:
        logging.getLogger().setLevel(logging.INFO)
    elif given_pash_args.debug >= 2:
        logging.getLogger().setLevel(logging.DEBUG)


## Increase the recursion limit (it seems that the parser/unparser needs it for bigger graphs)
sys.setrecursionlimit(10000)


def init_log_file():
    global LOG_FILE
    if not LOG_FILE == "":
        with open(LOG_FILE, "w") as f:
            pass
