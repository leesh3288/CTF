# Extended Extended Berkeley Packet Filter

Linux kernel exploitation chal, eBPF with BPF_ALSH implemented.

## Bugs

Faulty verification logic at added BPF_ALSH ALU op. Shifting bits to left with a shift value corresponding to possible minimal shift does not guarantee a signed minimum & maximum range. A very simple example would be a signed range `[S64_MIN, 0]`, where shifting this left by 1 would result in `[0, 0]` - we're quite certain that (-1) << 1 != 0.

## Exploitation

1. Create a BPF register that verifies into `[smin_val, smax_val] = [S64_MIN, 0]` 
   1. Set register to S64_MIN
   1. Conditionally move data loaded from BPF Map into register only if value is signed-less-or-equal 0.
1. Use BPF_ALSH to shift away `smin_val` => `[smin_val, smax_val] = [0, 0]`
   - Verifier range checks are now invalid
1. OOB relative RW from BPF frame pointer or BPF map
   - Set data loaded from map to desired negative value before triggering BPF
   - Sometimes speculative execution verifier messes up things, can be fixed by adding proper offset
   - I used BPF frame pointer, leak kernel base & BPF frame address => escalates into AAR/W
1. Use AAR/W for profit :)
   - ex) Traverse init_task to find our process & overwrite creds for PoE

## Exploit Code

See [main.c](main.c), completed up to AAR/W primitive.

Debug environment provided by [ptr-yudai](https://twitter.com/ptrYudai) 🤗