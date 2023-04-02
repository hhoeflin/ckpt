from typing import Any, Callable, Dict, Optional, Tuple, Union

from .task import Task, stack


class CkptWrapper:
    def __init__(
        self,
        func: Callable,
        ckpt_name: str,
        active: Union[bool, Callable[..., bool]],
        on_error: bool,
        save_locals: bool,
    ):
        self.func = func
        self.ckpt_name = ckpt_name
        self.active = active
        self.on_error = on_error
        self.save_locals = save_locals

    def __call__(self, *args, **kwargs):
        """Performs saving the function and arguments when necessary."""
        task = Task.from_func(self.func, *args, **kwargs)
        task.ckpt_name = self.ckpt_name
        # go through the condition if provided
        if isinstance(self.active, bool):
            save = self.active
        elif isinstance(self.active, Callable):
            save = self.active(*args, **kwargs)
        else:
            raise TypeError("cond needs to be bool or a Callable")

        if save:
            stack.append(task)
            task.save(self.ckpt_name)
        try:
            return self.func(*args, **kwargs)
        except Exception as e:
            if self.on_error:
                if self.save_locals:
                    # we get the locals from the traceback and save it as well
                    tb = e.__traceback__
                    if tb is not None and tb.tb_next is not None:
                        task.locals = tb.tb_next.tb_frame.f_locals
                task.save(self.ckpt_name)
            raise
        finally:
            stack.pop()


def ckpt(
    name: Optional[str] = None,
    on_error: bool = True,
    active: Union[bool, Callable[..., bool]] = False,
    save_locals: bool = True,
) -> Callable[[Callable], Any]:
    """
    Create a checkpointing decorator.

    Args:
        ckpt_name (Optional[str]): Name of the checkpoint when saved.
        on_error (bool): Whether to save checkpoint when an error occurs.
        cond (Union[bool, Callable[..., bool]]): Condition under which to save checkpoint.
            If a Callable, all parameters of the wrapped function should be passed
            and it has to return a boolean.

    Returns:
        A decorator function.
    """

    def ckpt_worker(func: Callable):
        if name is None:
            ckpt_name = func.__name__
        else:
            ckpt_name = name

        return CkptWrapper(
            func=func,
            ckpt_name=ckpt_name,
            on_error=on_error,
            active=active,
            save_locals=save_locals,
        )

    return ckpt_worker
