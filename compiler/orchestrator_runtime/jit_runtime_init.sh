#!/bin/bash

## Minimal initialization for runtime-only mode
## Defines logging functions needed by orchestrator_runtime scripts

## Set PASH_DEBUG_LEVEL if not already set
export PASH_DEBUG_LEVEL="${PASH_DEBUG_LEVEL:-0}"
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
