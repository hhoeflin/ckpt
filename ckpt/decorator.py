import sys
from dataclasses import dataclass
from functools import partial
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple, Union

import dill as pickle

from .config import ckpt_file, get_ckpt_dir


@dataclass
class Task:
    module_name: str
    module_file: str
    func_name: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]

    @classmethod
    def from_func(cls, func, *args, **kwargs):
        """
        Create the task using a given function.
        """

        # for the function, we need to find out the
        # module_name, module_file and function name

        module_spec = sys.modules[func.__module__].__spec__
        assert module_spec is not None
        module_name = module_spec.name
        module_file = module_spec.origin

        assert module_file is not None

        func_name = func.__name__

        return cls(
            module_name=module_name,
            module_file=module_file,
            func_name=func_name,
            args=args,
            kwargs=kwargs,
        )

    def to_partial(self) -> partial:
        """Return a partial object."""
        try:
            imp_mod = import_module(self.module_name)
        except ModuleNotFoundError:
            # add the directory of the file to the path and try again
            sys.path.insert(0, str(Path(self.module_file).parent))
            imp_mod = import_module(self.module_name)
            # and take it off again
            sys.path.pop(0)

        decorated_func = getattr(imp_mod, self.func_name)

        # check if this is a checkpoint wrapper; should be the case
        if isinstance(decorated_func, CkptWrapper):
            return partial(decorated_func.func, *self.args, **self.kwargs)
        else:
            raise Exception(
                f"Expected object of class CheckpointWrapper, but got {type(decorated_func)}"
            )

    def __call__(self):
        return self.to_partial()()


class CkptWrapper:
    def __init__(
        self,
        func: Callable,
        ckpt_name: str,
        cond: Union[bool, Callable[..., bool]],
        on_error: bool,
    ):
        self.func = func
        self.ckpt_name = ckpt_name
        self.cond = cond
        self.on_error = on_error

    def __call__(self, *args, **kwargs):
        """Performs saving the function and arguments when necessary."""
        task = Task.from_func(self.func, *args, **kwargs)
        # go through the condition if provided
        if isinstance(self.cond, bool):
            save = self.cond
        elif isinstance(self.cond, Callable):
            save = self.cond(*args, **kwargs)
        else:
            raise TypeError("cond needs to be bool or a Callable")

        if save:
            _save_ckpt(task, self.ckpt_name)
        try:
            return self.func(*args, **kwargs)
        except Exception as e:
            if self.on_error:
                _save_ckpt(task, self.ckpt_name)
            raise e


def checkpoint(
    name: Optional[str] = None,
    on_error: bool = True,
    cond: Union[bool, Callable[..., bool]] = False,
) -> Callable[[Callable], Any]:
    """
    Create a checkpointing decorator.

    Args:
        ckpt_name (Optional[str]): Name of the checkpoint when saved.
        on_error (bool): Whether to save checkpoint when an error occurs.
        cond (Union[bool, Callable[..., bool]]): Condition under which to save checkpoint.
            If a Callable, all parameters of the wrapped function should be passed
            and it has to return a boolean.

    Returns:
        A decorator function.
    """

    def ckpt_worker(func: Callable):
        if name is None:
            ckpt_name = func.__name__
        else:
            ckpt_name = name

        return CkptWrapper(func=func, ckpt_name=ckpt_name, on_error=on_error, cond=cond)

    return ckpt_worker


def _save_ckpt(task, ckpt_name):
    ckpt_dir = get_ckpt_dir()

    ckpt_dir.mkdir(parents=True, exist_ok=True)

    with ckpt_file(ckpt_dir, ckpt_name).open("wb") as f:
        pickle.dump(task, f)
