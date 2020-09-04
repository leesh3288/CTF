# winsanity (pwn)

## Description

The time has finally come.

Enter the gate of pure insanity.

Service running on Windows Server, Version 2004 (Build 19041.450) with the following command:

```bat
powershell Set-ProcessMitigation -Name winsanity.exe -Enable DisallowChildProcessCreation
appjaillauncher-rs.exe run --key C:\CTF\flag.txt --name appjail_winsanity --port 17324 C:\CTF\winsanity.exe
```


## Deployment Guide

1. ~~Download server.iso, which is a preconfigured Windows Server installation image with auto-deployment.~~
1. ~~Install the downloaded iso. Minimal user interaction is needed, for example selecting installation partition, but everything else is automatic.~~
   1. ~~Minimum 2GB RAM~~
   1. ~~10GB disk size suffices~~
   1. ~~Port-forward (guest) 17324 <-> (host) 17324 when using hypervisors~~
1. ~~While installing, VM will automatically reboot itself 2~3 times, wait for installation to complete.~~
1. ~~After installation completes, we will see a command prompt given and nothing else. In this state, everything is already automatically deployed and running on port 17324.~~
1. ~~In case a reboot is needed, just reboot and everything will automatically run again after boot.~~

Customized server deployment ISO redacted due to licensing issues. One can construct an almost equivalent setup by the following steps:

1. Install [Windows 10 Enterprise from Microsoft Evaluation Center](https://www.microsoft.com/en-us/evalcenter/evaluate-windows-10-enterprise)
1. Apply updates up to Build 19041.450, either by hand or by pre-installing update packages on ISO before installation, with the help of [UUP dump](https://uupdump.ml/)
1. Copy [binary_flag](./binary_flag) folder as C:\CTF
1. Open inbound for service port with the following commands  
   ```bat
   netsh advfirewall firewall add rule name="winsanity_svc" dir=in action=allow program="C:\CTF\appjaillauncher-rs.exe" enable=yes
   netsh advfirewall firewall add rule name="winsanity_port" protocol=TCP dir=in localport=17324 action=allow
   ```
1. Run the command given at description. Note that you will need elevated rights for `Set-ProcessMitigation`.


## Distribution Guide

**All files to be distributed are located in `dist` folder**, which includes the following:

1. Exploit target binary `winsanity.exe`
1. Exploit target binary debug symbols `winsanity.pdb`
1. Appjaillauncher binary `appjaillauncher-rs.exe`
1. Sample flag file `flag.txt`
1. Windows DLLs folder `libs`, which contains the following:
   - `kernel32.dll`
   - `ntdll.dll`