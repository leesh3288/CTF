# winterpreter

## Description

It's now time to get your hands dirty on Windows exploitation chals.

Try out my bulletproof debugger with a weird language!

Service running on Windows Server 2019, Version 1809 (Build 17763.737) with the following command:

`C:\CTF\appjaillauncher-rs.exe run --key C:\CTF\flag.txt --name appjail_winterpreter --port 54321 C:\CTF\winterpreter.exe`


## Deployment Guide

### On Linux Server (+KVM)
1. This challenge can run on Windows Server 2019 running on QEMU inside Docker for Linux. This is to completely dockerize the challenge inside a single docker container on a Linux environment. KVM support is necessary.
1. Deployer should build the docker container with a good time margin before the challenge must actually be hosted, since the build process takes a long time to download .vhd file & convert to .qcow2 (~15min). Docker run preprocessing may also take a bit (~7.5min).
1. `binary_flag/`, `vm_resc/`, `Dockerfile`, `run.sh` is required to build the docker container. Following docker build & run commands in `info.txt` would be sufficient to deploy the challenge in a runnning state.

### On Windows Server
1. This challenge runs ideally on Windows-based environment, where additional virtualization is not needed.
1. Deployer should install needed MSVC Redistributables located at `vm_resc/VCRT/Source` prior to CTF event.
1. `binary_flag/` is required to deploy the service. Set the folder `binary_flag/` as working directory, and run `run_server.bat` to deploy the challenge.

Note that **running the challenge on a Windows environment requires the following additional steps**:
1. Change the description to match the Windows environment version & build.
1. Change the description to match the actual command used by the batch file.
1. Copy all DLLs to `dist/libs` folder for later distribution. Note that exploitation does not depend heavily on a specific Windows version, so using any recent Windows Server builds would suffice.


## Distribution Guide

**All files to be distributed are located in `dist` folder**, which includes the following:

1. Exploit target binary `winterpreter.exe`
1. Exploit target binary debug symbols `winterpreter.pdb`
1. Appjaillauncher binary `appjaillauncher-rs.exe`
1. Sample flag file `flag.txt`
1. Windows DLLs folder `libs`, which contains the following:
  - `KernelBase.dll`
  - `kernel32.dll`
  - `ntdll.dll`
  - `vcruntime140.dll`
  - `msvcp140.dll`
  - `ucrtbase.dll`