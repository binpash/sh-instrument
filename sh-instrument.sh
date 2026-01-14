#!/usr/bin/env bash

export PASH_TOP=${PASH_TOP:-${BASH_SOURCE%/*}}
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/usr/local/lib/"
export RUNTIME_DIR="${RUNTIME_DIR:-$PASH_TOP/runtime}"
export RUNTIME_LIBRARY_DIR="${RUNTIME_LIBRARY_DIR:-$PASH_TOP/runtime/}"

# Use Python from virtual environment
PYTHON_VENV="$PASH_TOP/python_pkgs/bin/python"
if [ ! -f "$PYTHON_VENV" ]; then
    echo "Error: Python virtual environment not found at $PYTHON_VENV" >&2
    echo "Please run setup.sh first." >&2
    exit 1
fi

trap kill_all SIGTERM SIGINT
kill_all() {
    kill -s SIGKILL 0
}

old_umask=$(umask)
umask u=rwx,g=rx,o=rx

if ! command -v python3 &> /dev/null; then
    echo "Python >=3 could not be found"
    exit
fi

## Parse debug option without consuming arguments
export PASH_DEBUG_LEVEL=0
for ((i=1; i<=$#; i++)); do
    arg="${!i}"
    next_i=$((i+1))
    next_arg="${!next_i}"

    if [[ "$arg" == "-d" ]] || [[ "$arg" == "--debug" ]]; then
        if [[ -n "$next_arg" ]] && [[ "$next_arg" =~ ^[0-9]+$ ]]; then
            export PASH_DEBUG_LEVEL="$next_arg"
            break
        else
            echo "Error: --debug requires an integer argument" >&2
            exit 1
        fi
    fi
done

## TODO: Get it from argument
export PASH_REDIR="${PASH_REDIR:-&2}"

## `__jit_redir_output` and `__jit_redir_all_output` are strictly for logging.
## They do not execute their arguments if there is no debugging.
if [ "$PASH_DEBUG_LEVEL" -eq 0 ]; then
    __jit_redir_output()
    {
        :
    }

    __jit_redir_all_output()
    {
        :
    }

    __jit_redir_all_output_always_execute()
    {
        > /dev/null 2>&1 "$@"
    }

else
    if [ "$PASH_REDIR" == '&2' ]; then
        __jit_redir_output()
        {
            >&2 "$@"
        }

        __jit_redir_all_output()
        {
            >&2 "$@"
        }

        __jit_redir_all_output_always_execute()
        {
            >&2 "$@"
        }
    else
        __jit_redir_output()
        {
            >>"$PASH_REDIR" "$@"
        }

        __jit_redir_all_output()
        {
            >>"$PASH_REDIR" 2>&1 "$@"
        }

        __jit_redir_all_output_always_execute()
        {
            >>"$PASH_REDIR" 2>&1 "$@"
        }
    fi
fi

export -f __jit_redir_output
export -f __jit_redir_all_output
export -f __jit_redir_all_output_always_execute

umask "$old_umask"
PASH_FROM_SH="sh-instrument.sh" "$PYTHON_VENV" "$PASH_TOP/preprocessor/preprocess.py" "$@"
