import importlib.util
import inspect
import sys
from dataclasses import dataclass
from functools import partial
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cloudpickle as pickle

import ckpt

from .config import get_ckpt_dir, get_ckpt_file


@dataclass
class Task:
    module_name: str
    module_file: Path
    func_name: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    ckpt_name: str
    locals_pkl: Optional[bytes] = None

    @classmethod
    def from_func(cls, func, *args, **kwargs):
        """
        Create the task using a given function.
        """

        # for the function, we need to find out the
        # module_name, module_file and function name

        module = sys.modules[func.__module__]
        module_name = module.__name__
        module_file = getattr(module, "__file__", None)

        assert module_file is not None

        func_name = func.__name__

        return cls(
            module_name=module_name,
            module_file=Path(module_file).absolute(),
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
            try:
                imp_mod = import_module(module_name)
            except:
                raise
            finally:
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

    def store_locals(self, stack_depth=1):
        frame = sys._getframe(stack_depth)
        if frame is None:
            raise Exception("Can't access frame")
        else:
            self.locals = frame.f_locals

    def __call__(self):
        return self.to_partial()()

    def save(self, ckpt_name):

        ckpt_dir = get_ckpt_dir()
        ckpt_dir.mkdir(parents=True, exist_ok=True)

        with get_ckpt_file(ckpt_name).open("wb") as f:
            pickle.dump(self, f)

    @property
    def locals(self) -> Optional[Dict[str, Any]]:
        if self.locals_pkl is None:
            return None
        try:
            return pickle.loads(self.locals_pkl)
        except:
            # maybe we have to attach the location of the original module to the
            # search path
            sys.path.insert(0, str(Path(self.module_file).parent))
            try:
                return pickle.loads(self.locals_pkl)
            except:
                raise
            finally:
                # and take it off again
                sys.path.pop(0)

    @locals.setter
    def locals(self, value):
        self.locals_pkl = pickle.dumps(value)


stack: List[Task] = []


def clean_locals(locals_dict: Dict[str, Any]) -> Dict[str, Any]:
    l = locals_dict.copy()

    # detect if in IPython, if yes, exclude certain variables from locals

    return l


def load_module_from_file(
    file: Union[Path, str],
    module_name: Optional[str] = None,
):
    file = Path(file)
    if module_name is None:
        module_name = file.stem
    spec = importlib.util.spec_from_file_location(module_name, str(file))
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
