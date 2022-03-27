import hashlib
import os
import tempfile
from pathlib import Path
from typing import Optional

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


def derive_ckpt_dir(
    repo_root_dir: Optional[Path] = repo_root(Path(os.getcwd())),
) -> Path:
    """
    Function to derive the ckpt directory.

    This is called once at initialization. The reason is that it could change
    if the working directory is changed and this would be undesirable
    behavior.
    """
    ckpt_dir = Path(os.environ.get("CKPT_DIR", tempfile.gettempdir()))
    # depending on the repo root, add subdirectory

    if repo_root_dir is None:
        ckpt_dir = ckpt_dir / "default"
    else:
        hash_str = hashlib.md5(str(repo_root_dir.resolve()).encode()).hexdigest()
        ckpt_dir = ckpt_dir / hash_str

    return ckpt_dir


# the ckpt_directory to use
ckpt_dir = derive_ckpt_dir()
