import pytest

import ckpt


@pytest.fixture(scope="session", autouse=True)
def ckpt_dir(tmp_path_factory):
    ckpt.set_ckpt_dir(tmp_path_factory.mktemp(".pyckpt"))
