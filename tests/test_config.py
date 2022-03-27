import tempfile
from pathlib import Path

from checkpoint.config import derive_ckpt_dir


def test_derive_ckpt_dir():
    assert derive_ckpt_dir(None) == Path(tempfile.gettempdir()) / "default"
    assert (
        derive_ckpt_dir(Path("test_repo"))
        == Path(tempfile.gettempdir()) / "6aa03e670bb12af8966a25e13eb172af"
    )
