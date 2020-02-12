# Windows inside QEMU inside Docker

FROM ubuntu:18.04

# Setup environ
ENV prob_port 54321

# Install packages
RUN sed -i "s/http:\/\/archive.ubuntu.com/http:\/\/mirror.kakao.com/g" /etc/apt/sources.list
RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y qemu-kvm qemu-system-x86 qemu-utils libguestfs-tools linux-image-generic wget

# Change permission
RUN chmod 1733 /tmp /var/tmp /dev/shm

# Download Windows Server .vhd
RUN wget https://software-download.microsoft.com/download/pr/17763.737.amd64fre.rs5_release_svc_refresh.190906-2324_server_serverdatacentereval_en-us_1.vhd -O ws2019.vhd -q

# Convert .vhd to .qcow2
RUN qemu-img convert -f vpc -O qcow2 ws2019.vhd ws2019.qcow2
RUN rm ws2019.vhd

# Add binary & flag files
ADD ./binary_flag/winterpreter.exe /home/chal/binary_flag/winterpreter.exe
ADD ./binary_flag/appjaillauncher-rs.exe /home/chal/binary_flag/appjaillauncher-rs.exe
ADD ./binary_flag/flag.txt /home/chal/binary_flag/flag.txt

# Add resources mostly for Windows Server automated setup
ADD ./vm_resc/unattend.xml /home/chal/vm_resc/unattend.xml
ADD ./vm_resc/SetupComplete.cmd /home/chal/vm_resc/SetupComplete.cmd
RUN sed -i "s/PORT/$prob_port/g" /home/chal/vm_resc/SetupComplete.cmd
ADD ./vm_resc/nssm.exe /home/chal/vm_resc/nssm.exe
ADD ./vm_resc/VCRT /home/chal/vm_resc/VCRT

# Add run script
ADD ./run.sh /run.sh
RUN chmod 744 /run.sh

# Expose port
EXPOSE $prob_port

# Run server
CMD /run.sh