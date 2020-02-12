cscript C:\VCRT\Install-MicrosoftVisualC++x86x64.wsf

netsh advfirewall firewall add rule name="winterpreter_svc" dir=in action=allow program="C:\CTF\appjaillauncher-rs.exe" enable=yes
netsh advfirewall firewall add rule name="winterpreter_port" protocol=TCP dir=in localport=PORT action=allow

nssm install winterpreter_svc C:\CTF\appjaillauncher-rs.exe "run --key C:\CTF\flag.txt --name appjail_winterpreter --port PORT C:\CTF\winterpreter.exe"
nssm set winterpreter_svc Start SERVICE_DELAYED_START
nssm start winterpreter_svc