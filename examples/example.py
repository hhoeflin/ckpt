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


if __name__ == "__main__":
    outer(a=5, b=3)
