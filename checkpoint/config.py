import hashlib
import os
import tempfile
from pathlib import Path
from typing import List, Optional

from git.repo import Repo


def repo_root(path: Path = Path(".")) -> Optional[Path]:
    """
    Find the root of the current repository.

    Args:
        path (Path): A path in the repository.

    Returns:
        Optional[Path]: The root of the repo if it is a repo, None otherwise.

    """
    try:
        repo = Repo(path, search_parent_directories=True)
        if repo.working_tree_dir is None:
            return None
        else:
            return Path(repo.working_tree_dir)
    except Exception:
        pass

    return None


def set_ckpt_dir(
    ckpt_dir: Path = Path(
        os.environ.get("CKPT_DIR", Path(tempfile.gettempdir()) / "checkpoint")
    ),
    repo_root_dir: Optional[Path] = repo_root(Path(os.getcwd())),
):
    """
    Function to derive the ckpt directory.

    This is called once at initialization. The reason is that it could change
    if the working directory is changed and this would be undesirable
    behavior.
    """
    if repo_root_dir is None:
        ckpt_dir = ckpt_dir / "default"
    else:
        hash_str = hashlib.md5(str(repo_root_dir.resolve()).encode()).hexdigest()
        ckpt_dir = ckpt_dir / hash_str

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
state = dict()
set_ckpt_dir()
