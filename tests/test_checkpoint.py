import sys
from pathlib import Path

import dill as pickle

import ckpt as checkpoint
from ckpt import ckpt, set_ckpt_dir
from ckpt.config import ckpt_file, get_ckpt_dir
from ckpt.task import Task


def func_normal(a, b=1):
    pass


def func_error(a, b=1):
    a = 2
    b = 3
    c = 4
    raise Exception()


class TestCkpt:
    def test_ckpt_normal(self):
        ckpt(active=True)(func_normal)(a=0)

        file = ckpt_file(get_ckpt_dir(), "func_normal")

        with file.open("rb") as f:
            task = pickle.load(f)
            assert task.ns(start=True) == dict(a=0, b=1, _ckpt=checkpoint)
            assert task.ns(start=False) == dict(a=0, b=1, _ckpt=checkpoint)

    def test_ckpt_error(self):
        try:
            ckpt()(func_error)(a=0)
        except:
            pass

        file = ckpt_file(get_ckpt_dir(), "func_error")

        with file.open("rb") as f:
            task = pickle.load(f)
            assert task.ns(start=True) == dict(a=0, b=1, _ckpt=checkpoint)
            assert task.ns(start=False) == dict(a=2, b=3, c=4, _ckpt=checkpoint)

    def test_deep_import(self):
        sys.path.append(str(Path(__file__).parent))
        from mod_a.mod_b import mod_b_func

        sys.path.pop()
        task = Task.from_func(mod_b_func)
        assert task.module_name == "mod_a.mod_b"
        assert task.func_name == "mod_b_func"
