from functools import partial, wraps
from typing import Any, Callable

state = {"level": -1}


def checkpoint() -> Callable[[Callable], Any]:
    """
    Create a checkpointing decorator.

    Returns:
        A decorator function.
    """

    def ckpt_worker(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            """Performs saving the function and arguments when necessary."""
            try:
                state["level"] += 1
                # we save a partial func for running later when needed
                partial_func = partial(func, *args, **kwargs)
            finally:
                state["level"] -= 1

            return func(*args, **kwargs)

        return wrapper

    return ckpt_worker
