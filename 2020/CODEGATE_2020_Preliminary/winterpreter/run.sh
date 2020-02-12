#!/usr/bin/env bash

# Mount disc for modification
mkdir -p /mnt/
guestmount -a ws2019.qcow2 -i /mnt/

# Add binaries & flag
mkdir -p /mnt/CTF
cp /home/chal/binary_flag/winterpreter.exe /mnt/CTF/winterpreter.exe
cp /home/chal/binary_flag/appjaillauncher-rs.exe /mnt/CTF/appjaillauncher-rs.exe
cp /home/chal/binary_flag/flag.txt /mnt/CTF/flag.txt

# Add Windows Server setup
mkdir -p /mnt/Windows/Setup/Scripts
cp /home/chal/vm_resc/unattend.xml /mnt/unattend.xml
cp /home/chal/vm_resc/SetupComplete.cmd /mnt/Windows/Setup/Scripts/SetupComplete.cmd
cp /home/chal/vm_resc/nssm.exe /mnt/Windows/System32/nssm.exe
cp -a /home/chal/vm_resc/VCRT /mnt/VCRT

# Unmount disk
umount /mnt/

# Wait for IO to complete, required for QEMU write lock acquisition
sleep 5

# Run server
qemu-system-x86_64 -hda ws2019.qcow2 -m 4096M -enable-kvm -cpu host -smp $(nproc) -nographic -monitor /dev/null -net nic,model=rtl8139 -net user,hostfwd=tcp::$prob_port-:$prob_port