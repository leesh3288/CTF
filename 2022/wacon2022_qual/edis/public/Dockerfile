FROM redis:7.0.2@sha256:cfda0458239615720cc16d6edf6bae7905c31265f218d2033c43cdb40cd59792

RUN apt update && apt install python3 socat python3-pip -y
RUN pip3 install redis psutil

COPY ./stuff/* /
COPY ./flag /
RUN chmod 500 /flag
RUN chmod u+s /readflag

RUN useradd ctf
RUN chmod +x /*.sh /decoder.so
RUN chmod +x /*.py
WORKDIR /
CMD socat tcp-l:9000,reuseaddr,fork EXEC:"/run.py",stderr,su=ctf

