# coding: utf-8

from functools import partial

RING264 = 2 ** 64
RING232 = 2 ** 32


def djb2(string_to_hash, modulo=RING232):
    # От выбора начального значения абсолютно ничего не зависит
    h = 5381
    ht = 0

    ord_func = ord
    try:
        ord_func(string_to_hash[0])
    except TypeError:
        # bytearray
        ord_func = lambda x: x
    except IndexError:
        return h

    for c in string_to_hash:
        # В исходнике явно используется тип unsigned char. В Python также символы не имеют знака
        # Имитимируем C - в питоне длинные числа по умолчанию, нам необходимо умножать их в кольце 2**64
        # Потребуется ли char со знаком или без зависит от конкретной реализации целевой хеш-функции
        # При необходимости можно имитировать знаковый char:
        # from ctypes import c_int8
        # h = (ht + c_int8(c).value) % modulo
        ht = (h * 33) % modulo
        h = (ht + ord_func(c)) % modulo

    return h

djb2_32 = partial(djb2, modulo=RING232)
# Not authentic, but probably OK
djb2_64 = partial(djb2, modulo=RING264)
