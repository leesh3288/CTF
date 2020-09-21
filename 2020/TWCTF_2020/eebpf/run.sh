#!/bin/bash
qemu-system-x86_64 \
    -kernel bzImage\
    -initrd debugfs.cpio\
    -append "loglevel=3 root=/dev/ram console=ttyS0 oops=panic panic=1"\
    -nographic -monitor /dev/null\
    -smp cores=1,threads=1\
    -cpu kvm64,+smep,+smap\
    -gdb tcp::12345
