# FROM python:3.10.2-slim-bullseye
FROM python@sha256:6faf002f0bce2ce81bec4a2253edddf0326dad23fe4e95e90d7790eaee653da5

ENV user showdown
ENV port 56925

RUN chmod 1733 /tmp /var/tmp /dev/shm

# Add user
RUN adduser --disabled-password --gecos "" $user \
 && chown -R root:root /home/$user

# Add files
COPY --chown=root:$user . /home/$user/

# chown & chmod files
RUN chmod -R 550 /home/$user/app \
 && chmod -R 440 /home/$user/app/static/* \
                 /home/$user/app/templates/* \
                 /home/$user/flag

RUN echo 0 > /tmp/leakctr \
 && chown root:$user /tmp/leakctr \
 && chmod 660 /tmp/leakctr

# Install requirements
RUN pip install --no-cache-dir flask

# Run server
WORKDIR /home/$user/app
CMD ["bash", "-c", "while true; do timeout -k 0 5m ./showdown.py; done"]
USER $user
EXPOSE $port
