"""Stub for util_spec - speculative execution not supported in runtime-only mode"""

def save_df_region(*args, **kwargs):
    raise NotImplementedError("Speculative mode not supported in runtime-only version")
