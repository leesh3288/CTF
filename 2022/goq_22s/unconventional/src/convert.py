#!/usr/bin/env python3

import sys
import re

in_fn, out_fn = sys.argv[1:3]

with open(in_fn, 'r') as fi:
    in_asm = fi.read()

# This would get real dirty, assume we don't have one
assert '%ah' not in in_asm

"""
Conversion Rules:
1. pushq %REG
   => movq %REG, -0x8(%rax)
      leaq -0x8(%rax), %rax
2. popq %REG
   => leaq 0x8(%rax), %rax
      movq -0x8(%rax), %REG
3. call EQU  // EQU may be dependent on rsp! (rax after conv)
   => movq %rsp, -0x8(%rax)
        if (EQU is rip-relative symbol)
          leaq EQU(rip), %rsp
        else
          movq EQU, %rsp
      leaq -0x8(%rax), %rax
      movq %rsp, -0x8(rax)  // real address to be called
      leaq .LRETnn(%rip), %rsp
      xchgq %rsp, (%rax)
        if (EQU is external func)
          xchgq %rsp, %rax
          jmp *-0x8(%rsp)
          .LRETnn:
          xchgq %rsp, %rax
        else
          jmp *-0x8(%rax)
          .LRETnn:
4. ret
   => leaq 0x8(%rax), %rax
      jmp *-0x8(%rax)
5. leave
   => movq %rbp, %rax
      popq %rbp  // use conversion rule #2

Notes:
1. push, pop, call, ret, etc. must be split into instructions done in
    a specific order to guarantee exact same semantics in case of rsp-dependent operands
2. Must use lea to ensure no flags are affected

Problems:
1. Unsupported:
   - %ah => assume none
   - Tail Call Optimization into extern functions => avoid w/ gcc -O1
2. %rax can be index of ofs(base, index, mult), but not %rsp
   => Solution #1. Use MULX/SHLX instructions -> requires BMI2 instruction set support, nah
   => Solution #2. Yet another "xchg %rsp, %rax" -> yea
3. %rax may be modified or be required by some arithmetic ops (cdqe, div, etc.)
   => Just "xchg %rsp, %rax" and go brrr
"""

def swap_words(s, x, y):
    return y.join(part.replace(y, x) for part in s.split(x))

def ltrimmed(s):
    return re.match(r"\s*", s).group()

def swap_all(s):
    s = swap_words(s, '%rsp', '%rax')
    s = swap_words(s, '%esp', '%eax')
    s = swap_words(s, '%sp', '%ax')
    s = swap_words(s, '%spl', '%al')
    return s

in_asm = swap_all(in_asm)

il = in_asm.splitlines()
ol = []
label_ctr = 0

def atnt(op):
    return [op, op+'b', op+'w', op+'l', op+'q']

def append_xchg(lines, ws):
    if len(lines) >= 1 and lines[-1].strip().split() == ['xchgq', '%rsp,', '%rax']:
        lines.pop()  # double xchg, reduce to noop
    else:
        lines.append(f'{ws}xchgq\t%rsp, %rax')

# https://sourceware.org/binutils/docs/as/i386_002dMnemonics.html
# Probably not even close to exhaustive, but well it works in our case :)
rax_ops = [
    'cbtw', 'cwtl', 'cwtd', 'cltd', 'cltq', 'cqto',
    'cmpxchg8b', 'cmpxchg16b',
    *atnt('div'), *atnt('idiv'),
    *atnt('mul'), *atnt('imul'),
    'rep', 'repe', 'repz', 'repne', 'repnz',
    *atnt('stos')
]

in_main = False

for i, line in enumerate(il):
    elems = line.strip().split()
    leading_ws = ltrimmed(line)
    if len(elems) == 0:
        ol.append('')
        continue
    elif elems[0] == 'main:':
        # main label
        in_main = True
        ol.append(line)
    elif elems[0] == 'endbr64' and in_main:
        # main entry (endbr64)
        ol.append(line)
        append_xchg(ol, leading_ws)
    elif elems[0] == 'ret' and in_main:
        # main exit (ret)
        append_xchg(ol, leading_ws)
        ol.append(line)
    elif elems[0:3] == '.size main, .-main'.split():
        # main label end
        in_main = False
        ol.append(line)
    elif elems[0] in rax_ops or any(','+reg in line for reg in ['%rsp', '%esp', '%sp', '%spl']):
        # rax-dependent ops or %rax in index of base/index addressing
        append_xchg(ol, leading_ws)
        ol.append(swap_all(line))
        append_xchg(ol, leading_ws)
    elif elems[0] == 'pushq':
        ol.append(f'{leading_ws}movq\t{elems[1]}, -0x8(%rax)')
        ol.append(f'{leading_ws}leaq\t-0x8(%rax), %rax')
    elif elems[0] == 'popq':
        ol.append(f'{leading_ws}leaq\t0x8(%rax), %rax')
        ol.append(f'{leading_ws}movq\t-0x8(%rax), {elems[1]}')
    elif elems[0] == 'call':
        extern = False
        ol.append(f'{leading_ws}movq\t%rsp, -0x8(%rax)')
        if elems[1].startswith('*'):  # depends on some register value (assume internal)
            ol.append(f'{leading_ws}movq\t{elems[1][1:]}, %rsp')
        else:
            extern = elems[1].endswith('@PLT')  # external function
            ol.append(f'{leading_ws}leaq\t{elems[1]}(%rip), %rsp')
        ol.append(f'{leading_ws}leaq\t-0x8(%rax), %rax')
        ol.append(f'{leading_ws}movq\t%rsp, -0x8(%rax)')
        ol.append(f'{leading_ws}leaq\t.LRET{label_ctr}(%rip), %rsp')
        ol.append(f'{leading_ws}xchgq\t%rsp, (%rax)')
        if extern:
            append_xchg(ol, leading_ws)
            ol.append(f'{leading_ws}jmp\t*-0x8(%rsp)')
            ol.append(f'.LRET{label_ctr}:')
            append_xchg(ol, leading_ws)
        else:
            ol.append(f'{leading_ws}jmp\t*-0x8(%rax)')
            ol.append(f'.LRET{label_ctr}:')
        label_ctr += 1
    elif elems[0] == 'jmp':
        # external function TCO'd, hard to jmp without fixing stack frame...
        assert not elems[1].endswith('@PLT')
        ol.append(line)
    elif elems[0] == 'ret':
        ol.append(f'{leading_ws}leaq\t0x8(%rax), %rax')
        ol.append(f'{leading_ws}jmp\t*-0x8(%rax)')
    elif elems[0] == 'leave':
        ol.append(f'{leading_ws}movq\t%rbp, %rax')
        ol.append(f'{leading_ws}leaq\t0x8(%rax), %rax')
        ol.append(f'{leading_ws}movq\t-0x8(%rax), %rbp')
    else:
        ol.append(line)

ol.append('')

with open(out_fn, 'w') as fo:
    fo.write('\n'.join(ol))
