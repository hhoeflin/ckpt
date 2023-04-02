import os
from pathlib import Path
from typing import Any, Dict, List, Optional


def search_parent_ckpt_dir(cwd: Path) -> Optional[Path]:
    for path in [cwd] + list(cwd.parents):
        cand_dir = path / ".pyckpt"
        if cand_dir.exists() and cand_dir.is_dir():
            return cand_dir

    return None


def user_ckpt_dir() -> Optional[Path]:
    if "HOME" in os.environ:
        user_root_dir = Path(
            os.environ.get("XDG_STATE_HOME", f"{os.environ['HOME']}/.local/.state")
        )
        return user_root_dir / "pyckpt"
    else:
        return None


def resolve_ckpt_dir(
    ckpt_dir: Optional[Path] = None,
) -> Path:
    if ckpt_dir is not None:
        return ckpt_dir

    if "PYCKPT_DIR" in os.environ:
        return Path(os.environ["PYCKPT_DIR"])

    if (ckpt_dir := search_parent_ckpt_dir(Path.cwd())) is not None:
        return ckpt_dir

    if (ckpt_dir := user_ckpt_dir()) is not None:
        return ckpt_dir

    raise Exception("Could not find ckpt-directory")


def set_ckpt_dir(
    ckpt_dir: Optional[Path] = None,
):
    """
    Function to derive the ckpt directory.

    This is called once at initialization. The reason is that it could change
    if the working directory is changed and this would be undesirable
    behavior.
    """
    ckpt_dir = resolve_ckpt_dir(ckpt_dir)

    state["ckpt_dir"] = ckpt_dir


def get_ckpt_dir() -> Path:
    return state["ckpt_dir"]


def ckpt_file(ckpt_dir: Path, ckpt_name: str) -> Path:
    return ckpt_dir / f"{ckpt_name}.pkl"


def get_ckpts_sorted() -> List[Path]:
    """
    Find checkpoint file that was created last and return its name.
    """
    ckpt_dir = get_ckpt_dir()
    all_files = sorted(
        list(ckpt_dir.glob("*.pkl")), key=lambda file: file.stat().st_mtime
    )
    return all_files


# the ckpt_directory to use
state: Dict[str, Any] = dict()
set_ckpt_dir()
