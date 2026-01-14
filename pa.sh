#!/usr/bin/env bash

export PASH_TOP=${PASH_TOP:-${BASH_SOURCE%/*}}
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/usr/local/lib/"
export PYTHONPATH="${PASH_TOP}/python_pkgs/:${PYTHONPATH}"
export RUNTIME_DIR="${RUNTIME_DIR:-$PASH_TOP/runtime}"
export RUNTIME_LIBRARY_DIR="${RUNTIME_LIBRARY_DIR:-$PASH_TOP/runtime/}"



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

source "$RUNTIME_DIR/jit_runtime_init.sh"

export PASH_BASH_VERSION="${BASH_VERSINFO[@]:0:3}"

umask "$old_umask"
PASH_FROM_SH="pa.sh" python3 -S "$PASH_TOP/compiler/pash.py" "$@"
pash_exit_code=$?


(exit "$pash_exit_code")
