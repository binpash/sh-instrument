#!/bin/bash

## Assumes the following variable is set:
## __jit_script_to_execute: the script that was stubbed

## High level design (adapted from pash_runtime.sh):
##
## (1) Save shell state (exit code, set status)
## (2) No compilation - just prepare to execute sequential script
## (3) Restore shell state before execution
## (4) Execute the script
## (5) Save state after execution (for logging)
## (6) No daemon communication needed
## (7) Restore final state before exit

##
## (1) Save shell state
##

## First save the state of the shell
export __jit_previous_exit_status="$?"
export __jit_previous_set_status=$-
source "$RUNTIME_DIR/jit_set_from_to.sh" "$__jit_previous_set_status" "${DEFAULT_SET_STATE:-huB}"
__jit_redir_output echo "$$: (1) Pre-ec, pre-set, jit-set: ($__jit_previous_exit_status, $__jit_previous_set_status, $-)"

##
## (2) Prepare for dynamic analysis
##
##
## Your analysis on $__jit_script_to_execute here!
##

##
## (3) & (4) Restore state and execute script
##

## Run the script
export SCRIPT_TO_EXECUTE="$__jit_script_to_execute"
## Clean up JIT-specific environment variables to prevent leakage
unset __jit_script_to_execute
source "$RUNTIME_DIR/jit_restore_state_and_execute.sh"

## Comment out the rest if you don't want an analysis post execution of the script

##
## (5) Save state after execution
##

## Save the state after execution
export __jit_runtime_final_status="$?"
export __jit_previous_set_status=$-
source "$RUNTIME_DIR/jit_set_from_to.sh" "$__jit_previous_set_status" "${DEFAULT_SET_STATE:-huB}"
__jit_redir_output echo "$$: (5) Script exited with ec: $__jit_runtime_final_status"

##
## (6) Your analysis post execution here
##

##
## (7) Restore final state before exit
##

## Set the shell state before exiting
__jit_redir_output echo "$$: (7) Reverting set (from,to): ($-,$__jit_previous_set_status)"
source "$RUNTIME_DIR/jit_set_from_to.sh" "$-" "$__jit_previous_set_status"

## Set the exit code
(exit "$__jit_runtime_final_status")
