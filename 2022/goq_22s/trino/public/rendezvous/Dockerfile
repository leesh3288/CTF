FROM i386/redis:6.2.4-buster

COPY --chown=root:redis flag_rendezvous /flag
RUN chmod 440 /flag && \
    mv /flag /flag_$(md5sum /flag | awk '{print $1}')

COPY --chown=root:redis redis.conf /redis.conf
RUN chmod 440 /redis.conf

CMD ["redis-server", "/redis.conf"]
