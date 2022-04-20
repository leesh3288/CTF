#!/usr/bin/python3.10
import base64
import types

names = base64.b64decode(input('Enter names: '), validate=False)
code = base64.b64decode(input('Enter code: '), validate=False)

def f():
    pass

f.__code__ = f.__code__.replace(
    co_names=(*types.FunctionType(f.__code__.replace(co_code=names),{})(),),
    co_code=code
)
print(f())
