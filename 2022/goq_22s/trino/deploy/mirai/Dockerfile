FROM redis:6.2.6-buster

COPY --chown=root:redis flag_mirai /flag
RUN chmod 440 /flag && \
    mv /flag /flag_$(md5sum /flag | awk '{print $1}')

CMD ["redis-server", "--port", "65403"]
