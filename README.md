# Package for creating checkpoints during code development

The intent of this package is to make the code development process 
faster and easier. For this, the package provides the `ckpt` decorator
for functions. With this decorator, the function and its input arguments
will be stored (either when called or on error) so that it can later 
be called. 

This allows for 2 things:
- Quickly restart a function that has errors in the same form as before, without
  having to wait e.g. for complicated or slow preprocessing code
- Change other functions in the same or other modules, that can then be cleanly reloaded.


# How to use it

## Customizing storage location

If the environment variable `PYCKPT_DIR` is set, then it will be used to determine
the directory where checkpoints will be saved and searched.

Otherwise, from the current working directory and up all parent directories,
it searches for a `.pyckpt` hidden directory and uses that if present.

If none of these can be found, it falls back to a `pyckpt` subdirectory either
in `XDG_STATE_HOME` if available, or `${HOME}/.local/state` if not.

When using the command line 

```bash
ckpt init
```
it creates a `.pyckpt` in the current directory.

## Setting checkpoints
Usage is very simple. For any function that should be checkpointed, just use 
the `ckpt` decorator. 


```python
import ckpt

@ckpt.ckpt
def func(a, b):
    pass
```

By default, the function will be checkpointed every time it is called or when an error 
occurs. For only checkpointed when an error occurs, one can do

```python
import ckpt

@ckpt.ckpt(active=False)
def func(a, b):
    pass

```

For the `active` parameter, it can be a boolean, or itself a function that gets
called with all parameters of the function and returns a boolean.

## Using checkpoints

### Listing available checkpoints

```bash
cdip info
```

List the storage directory as well as a time-ordered list of created checkpoints.

### Running a checkpoint

```bash
cdip run [ckpt-name]

```

starts either a debugger or a shell with the function that was checkpointed loaded.
For the debugger, the options are to drop in at the beginning of the function or 
run it until an error occurs. For the shell, the options are to have only the 
variables passed at the beginning of the function available or alternatively any local
variables inside the function (e.g. if the function was checkpointed due to an error
occuring).

# When to use it

It is a potential alternative to `autoreload` in IPython, restarting the session
more often (especially when working directly on the command line). In this way, it is 
easier when encountering issues where autoreload isn't working.

It can also be used when running analysis scripts with a debugger, especially when
the analysis can be running long when restarting or certain steps should be skipped.
