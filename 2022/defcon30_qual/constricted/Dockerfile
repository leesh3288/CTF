FROM ubuntu:20.04
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && DEBIAN_FRONTEND=noninteractive \
    apt-get install --no-install-recommends -y socat && apt-get upgrade -y

WORKDIR /challenge
COPY boa boa
RUN adduser --no-create-home --disabled-password --gecos "" user

ENV port 65401

USER user
CMD socat -t 3600 -T 3600 TCP-LISTEN:$port,reuseaddr,fork EXEC:"/challenge/boa"
