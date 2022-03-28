import inspect

from ckpt import checkpoint


@checkpoint(cond=True)
def outer(a, b):
    print(a)
    print(b)
    inner(a * 2, b * 2)


@checkpoint(cond=True)
def inner(c, d):
    print(c + d)
    print(c)
    print(d)


if __name__ == "__main__":
    outer(a=5, b=3)
