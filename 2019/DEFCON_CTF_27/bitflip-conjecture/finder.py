from pwn import *

context.arch = "amd64"

for i in range(256):
    flips = ""
    flips += disasm("\x30" + chr(i)) + "\n"
    for j in range(8):
        flips += disasm("\x30" + chr(i ^ (1 << j))) + "\n"
        if not("(bad)" not in flips and ".byte" not in flips):
            break
    if "(bad)" not in flips and ".byte" not in flips:
        print(hex(i))
        print(flips)