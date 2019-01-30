algo_auth
=============

A simple (pseudo) algorithm problem.

Problem statement is as follows:
```
==> Hi, I like an algorithm. So, i make a new authentication system.
==> It has a total of 100 stages.
==> Each stage gives a 7 by 7 matrix below sample.
==> Find the smallest path sum in matrix, 
    by starting in any cell in the left column and finishing in any cell in the right column,
    and only moving up, down, and right.
==> The answer for the sample matrix is 12.
==> If you clear the entire stage, you will be able to authenticate.

[sample]
99 99 99 99 99 99 99
99 99 99 99 99 99 99
99 99 99 99 99 99 99
99 99 99 99 99 99 99
99  1  1  1 99  1  1
 1  1 99  1 99  1 99
99 99 99  1  1  1 99
```

As the problem statement, we are given a **7x7** matrix. Although not stated explicitly, the answer of each of the 100 stages is a character in ASCII range. Decoding the 100-character string as base64 gives us the flag.

Each of the stages must be cleared in 10 seconds. Since this is a very generous time limit, we can solve the problem in most time complexities. Below is a dynamic programming solution of `O(n^3)`, with `n=7`. Note that even a brute-force solution of `O(n^n)` will suffice.

```python
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

```

**FLAG : `g00ooOOd_j0B!!!___uncomfort4ble__s3curity__is__n0t__4__security!!!!!`**