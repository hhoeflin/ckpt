from ckpt import ckpt


@ckpt(active=True)
def outer(a, b):
    print(a)
    print(b)
    inner(a * 2, b * 2)


@ckpt(active=True)
def inner(c, d):
    print(c + d)
    print(c)
    print(d)
    e = c + d
    raise Exception()


@ckpt(active=True)
def function_copy():
    inner_copy = inner
    raise Exception()


if __name__ == "__main__":
    try:
        outer(a=5, b=3)
    except:
        pass

    try:
        function_copy()
    except:
        pass
