import dill as pickle

from ckpt import ckpt, set_ckpt_dir
from ckpt.config import ckpt_file, get_ckpt_dir


def func_normal(a, b=1):
    pass


def func_error(a, b=1):
    a = 2
    b = 3
    c = 4
    raise Exception()


class TestCkpt:
    def test_ckpt_normal(self, tmp_path):
        set_ckpt_dir(tmp_path)
        ckpt(active=True)(func_normal)(a=0)

        file = ckpt_file(get_ckpt_dir(), "func_normal")

        with file.open("rb") as f:
            task = pickle.load(f)
            assert task.ns(start=True) == dict(a=0, b=1)
            assert task.ns(start=False) == dict(a=0, b=1)

    def test_ckpt_error(self, tmp_path):
        set_ckpt_dir(tmp_path)
        try:
            ckpt()(func_error)(a=0)
        except:
            pass

        file = ckpt_file(get_ckpt_dir(), "func_error")

        with file.open("rb") as f:
            task = pickle.load(f)
            assert task.ns(start=True) == dict(a=0, b=1)
            assert task.ns(start=False) == dict(a=2, b=3, c=4)
