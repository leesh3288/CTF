from pwn import *

FLAG_LEN = 37

flag = [set(i for i in range(256)) for _ in range(FLAG_LEN)]

while True:
    p = remote('hitme.tasteless.eu', 10401)
    res = p.recvall()
    p.close()

    if not res:
        continue

    for i in range(FLAG_LEN):
        flag[i].discard(ord(res[i]))
    print([len(flag[i]) for i in range(FLAG_LEN)])
    if all(len(flag[i]) == 1 for i in range(FLAG_LEN)):
        print(''.join(chr(flag[i].pop()) for i in range(FLAG_LEN)))
        break