from enum import Enum
from pathlib import Path

import dill as pickle


class Debuggers(Enum):
    """
    Enum of supported debuggers.
    """

    pdb = "pdb"
    ipdb = "ipdb"
    pudb = "pudb"


def _get_debugger(debugger: Debuggers):
    """Load the appropriate debugging module."""
    if debugger == Debuggers.pdb:
        import pdb

        return pdb
    elif debugger == Debuggers.pudb:
        import pudb

        return pudb
    elif debugger == Debuggers.ipdb:
        import ipdb

        return ipdb
    else:
        raise ValueError(f"Unknown debugger {debugger}")


def run_ckpt(ckpt_file: Path, debugger: Debuggers, start: bool = False):
    """
    Run a checkpoint.

    Args:
        ckpt_file (Path): The checkpoint file to use.
        debugger (Debuggers): The debugger to use.
        start (bool): Start at the beginning of the function?
    """
    debug_module = _get_debugger(debugger)

    with ckpt_file.open("rb") as f:
        task = pickle.load(f)
        partial_obj = task.to_partial()
    if start:
        partial_obj.func.__closure__
        debug_module.runcall(partial_obj)  # type: ignore
    else:
        try:
            partial_obj()
        except Exception:
            debug_module.post_mortem()
