import tempfile
from pathlib import Path

from ckpt.config import get_ckpt_dir, set_ckpt_dir


def test_derive_ckpt_dir():
    set_ckpt_dir(repo_root_dir=None)
    assert get_ckpt_dir() == Path(tempfile.gettempdir()) / "checkpoint" / "default"
    set_ckpt_dir(repo_root_dir=Path("test_repo"))
    assert (
        get_ckpt_dir()
        == Path(tempfile.gettempdir())
        / "checkpoint"
        / "6aa03e670bb12af8966a25e13eb172af"
    )
