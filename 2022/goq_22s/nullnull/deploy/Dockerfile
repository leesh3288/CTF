# Digest pinning to guarantee constant libc version
# FROM ubuntu:20.04
FROM ubuntu@sha256:8ae9bafbb64f63a50caab98fd3a5e37b3eb837a3e0780b78e5218e63193961f9

ENV user nullnull
ENV port 9431

# Install packages
RUN sed -i "s/http:\/\/archive.ubuntu.com/http:\/\/mirror.kakao.com/g" /etc/apt/sources.list \
 && apt-get update \
 && DEBIAN_FRONTEND=noninteractive \
    apt-get install --no-install-recommends -y socat \
 && rm -rf /var/lib/apt/lists/*

# Change tmp permissions
RUN chmod 1733 /tmp /var/tmp /dev/shm

# Add user
RUN adduser --disabled-password --gecos "" $user
RUN chown -R root:root /home/$user

# Add files
COPY --chown=root:$user nullnull flag /home/$user/

# chown & chmod files
RUN chmod 755 /home/$user/nullnull \
 && chmod 440 /home/$user/flag

# Run server
WORKDIR /home/$user
CMD socat -t 30 -T 30 TCP-LISTEN:$port,reuseaddr,fork EXEC:"/home/$user/nullnull"
USER $user
EXPOSE $port
