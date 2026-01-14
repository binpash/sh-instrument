
## Shell-Instrument

A shell script instrumentation engine that can preprocess a script, stub out fragments of it with calls to a JIT engine, and then allows the user to implement any form of analysis or instrumentation at runtime, before the fragment runs.

It includes a [preprocessor](/preprocessor/) and a [just-in-time engine](/jit.sh).

TODOs:
- Separate the preprocessor from the runner python script
- The specific should become its own library
- Add CI
