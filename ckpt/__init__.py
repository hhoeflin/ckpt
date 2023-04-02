"""A package to create checkpoints in code for easier debugging."""

__version__ = "0.2.0"

from .config import get_ckpt_dir, set_ckpt_dir
from .decorator import ckpt
from .task import Task, stack

__all__ = ["ckpt", "get_ckpt_dir", "set_ckpt_dir", "Task", "last", "stack"]
