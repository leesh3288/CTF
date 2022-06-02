FROM ubuntu:22.04 as challenge

# Install packages
RUN sed -i "s/http:\/\/archive.ubuntu.com/http:\/\/mirror.kakao.com/g" /etc/apt/sources.list \
 && apt-get update \
 && DEBIAN_FRONTEND=noninteractive \
    apt-get install --no-install-recommends -y socat gdb git \
 && GIT_SSL_NO_VERIFY=1 git clone https://github.com/pwndbg/pwndbg \
 && cd pwndbg \
 && ./setup.sh

ENV port 65400

WORKDIR /perribus/challenge
COPY  cryptochall /perribus/challenge/
COPY flag.txt /perribus/challenge/

RUN adduser --no-create-home --disabled-password --gecos "" user
USER user

CMD socat -t 3600 -T 3600 TCP-LISTEN:$port,reuseaddr,fork EXEC:"/perribus/challenge/cryptochall"
