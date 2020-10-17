FROM ubuntu:18.04

# Setup environ
ENV user protein
ENV prob_port 13100

# Install packages
RUN apt-get update
RUN apt-get install -y socat python3

# Change permission
RUN chmod 1733 /tmp /var/tmp /dev/shm

# Additional configuration
RUN adduser $user
ADD ./run.py /home/$user/run.py
ADD ./protein /home/$user/protein
ADD ./flag.pdb /home/$user/flag.pdb

RUN chown -R root:root /home/$user/
RUN chown root:$user /home/$user/run.py
RUN chown root:$user /home/$user/flag.pdb

RUN chmod 2755 /home/$user/run.py
RUN chmod 440 /home/$user/flag.pdb

# final
WORKDIR /home/$user
CMD socat -T 60 TCP-LISTEN:$prob_port,reuseaddr,fork EXEC:/home/$user/run.py
USER $user
EXPOSE $prob_port
