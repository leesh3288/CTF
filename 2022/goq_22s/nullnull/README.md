# NullNull

GoN Open Qual 2022 Spring

Category: Pwn

Author: Xion

Estimated Difficulty: 0.5 / 5


## Description

I know there's been some trust issues on "baby" CTF chals, but this really is a NullNull(colloquially "spacious", "easy" in KR) pwnable chal...

## Summary

Simple pwnable exploiting "poison null byte" on stack caused by `scanf("%Ns", buf)` => `buf[N]='\0'`

**Flag: `GoN{A_v3ry_Nul1Nu1l_sc4nf_width}`**
