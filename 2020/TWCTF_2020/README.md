# TokyoWesterns CTF 6th 2020

Participated as member of **KAIST GoN** under alliance team **D0G$**. Solved Vi deteriorated and Blind Shot, _almost_ solved Extended Extended Berkeley Packet Filter (+Birds).

## TL;DR solutions

### [Vi deteriorated](vid/writeup.md)

First blood!

1. OOB std::vector & std::string accessed with .at() + C++ exception printing backtrace
   - binary & libc base leak
1. Faulty iterator use with std::vector::insert() causing UAF + OOB access
   - Object being accessed is std::string, fetch a fake string & replace to get AAW
   - Requires simple heap shaping

### [Blind Shot](blindshot/writeup.md)

First blood!

1. dprintf() format-string bug once against fd = open("/dev/null")
   - In virtually ALL cases, one FSB is sufficient for repeated AAR/W
1. Do the "One-shot Double Staged FSB" to overwrite return address of service(), repeat FSB
   - Requires 1.5byte stack addr bruteforce
1. Again, do the above but now with "argv-flip" for repeated AAW
   - Deferred use of positional arguments leading to argument caching at printf_positional()
   - "Flip" pointers at stack to obtain two writes at once!

### [Extended Extended Berkeley Packet Filter](eebpf/writeup.md)

Got AAR/W, but was too exhausted to complete the rest 😪

1. Create a BPF register that verifies into `[smin_val, smax_val] = [S64_MIN, 0]` 
   - Set register to S64_MIN
   - Conditionally move data loaded from BPF Map only if SLE 0
1. Use BPF_ALSH to shift away `smin_val` => `[smin_val, smax_val] = [0, 0]`
   - Verifier range checks are now wrong
1. OOB relative read from BPF frame pointer or BPF map
   - Set data loaded from map to appropriate negative value
   - Sometimes speculative execution verifier messes up things, can be fixed by adding proper offset
   - I used BPF frame pointer, leak kernel base & BPF frame address => AAR/W
1. Use AAR/W for profit :)
   - ex) Traverse init_task to find our process & overwrite creds for PoE

### Birds

```
TWCTF{
BC552
AC849
JL106
PQ448
JL901
LH908
NH2177
}

BC552 : OKA -> NGO
AC849 : LHR -> YYZ
JL106 : ITM -> HND
PQ448 : TBS -> ODS
JL901 : HND -> OKA
LH908 : FRA -> LHR
NH2177 : NRT -> ITM

FRA -> LHR -> YYZ:               FLY
TBS -> ODS:                      TO
NRT -> ITM -> HND -> OKA -> NGO: NIHON

TWCTF{FLYTONIHON}
```