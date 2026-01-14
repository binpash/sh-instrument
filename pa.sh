#!/usr/bin/env bash

export PASH_TOP=${PASH_TOP:-${BASH_SOURCE%/*}}
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/usr/local/lib/"
export PYTHONPATH="${PASH_TOP}/python_pkgs/:${PYTHONPATH}"

trap kill_all SIGTERM SIGINT
kill_all() {
    kill -s SIGKILL 0
}

old_umask=$(umask)
umask u=rwx,g=rx,o=rx

if [ "$#" -eq 1 ] && [ "$1" = "--init" ]; then
  echo "No initialization needed for runtime-only mode"
  exit
fi

if ! command -v python3 &> /dev/null; then
    echo "Python >=3 could not be found"
    exit
fi

export PASH_BASH_VERSION="${BASH_VERSINFO[@]:0:3}"
export PASH_TMP_PREFIX="$(mktemp -d /tmp/pash_XXXXXXX)/"
export PASH_TIMESTAMP="$(date +"%y-%m-%d-%T")"

umask "$old_umask"
PASH_FROM_SH="pa.sh" python3 -S "$PASH_TOP/compiler/pash.py" "$@"
pash_exit_code=$?

if [ "${PASH_DEBUG_LEVEL:-0}" -eq 0 ]; then
  rm -rf "${PASH_TMP_PREFIX}"
fi

(exit "$pash_exit_code")
