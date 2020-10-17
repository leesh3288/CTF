FROM ubuntu:20.10
MAINTAINER Anonymous<anonymous@anonymous.com>

RUN sed -i "s/http:\/\/archive.ubuntu.com/http:\/\/mirror.kakao.com/g" /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y xinetd

RUN chmod og-rwx /var/log && \
      chmod og-rwx /tmp && \
      chmod og-rwx /var/tmp && \
      chmod og-rwx /dev/shm

RUN useradd -s /bin/false rmodule
WORKDIR /home/rmodule

COPY ./xinetd_file /etc/xinetd.d/rmodule
EXPOSE 54321

COPY ./flag /home/rmodule/flag
COPY ./rmodule /home/rmodule/rmodule

RUN chown -R root:root /home/rmodule
RUN chmod -R 755 /home/rmodule
RUN chmod 444 /home/rmodule/flag

CMD ["/usr/sbin/xinetd", "-dontfork"]
