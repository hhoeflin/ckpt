# Package for creating checkpoints during code creation

The intent of this package is to make the code development process 
faster and easier. For this, the package provides the `ckpt` decorator
for functions. With this decorator, the function and its input arguments
will be stored (either when called or on error) so that it can later 
be called. 

This allows for 2 things:
- Quickly restart a function that has errors in the same form as before, without
  having to wait e.g. for complicated or slow preprocessing code
- Change other functions in the same or other modules, that can then be cleanly reloaded.

As such it works as a potential alternative to `autoreload` in IPython, restarting the session
more often (especially when working directly on the command line).
