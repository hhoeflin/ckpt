import importlib.util
import inspect
import sys
from collections.abc import MutableMapping, MutableSequence
from dataclasses import dataclass
from functools import partial
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

import cloudpickle as pickle
import loguru

import ckpt

from .config import get_ckpt_dir, get_ckpt_file


class PickleError(Exception):
    pass


class Pickler:
    def __init__(self, module_file: Path):
        self.module_file = module_file

    def dumps(self, value: Any) -> bytes:
        try:
            res = pickle.dumps(value)
        except Exception as e:
            res = pickle.dumps(PickleError(str(e)))

        return res

    def loads(self, value: bytes) -> Any:
        try:
            return pickle.loads(value)
        except:
            # maybe we have to attach the location of the original module to the
            # search path
            sys.path.insert(0, str(Path(self.module_file).parent))
            try:
                return pickle.loads(value)
            except:
                raise
            finally:
                # and take it off again
                sys.path.pop(0)


class DictPickleProxy(MutableMapping):
    def __init__(
        self,
        initialdata,
        pickler: Pickler,
    ):
        super().__init__()
        self.pickler = pickler
        self.data: Dict[str, bytes] = {}
        self.update(initialdata)

    def __getitem__(self, key):
        return self.pickler.loads(self.data[key])

    def __setitem__(self, key, value):
        self.data[key] = self.pickler.dumps(value)
        if isinstance(self.data[key], PickleError):
            loguru.logger.warning(f"Could not pickle item {key}: {str(value)}")

    def __delitem__(self, key):
        del self.data[key]

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return self.data.__iter__()


class ListPickleProxy(MutableSequence):
    def __init__(
        self,
        initialdata,
        pickler: Pickler,
    ):
        super().__init__()
        self.data: List[bytes] = []
        self.pickler = pickler
        self.extend(initialdata)

    def __getitem__(self, key):
        return self.pickler.loads(self.data[key])

    def __setitem__(self, key, value):
        self.data[key] = self.pickler.dumps(value)
        if isinstance(self.data[key], PickleError):
            loguru.logger.warning(f"Could not pickle item {key}: {str(value)}")

    def __delitem__(self, key):
        del self.data[key]

    def __len__(self):
        return len(self.data)

    def insert(self, idx, obj):
        self.data.insert(idx, self.pickler.dumps(obj))


class Task:
    module_name: str
    module_file: Path
    func_name: str
    ckpt_name: str
    _args: ListPickleProxy
    _kwargs: DictPickleProxy
    _locals: Optional[DictPickleProxy] = None

    def __init__(
        self,
        module_name: str,
        module_file: Path,
        func_name: str,
        ckpt_name: str,
        args: Sequence[Any],
        kwargs: Dict[str, Any],
    ):
        self.module_name = module_name
        self.module_file = module_file
        self.func_name = func_name
        self.ckpt_name = ckpt_name

        self._args = ListPickleProxy(args, pickler=Pickler(module_file))
        self._kwargs = DictPickleProxy(kwargs, pickler=Pickler(module_file))

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
            return partial(decorated_func.func, *self._args, **self._kwargs)
        else:
            return partial(decorated_func, *self._args, **self._kwargs)

    def ns(self, start: bool = True):
        partial = self.to_partial()
        if start or self._locals is None:
            # get the locals from the function call
            sig = inspect.signature(partial.func)
            bound = sig.bind(*self._args, **self._kwargs)
            bound.apply_defaults()
            res_ns = {k: v for k, v in bound.arguments.items()}
        else:
            res_ns = {k: v for k, v in self._locals.items()}

        res_ns["_ckpt"] = ckpt
        return res_ns

    def store_locals(
        self,
        locals: Optional[Dict[str, Any]] = None,
        stack_depth: int = 1,
        save: bool = True,
    ):
        if locals is not None:
            to_store = locals
        else:
            frame = sys._getframe(stack_depth)
            if frame is None:
                raise Exception("Can't access frame")
            else:
                to_store = clean_locals(frame.f_locals)

        self.locals = to_store

        if save:
            self.save()

    def __call__(self):
        return self.to_partial()()

    def save(self):

        ckpt_dir = get_ckpt_dir()
        ckpt_dir.mkdir(parents=True, exist_ok=True)

        with get_ckpt_file(self.ckpt_name).open("wb") as f:
            pickle.dump(self, f)

    @property
    def locals(self) -> Optional[DictPickleProxy]:
        return self._locals

    @locals.setter
    def locals(self, value: Union[None, Dict[str, Any], DictPickleProxy]):
        if value is None:
            self._locals = None
        elif isinstance(value, DictPickleProxy):
            self._locals = value
        elif isinstance(value, dict):
            self._locals = DictPickleProxy(value, pickler=Pickler(self.module_file))
        else:
            raise ValueError("Locals has to be a dict, none or DictPickleProxy")


stack: List[Task] = []


def is_run_from_ipython():
    try:
        __IPYTHON__  # type: ignore
        return True
    except NameError:
        return False


def clean_locals(locals_dict: Dict[str, Any]) -> Dict[str, Any]:

    # detect if in IPython, if yes, exclude certain variables from locals
    if is_run_from_ipython():
        vars_to_omit = [
            "_ih",
            "_oh",
            "_dh",
            "In",
            "Out",
            "get_ipython",
            "exit",
            "quit",
            "open",
            "_",
            "__",
            "___",
            "_i",
            "_ii",
            "_iii",
            "_i1",
        ]
    else:
        vars_to_omit = []

    l = {k: v for k, v in locals_dict.items() if k not in vars_to_omit}
    return l


def load_module_from_file(
    file: Union[Path, str],
    global_name: Optional[str] = "**",
    module_name: Optional[str] = None,
    stack_depth: int = 1,
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

    frame = sys._getframe(stack_depth)
    if global_name is None:
        frame.f_globals[module_name] = module
    elif global_name == "*":
        # read all items into globals that are not hidden
        frame.f_globals.update(
            {k: v for (k, v) in inspect.getmembers(module) if not k.startswith("_")}
        )
        pass
    elif global_name == "**":
        # read all items into globals
        frame.f_globals.update({k: v for (k, v) in inspect.getmembers(module)})
    else:
        frame.f_globals[global_name] = module
