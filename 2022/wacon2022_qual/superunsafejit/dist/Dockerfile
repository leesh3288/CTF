FROM ubuntu:20.04

# Setup environment variables
ENV user superunsafejit
ENV prob_port 4444
ENV flag flag

# Install packages
RUN apt-get update 
RUN apt-get install -y socat 

# Change permission
RUN chmod 1733 /tmp /var/tmp /dev/shm

# Copy binaries and flag
RUN adduser $user
ADD ./chal /home/$user/chal
ADD ./$flag /home/$user/$flag
RUN chown -R root:root /home/$user/
RUN chown root:$user /home/$user/chal
RUN chown root:$user /home/$user/$flag
RUN chmod 2755 /home/$user/chal
RUN chmod 440 /home/$user/$flag

# final
CMD socat TCP-LISTEN:$prob_port,reuseaddr,fork EXEC:/home/$user/chal
USER $user
EXPOSE $prob_port