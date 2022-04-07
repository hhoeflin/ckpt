"""A package to create checkpoints in code for easier debugging."""

__version__ = "0.1.2"

from .config import get_ckpt_dir, set_ckpt_dir
from .decorator import checkpoint

__all__ = ["checkpoint", "get_ckpt_dir", "set_ckpt_dir"]
