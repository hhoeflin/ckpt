import inspect
import sys
from dataclasses import dataclass
from functools import partial
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import dill as pickle

import ckpt

from .config import ckpt_file, get_ckpt_dir


@dataclass
class Task:
    module_name: str
    module_file: str
    func_name: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    ckpt_name: str
    locals: Optional[Dict[str, Any]] = None

    @classmethod
    def from_func(cls, func, *args, **kwargs):
        """
        Create the task using a given function.
        """

        # for the function, we need to find out the
        # module_name, module_file and function name

        module = sys.modules[func.__module__]
        module_name = module.__name__
        module_file = module.__file__

        assert module_file is not None

        func_name = func.__name__

        return cls(
            module_name=module_name,
            module_file=module_file,
            func_name=func_name,
            args=args,
            kwargs=kwargs,
            ckpt_name=func_name,
        )

    def func_module(self):
        if self.module_name == "__main__":
            module_name = Path(self.module_file).stem
        else:
            module_name = self.module_name
        try:
            imp_mod = import_module(module_name)
        except ModuleNotFoundError:
            # add the directory of the file to the path and try again
            sys.path.insert(0, str(Path(self.module_file).parent))
            imp_mod = import_module(module_name)
            # and take it off again
            sys.path.pop(0)

        return imp_mod

    def to_partial(self) -> partial:
        """Return a partial object."""
        imp_mod = self.func_module()

        decorated_func = getattr(imp_mod, self.func_name)

        # check if this is a checkpoint wrapper; should be the case
        from .decorator import CkptWrapper  # avoid circularity

        if isinstance(decorated_func, CkptWrapper):
            return partial(decorated_func.func, *self.args, **self.kwargs)
        else:
            return partial(decorated_func, *self.args, **self.kwargs)

    def ns(self, start: bool = True):
        partial = self.to_partial()
        if start or self.locals is None:
            # get the locals from the function call
            sig = inspect.signature(partial.func)
            bound = sig.bind(*self.args, **self.kwargs)
            bound.apply_defaults()
            res_ns = {k: v for k, v in bound.arguments.items()}
        else:
            res_ns = self.locals.copy()

        res_ns["_ckpt"] = ckpt
        return res_ns

    def __call__(self):
        return self.to_partial()()

    def save(self, ckpt_name):

        ckpt_dir = get_ckpt_dir()
        ckpt_dir.mkdir(parents=True, exist_ok=True)

        with ckpt_file(ckpt_dir, ckpt_name).open("wb") as f:
            pickle.dump(self, f)

stack: List[Task] = []
