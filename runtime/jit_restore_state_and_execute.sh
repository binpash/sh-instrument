#!/bin/bash

## File directory
RUNTIME_DIR=$(dirname "${BASH_SOURCE[0]}")

## INPUT: Expects SCRIPT_TO_EXECUTE to be set

#ONLY WAY OUT IS TO TREAT EXEC in special way

## Recover the `set` state of the previous shell
# __jit_redir_output echo "$$: (3) Previous BaSh set state: $__jit_previous_set_status"
# __jit_redir_output echo "$$: (3) JIT-internal set state of current shell: $-"
export __jit_current_set_state=$-
source "$RUNTIME_DIR/jit_set_from_to.sh" "$__jit_current_set_state" "$__jit_previous_set_status"
__jit_redir_output echo "$$: (3) Reverted to BaSh set state: $-"

## Execute the script
__jit_redir_output echo "$$: (4) Restoring previous exit code: ${__jit_previous_exit_status}"
__jit_redir_output echo "$$: (4) Will execute script in ${SCRIPT_TO_EXECUTE}:"
__jit_redir_output cat "${SCRIPT_TO_EXECUTE}"

## Note: We run the `exit` in a checked position so that we don't simply exit when we are in `set -e`.
if (exit "$__jit_previous_exit_status")
then 
{
    ## This works w.r.t. arguments because source does not change them if there are no arguments
    ## being given.
    source "${SCRIPT_TO_EXECUTE}"
}
else 
{
    source "${SCRIPT_TO_EXECUTE}"
}
fi
