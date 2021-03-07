# zer0pts CTF 2021

ptr-yudai san's 🤸 CTF & my first 2021 CTF :)

Solved stopwatch, GuestFS:AFR, OneShot, nasm kit.

Additionally worked on Baby SQLi, signme.


## Stopwatch

First blood!

- Always check scanf return value!
  - Leak canary through invalid input at `scanf("%lf", t);`
- Stack overflow using `scanf("%s", buf);`
- ROP your way


## GuestFS:AFR

Solved w/ [@whysw]

- Race `create` (symlink -> check -> unlink) & `read`
- Race window is very short, required us several hundred tries (at least with my implementation)


## OneShot

First blood!

Solved w/ [@Reinose]

- Always check `{c,m,re}alloc` return value!
  - Failed allocation returns NULL, binary is non-PIE
- We have 4 bytes arbitrary write at any absolute address
  - `puts` not yet called, overwrite `puts@got` to `main` & enjoy `n-Shot`
- Using arbitrary write setup a call chain: `exit -> setup -> setbuf -> 4005D0 -> 4007D6`
  - Leak libc lower 4 bytes from `_IO_2_1_stdin`
- We have libc leak, enjoy RCE


## nasm kit

First blood!

Solved w/ [@Reinose]

- Unicorn emulator w/ read, write, mmap, munmap, exit syscall available
- mmap? Recall something? [LCARS022](https://archive.ooo/c/LCARS022/267/)
  - Unintended solution with mmap `MAP_FIXED`
  - After I got my head bonked, I RTFMed...
    - `MAP_FIXED_NOREPLACE`: "If the requested range would collide with an existing mapping, then this call fails with the error EEXIST."
    - `MAP_FIXED`: "If the memory region specified by addr and len overlaps pages of any existing mapping(s), then the overlapped part of the existing mapping(s) will be discarded."
- Use mmap with `MAP_FIXED_NOREPLACE` to probe & derandomize ASLR
- Use mmap with `MAP_FIXED` to replace already mapped region & allow emulated code to use it
- Fix things (if necessary), write shellcode & enjoy RCE

PS. After dropping shell, I checked `uname -a` to see that the kernel version is `4.15` - this means that `MAP_FIXED_NOREPLACE` is not supported. However, man page hints that ```older kernels which do not recognize the MAP_FIXED_NOREPLACE flag will typically (upon detecting a collision with a preexisting mapping) fall back to a "non-MAP_FIXED" type of behavior: they will return an address that is different from the requested address.``` which means that the emulator will return the same results, effectively acting as the intended solution.


[@whysw]: https://twitter.com/whysw_p
[@Reinose]: https://twitter.com/_Reinose_en
