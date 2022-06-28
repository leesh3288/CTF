#!/usr/bin/python3
from Crypto.Cipher import DES
import os

FLAG = open("flag.txt", 'rb').read()
assert len(FLAG) == 96

level = int(input("Select a security level > "))
if level < 42:
    print(f"Level {level} is not enough I guess...?")
    exit(-1)

dat = FLAG
for i in range(level):
    key = bytes.fromhex(input(f"Select your own key[{i}] in hex format > "))
    if len(key) != 8 or len(set(key)) != 8:
        print("bye..")
        exit(-1)
    dat = DES.new(key, DES.MODE_ECB).encrypt(dat)


print("enc :", dat.decode())