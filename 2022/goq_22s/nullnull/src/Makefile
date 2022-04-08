CC = gcc
PROT = -fPIE -Wl,-z,relro,-z,now -s
CFLAGS = -std=gnu11 -O0 -Wall -Wextra -fno-stack-protector
TARGET = deploy

.PHONY : all deploy

all : $(TARGET)

deploy : nullnull

nullnull: nullnull.c
	$(CC) $(PROT) $(CFLAGS) -o nullnull nullnull.c

clean:
	rm -f nullnull
