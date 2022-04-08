# Unconventional

GoN Open Qual 2022 Spring

Category: Rev

Author: Xion

Estimated Difficulty: 2 / 5


## Description

### STOP USING STACK POINTERS

- Registers were supposed to store values for arithmetic operations, NOT to point at stack top
- `rsp` DON'T point to anything, it's a register full of 64 bits of data
- You want to save something? Use `mov r/m64, r64`, NOT THIS: `push r64`

All instructions to do with stack you may see are fake, they're fooling us

Real people believe THIS CAN PUSH AND POP -> `rsp`

THEY HAVE PLAYED US FOR ABSOLUTE FOOLS

## Summary

Simple x86_64 reversing, but with rsp <-> rax

**Flag: `GoN{x86-64_c4ll1ng_c0nv3nt10n_0f_th3_m!rr0r_univers3}`**
