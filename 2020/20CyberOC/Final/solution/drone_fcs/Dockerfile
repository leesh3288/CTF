FROM ubuntu:18.04

# Setup environ
ENV user dronefcs
ENV prob_port 13100

# Install packages
RUN apt-get update
RUN apt-get install -y socat

# Change permission
RUN chmod 1733 /tmp /var/tmp /dev/shm

# Additional configuration
RUN adduser $user
ADD ./run.sh /home/$user/run.sh
ADD ./firmware /home/$user/firmware
ADD ./libjemalloc.so /home/$user/libjemalloc.so
ADD ./flag /home/$user/flag


RUN chown -R root:root /home/$user/
RUN chown root:$user /home/$user/run.sh
RUN chown root:$user /home/$user/firmware
RUN chown root:$user /home/$user/libjemalloc.so
RUN chown root:$user /home/$user/flag

RUN chmod 2755 /home/$user/run.sh
RUN chmod 755 /home/$user/firmware
RUN chmod 755 /home/$user/libjemalloc.so
RUN chmod 440 /home/$user/flag

# final
WORKDIR /home/$user
CMD socat -T 60 TCP-LISTEN:$prob_port,reuseaddr,fork EXEC:/home/$user/run.sh
USER $user
EXPOSE $prob_port
