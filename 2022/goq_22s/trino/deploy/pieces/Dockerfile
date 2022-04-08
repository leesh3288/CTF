FROM python:3.9-alpine

ENV user pieces
ENV port 15961

RUN chmod 1733 /tmp /var/tmp /dev/shm

# Add user
RUN adduser --disabled-password --gecos "" $user \
 && chown -R root:root /home/$user

# Add files
COPY --chown=root:$user . /home/$user/

# chown & chmod files
RUN chmod -R 550 /home/$user/app /home/$user/wait-for-it && \
    chmod 440 /home/$user/flag_albireo /home/$user/flag_pieces

# Install requirements
RUN apk add --no-cache libcurl bash
ENV PYCURL_SSL_LIBRARY=openssl
RUN apk add --no-cache --virtual .build-deps build-base curl-dev \
    && pip install --no-cache-dir -r /home/$user/requirements.txt \
    && apk del .build-deps

# Run server
WORKDIR /home/$user/app
CMD ["../wait-for-it",\
     "-w", "albireo:65401",\
     "-w", "rendezvous:65402",\
     "-w", "mirai:65403",\
     "--",\
     "./pieces.py"]
USER $user
EXPOSE $port
