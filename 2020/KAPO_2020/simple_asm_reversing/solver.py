from pwn import *
import string

binary = ELF('./challenge')

print('disasm...')
res = binary.disasm(0x400106, 0x5A7960-0x400106)
print('disasm complete.')

reg = {"rax": 0x2617CF3B31997597, "rbx": 0x223A066E1AFE6F5A, "rsi": 0x8321A118A2A8347B, "rdi": 0x9B453598947D757D}
MASK = (1 << 64) - 1

def get(s):
    if s in reg:
        return reg[s]
    else:
        base = 16 if s[:2] == '0x' else 10
        return int(s, base)

def rol(x, n):
    n &= 0x3f
    return ((x << n) | (x >> (0x40 - n))) & MASK

def ror(x, n):
    n &= 0x3f
    return ((x << (0x40 - n)) |  (x >> n)) & MASK

def egcd(a, b):
    if a == 0:
        return (b, 0, 1)
    else:
        g, y, x = egcd(b % a, a)
        return (g, x - (b // a) * y, y)

def modinv(a, m):
    g, x, y = egcd(a, m)
    if g != 1:
        raise Exception('modular inverse does not exist')
    else:
        return x % m

rev = res.split('\n')

i = len(rev) - 1
while i >= 0:
    if i & 0xfff == 0:
        print(i)
    line = rev[i]
    cmd = line[38:].replace(',', ' ').split()
    if cmd[0] == 'xor':
        reg[cmd[1]] = reg[cmd[1]] ^ get(cmd[2])
    elif cmd[0] == 'add':
        reg[cmd[1]] = (reg[cmd[1]] - get(cmd[2])) & MASK
    elif cmd[0] == 'sub':
        reg[cmd[1]] = (reg[cmd[1]] + get(cmd[2])) & MASK
    elif cmd[0] == 'rol':
        reg[cmd[1]] = ror(reg[cmd[1]], get(cmd[2]))
    elif cmd[0] == 'ror':
        reg[cmd[1]] = rol(reg[cmd[1]], get(cmd[2]))
    elif cmd[0] == 'nop':
        pass
    elif cmd[0] == 'dec':
        reg[cmd[1]] = (reg[cmd[1]] + 1) & MASK
    elif cmd[0] == 'inc':
        reg[cmd[1]] = (reg[cmd[1]] - 1) & MASK
    elif cmd[0] == 'not':
        reg[cmd[1]] = MASK ^ reg[cmd[1]]
    elif cmd[0] == 'neg':
        reg[cmd[1]] = (-reg[cmd[1]]) & MASK
    elif cmd[0] == 'adc':
        i -= 1
        prev = rev[i][38:].replace(',', ' ').split()
        if prev[0] == 'clc':
            reg[cmd[1]] = (reg[cmd[1]] - get(cmd[2])) & MASK
        elif prev[0] == 'stc':
            reg[cmd[1]] = (reg[cmd[1]] - get(cmd[2]) - 1) & MASK
        else:
            assert(False)
    elif cmd[0] == 'xchg':
        reg[cmd[1]], reg[cmd[2]] = reg[cmd[2]], reg[cmd[1]]
    elif cmd[0] == 'mul':
        assert(len(cmd) == 2 and cmd[1] == 'rdx')
        i -= 1
        prev = rev[i][38:].replace(',', ' ').split()
        assert(prev[:2] == ['mov', 'edx'])
        mul = get(prev[2])
        mod = (1 << 64) % mul
        rem = (mul - reg['rax'] % mul) % mul
        rdx = (modinv(mod, mul) * rem) % mul
        assert(((rdx << 64) | reg['rax']) % mul == 0)
        reg['rax'] = (((rdx << 64) | reg['rax']) // mul) & MASK
    elif cmd[0] == 'lea':
        addr = cmd[2].replace('[', '').replace(']', '').replace('+', ' ').replace('*', ' ').split()
        assert(cmd[1] == addr[0])
        if len(addr) == 2:
            reg[cmd[1]] = (reg[addr[0]] - get(addr[1])) & MASK
        elif len(addr) == 3:
            assert('*' in line)
            reg[cmd[1]] = (reg[addr[0]] - get(addr[1]) * get(addr[2])) & MASK
        else:
            assert(False)
    else:
        assert(False)
    i -= 1

print(p64(reg['rax'])+p64(reg['rbx'])+p64(reg['rsi'])+p64(reg['rdi']))

