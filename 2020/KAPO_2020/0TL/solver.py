from pwn import *
from hashlib import md5
from Crypto.Util.number import long_to_bytes as l2b, bytes_to_long as b2l
from Crypto.Cipher import AES

IP, PORT = '52.79.243.7', 1337

while True:
    p = remote(IP, PORT)

    p.recvuntil('[iv]\n')
    iv = l2b(int(p.recvline(False), 16)).rjust(0x10, '\0')
    if iv[0] != '\0':  # bruteforce null iv
        log.warning('retry iv')
        p.close()
        continue

    p.recvuntil('[server random]\n')
    server_rand = l2b(int(p.recvline(False), 16)).rjust(4, '\0')

    p.recvuntil('username >> ')
    p.sendline('admin')

    p.recvuntil('client random (hex) >> ')
    client_rand = '\0'*0x10  # bruteforce enc('\0'*0x10)[0] == '\0'
    p.sendline(hex(b2l(client_rand))[2:].rjust(0x20, '0'))

    """
    aes_key = md5("admin" + "guest1234" + server_rand).digest()
    cipher = AES.new(aes_key, AES.MODE_ECB)
    data = bytearray(iv + client_rand)
    for i in range(16):
        data[i+0x10] ^= ord(cipher.encrypt(bytes(data[i:i+0x10]))[0])
    aes_inv_key = bytes(data[0x10:0x20])
    """
    aes_inv_key = '\0'*0x10

    cipher = AES.new(aes_inv_key, AES.MODE_ECB)
    command = 'flag'.ljust(0x10, '\0')
    command_enc = cipher.encrypt(command)

    p.recvuntil('command (hex) >> ')
    p.sendline(hex(b2l(command_enc))[2:].rjust(0x20, '0'))

    try:
        print(p.readline())
        break
    except:
        log.warning('retry')
        p.close()
        continue
