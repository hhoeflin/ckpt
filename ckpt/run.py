from enum import Enum
from pathlib import Path
from typing import Optional

import dill as pickle

from .decorator import Task
from .task import stack


class DebuggerUnknownError(Exception):
    pass


class ShellUnknownError(Exception):
    pass


class DebuggerUnavailableError(Exception):
    pass


class ShellUnavailalbleError(Exception):
    pass


class Debuggers(Enum):
    """
    Enum of supported debuggers.
    """

    pudb = "pudb"
    ipdb = "ipdb"
    bpdb = "bpdb"
    pdb = "pdb"


class Shells(Enum):
    """
    Enum of supported shells.
    """

    ipython = "ipython"


def _use_debugger_single(debugger: Debuggers, start: bool, task: Task):
    """Load the appropriate debugging module."""
    if debugger == Debuggers.pdb:
        import pdb

        debug_module = pdb
    elif debugger == Debuggers.pudb:
        import pudb

        debug_module = pudb
    elif debugger == Debuggers.ipdb:
        import ipdb

        debug_module = ipdb
    else:
        raise DebuggerUnknownError(f"Unknown debugger {debugger}")

    # call the task with the identified debugger
    partial_obj = task.to_partial()
    if start:
        try:
            stack.append(task)
            debug_module.runcall(partial_obj)  # type: ignore
        except:
            raise
        finally:
            stack.pop()
    else:
        try:
            stack.append(task)
            partial_obj()
        except Exception:
            debug_module.post_mortem()
        finally:
            stack.pop()


def _use_debugger(debugger: Optional[Debuggers], start: bool, task: Task):
    if debugger is None:
        debugger_list = [d for d in Debuggers]
    else:
        debugger_list = [debugger]

    for debugger in debugger_list:
        try:
            _use_debugger_single(debugger=debugger, start=start, task=task)
            return
        except ImportError:
            continue
        except:
            raise

    raise DebuggerUnavailableError(
        f"No debugger from {', '.join([d.value for d in debugger_list])} found."
    )


def _use_shell_single(shell: Shells, start: bool, task: Task):
    """Load the appropriate debugging module."""

    func_module = task.func_module()
    ns = task.ns(start=start)

    if start or task.locals is None:
        entry_msg = (
            f"Function '{task.func_name}' in module '{task.module_name} at start"
        )
    else:
        entry_msg = (
            f"Function '{task.func_name}' in module '{task.module_name} at locals"
        )

    if shell == Shells.ipython:
        from IPython.terminal.embed import InteractiveShellEmbed

        ipy_shell = InteractiveShellEmbed(banner=entry_msg)
        ipy_shell.mainloop(local_ns=ns, module=func_module)

    else:
        raise ShellUnknownError(f"Unknown shell {shell}")


def _use_shell(shell: Optional[Shells], start: bool, task: Task):
    if shell is None:
        shell_list = [s for s in Shells]
    else:
        shell_list = [shell]

    for shell in shell_list:
        try:
            stack.append(task)
            _use_shell_single(shell=shell, start=start, task=task)
            return
        except ImportError:
            continue
        except:
            raise
        finally:
            stack.pop()

    raise ShellUnavailalbleError(
        f"No shell from {', '.join([s.value for s in shell_list])} found."
    )


def run_ckpt(
    ckpt_file: Path,
    debugger: Optional[Debuggers],
    shell: Optional[Shells],
    use_shell: bool,
    start: bool,
):
    """
    Run a checkpoint.

    Args:
        ckpt_file (Path): The checkpoint file to use.
        debugger (Optional[Debuggers]): The debugger to use.
        shell (Optional[Shells]): The shell to use.
        use_shell (bool): Should the shell or the debugger be used.
        start (bool): Start at the beginning of the function?
    """
    with ckpt_file.open("rb") as f:
        task = pickle.load(f)

    if use_shell:
        _use_shell(shell=shell, start=start, task=task)
    else:
        _use_debugger(debugger=debugger, start=start, task=task)
