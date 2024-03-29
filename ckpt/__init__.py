"""A package to create checkpoints in code for easier debugging."""

__version__ = "0.2.4"

from .config import get_ckpt_dir, set_ckpt_dir
from .decorator import ckpt
from .task import PickleError, Task, load_module_from_file, stack

__all__ = [
    "ckpt",
    "get_ckpt_dir",
    "set_ckpt_dir",
    "Task",
    "stack",
    "load_module_from_file",
    "PickleError",
]
