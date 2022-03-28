import shutil
from pathlib import Path
from typing import Optional

import typer

from .config import ckpt_file, get_ckpt_dir, get_ckpts_sorted, set_ckpt_dir
from .run import Debuggers, run_ckpt

app = typer.Typer()


@app.callback()
def dir(ckpt_dir: Path = typer.Option(None, help="Root checkpoint directory")):
    if ckpt_dir is not None:
        set_ckpt_dir(ckpt_dir=ckpt_dir)


@app.command()
def clear():
    """Clear the current checkpoint directory."""
    ckpt_dir = get_ckpt_dir()
    typer.echo(f"Removing directory {ckpt_dir}")
    if ckpt_dir.exists():
        shutil.rmtree(ckpt_dir)


@app.command()
def info():
    """Print summary information of current checkpoint."""
    typer.echo(f"Checkpoint directory: {get_ckpt_dir()}")
    typer.echo(f"Checkpoint names: {', '.join([x.stem for x in get_ckpts_sorted()])}")


@app.command()
def run(
    name: Optional[str] = typer.Argument(
        None, help="Name of checkpoint. If unspecified, use last one."
    ),
    debugger: Debuggers = typer.Option(
        "pdb", "-d", "--debugger", help="The debugger to use."
    ),
    start: bool = typer.Option(
        False,
        help="Debugging should start at beginning of function instead of at error.",
    ),
):
    """Execute a checkpoint."""
    if name is None:
        all_ckpts = get_ckpts_sorted()
        if len(all_ckpts) == 0:
            typer.echo("No checkpoint available.")
            raise typer.Exit()
        else:
            use_ckpt_file = all_ckpts[-1]
    else:
        use_ckpt_file = ckpt_file(get_ckpt_dir(), name)

    # check that the file exists
    if not use_ckpt_file.exists():
        typer.echo(f"File {str(use_ckpt_file)} does not exist.")
        raise typer.Exit()

    run_ckpt(ckpt_file=use_ckpt_file, debugger=debugger, start=start)
