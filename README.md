
## Shell-Instrument

A shell script instrumentation engine that can preprocess a script, stub out fragments of it with calls to a JIT engine, and then allows the user to implement any form of analysis or instrumentation at runtime, before the fragment runs.

It includes a [preprocessor](/preprocessor/), a script runner that behaves like a shell, and a [just-in-time engine](/jit.sh).

TODOs:
- Make the runner its own repo 
- Make the preprocessor its own repo and PyPI
- Use these in PaSh too
- Add CI
