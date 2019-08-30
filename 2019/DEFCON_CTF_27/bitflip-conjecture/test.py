#!/usr/bin/env python2

from pwn import *

context.arch = "amd64"

payload = """
sub al, dl
js $+0x7f
push rax
push rax
nop
nop
xor edi, edi
inc edi
mov eax, edi
call goA
.string "I am Invincible!"
goA:
pop rsi
xor edx, edx
mov dl, 16
syscall
xor edi, edi
mov al, 60
syscall
{}
xor edi, edi
inc edi
mov eax, edi
call goB
.string "I am Invincible!"
goB:
pop rsi
xor edx, edx
mov dl, 16
syscall
ret
""".format("nop\n" * 82)

assembled = asm(payload)

with open("shellcode", "wb") as f:
    f.write(assembled)

import subprocess
import os

dn = open(os.devnull, "w")

print len(asm(payload))

cnt = 0

result = ""
for byte in range(200):
    for bit in range(8):
        try:
            c = subprocess.check_output("timeout 1 ./test shellcode 3 {} {}".format(byte, bit).split())

            if c == "I am Invincible!":
                result += "-"
            else:
                cnt += 1
                result += "x"
        except subprocess.CalledProcessError:
            cnt += 1
            result += "x"

    if (byte + 1) % 8 != 0:
        result += " "
    else:
        result += "\n"

dn.close()


with open("test_res", "w") as f:
    f.write(result)

print result

print "Failed: {}".format(cnt)