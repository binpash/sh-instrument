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

## Parse arguments to separate preprocessing and execution concerns
## We need to extract: input script, shell name, script args, and flags

# Initialize variables
input_script=""
shell_name="pash"
script_args=()
bash_flag=""
preprocess_only=false
output_preprocessed=false
allexport_flag="+a"
verbose_flag=""
xtrace_flag=""
command_mode=""
command_text=""

# Parse arguments
i=1
while [ $i -le $# ]; do
    arg="${!i}"
    next_i=$((i+1))
    next_arg="${!next_i}"

    case "$arg" in
        -c|--command)
            command_mode="-c"
            command_text="$next_arg"
            i=$next_i
            ;;
        --preprocess_only)
            preprocess_only=true
            ;;
        --output_preprocessed)
            output_preprocessed=true
            ;;
        --bash)
            bash_flag="--bash"
            ;;
        -a)
            allexport_flag="-a"
            ;;
        +a)
            allexport_flag="+a"
            ;;
        -v)
            verbose_flag="-v"
            ;;
        -x)
            xtrace_flag="-x"
            ;;
        -d|--debug)
            # Already handled above, skip
            i=$next_i
            ;;
        --log_file)
            # Skip log_file argument
            i=$next_i
            ;;
        --version|-t|--time)
            # Skip these flags
            ;;
        *)
            # This is either the input script or a script argument
            if [ -z "$input_script" ] && [ -z "$command_mode" ]; then
                input_script="$arg"
                shell_name="$arg"
            else
                script_args+=("$arg")
            fi
            ;;
    esac
    i=$((i+1))
done

# Handle -c command mode
if [ -n "$command_mode" ]; then
    # Create temporary file for command text
    input_script=$(mktemp)
    echo "$command_text" > "$input_script"
    # If there are additional args, first becomes shell_name
    if [ ${#script_args[@]} -gt 0 ]; then
        shell_name="${script_args[0]}"
        script_args=("${script_args[@]:1}")
    fi
fi

# Create temporary file for preprocessed output
preprocessed_output=$(mktemp)

# Step 1: Call preprocessor.py to transform the script
__jit_redir_all_output echo "PaSh: Calling preprocessor..."
"$PYTHON_VENV" "$PASH_TOP/preprocessor/preprocessor.py" \
    "$input_script" \
    --output "$preprocessed_output" \
    --runtime-executable "$PASH_TOP/jit.sh" \
    --debug "$PASH_DEBUG_LEVEL" \
    $bash_flag

preprocessor_exit_code=$?

if [ $preprocessor_exit_code -ne 0 ]; then
    __jit_redir_all_output echo "PaSh: Preprocessor failed with exit code $preprocessor_exit_code"
    exit $preprocessor_exit_code
fi

# If preprocess_only flag was set, just exit
if [ "$preprocess_only" = true ]; then
    if [ "$output_preprocessed" = true ]; then
        cat "$preprocessed_output"
    fi
    exit 0
fi

# Step 2: Call runner.sh to execute the preprocessed script
__jit_redir_all_output echo "PaSh: Calling runner..."
"$PASH_TOP/runner.sh" \
    "$preprocessed_output" \
    "$shell_name" \
    "${script_args[@]}" \
    $allexport_flag \
    $verbose_flag \
    $xtrace_flag \
    --debug "$PASH_DEBUG_LEVEL"

runner_exit_code=$?

# Clean up temporary files if we created them
if [ -n "$command_mode" ]; then
    rm -f "$input_script"
fi
rm -f "$preprocessed_output"

exit $runner_exit_code
