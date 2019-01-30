# WARNING: extremely un-pythonic

from pwn import *

context.log_level = 'debug'

p = remote('110.10.147.109', 15712)

p.recvuntil('>> ')
p.sendline('G')

flag = ''

for i in range(100):
    p.recvuntil('***\n')
    raw = p.recvlines(7)  # 7x7 grid
    DP = []
    for line in raw:
        DP.append(map(int, line.strip().split()))
        assert(len(DP[-1]) == 7)
    assert(len(DP) == 7)
    
    # O(n^3), n=7
    for j in range(1, 7):
        colsum = [0]*8
        for k in range(7):
            colsum[k+1] = colsum[k] + DP[k][j]
        for k in range(7):  # up&down minimization
            mv = 2**30
            for l in range(7):
                if k >= l:
                    mv = min(mv, DP[l][j-1] + colsum[k+1] - colsum[l])
                else:  # k < l
                    mv = min(mv, DP[l][j-1] + colsum[l+1] - colsum[k])
            DP[k][j] = mv
    
    res = min(DP[j][6] for j in range(7))
    p.recvuntil('>>> ')
    p.sendline(str(res))
    flag += chr(res)

assert(len(flag)==100)
print flag.decode('base64')

p.interactive()
