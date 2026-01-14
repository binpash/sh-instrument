#!/bin/bash

## Runtime-only version of pash_runtime.sh
## Assumes the following variable is set:
## JIT_INPUT: the sequential script to execute
## JIT_SCRIPT_TO_EXECUTE: the script file path (can be same as JIT_INPUT)

## High level design (adapted from pash_runtime.sh):
##
## (1) Save shell state (exit code, set status)
## (2) No compilation - just prepare to execute sequential script
## (3) Restore shell state before execution
## (4) Execute the script
## (5) Save state after execution (for logging)
## (6) No daemon communication needed
## (7) Restore final state before exit

## Set runtime directories
export RUNTIME_DIR="${RUNTIME_DIR:-$PASH_TOP/compiler/orchestrator_runtime}"
export RUNTIME_LIBRARY_DIR="${RUNTIME_LIBRARY_DIR:-$PASH_TOP/runtime/}"

## Initialize logging functions
source "$RUNTIME_DIR/jit_runtime_init.sh"

##
## (1) Save shell state
##

## First save the state of the shell
source "$RUNTIME_DIR/save_shell_state.sh"
## Save state in JIT-specific variables
export __jit_previous_exit_status="$PREVIOUS_SHELL_EC"
export __jit_previous_set_status="$PREVIOUS_SET_STATUS"

__jit_redir_output echo "$$: (1) Previous exit status: $__jit_previous_exit_status"
__jit_redir_output echo "$$: (1) Previous set state: $__jit_previous_set_status"
__jit_redir_output echo "$$: (1) Set state reverted to JIT-internal set state: $-"

##
## (2) Prepare for sequential execution (no compilation)
##

## In runtime-only mode, we always execute the sequential script
## No daemon communication, no compilation, no parallel execution
__jit_script_to_execute="${JIT_SCRIPT_TO_EXECUTE:-$JIT_INPUT}"

__jit_redir_output echo "$$: (2) Runtime-only mode: will execute sequential script"
__jit_redir_output echo "$$: (2) Script to execute: $__jit_script_to_execute"

## Clean up JIT-specific environment variables immediately after use
## This prevents them from leaking into the user's script environment
unset JIT_INPUT JIT_SCRIPT_TO_EXECUTE

## Runtime-only mode always runs sequentially (no forking)
## This ensures correct shell state management and exit codes

##
## (3) & (4) Restore state and execute script
##

## Run the script (always sequential in runtime-only mode)
export SCRIPT_TO_EXECUTE="$__jit_script_to_execute"
source "$RUNTIME_DIR/jit_restore_state_and_execute.sh"

##
## (5) Save state after execution
##

## Save the state after execution
source "$RUNTIME_DIR/save_shell_state.sh"
__jit_runtime_final_status="$PREVIOUS_SHELL_EC"
export __jit_previous_set_status="$PREVIOUS_SET_STATUS"

__jit_redir_output echo "$$: (5) Script exited with ec: $__jit_runtime_final_status"

##
## (6) No daemon communication needed
##

## (skipped in runtime-only mode)

##
## (7) Restore final state before exit
##

## Set the shell state before exiting
__jit_redir_output echo "$$: (7) Current JIT set state: $-"
source "$RUNTIME_DIR/jit_set_from_to.sh" "$-" "$__jit_previous_set_status"
__jit_redir_output echo "$$: (7) Reverted to BaSh set state before exiting: $-"

## Clean up JIT-specific environment variables to prevent leakage
unset JIT_INPUT JIT_SCRIPT_TO_EXECUTE

## Set the exit code
(exit "$__jit_runtime_final_status")
