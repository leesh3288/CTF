CC = gcc
PROT = -fPIE -Wl,-z,relro,-z,now -s
CFLAGS = -std=gnu11 -O1 -Wall -Wextra \
	-fno-asynchronous-unwind-tables -fno-dwarf2-cfi-asm \
	-fno-stack-protector -DNDEBUG
TARGET = deploy

.PHONY : all deploy

all : $(TARGET)

deploy : unconventional

unconventional: unconventional.s
	$(CC) $(PROT) $(CFLAGS) -o unconventional unconventional.s

unconventional.s: conventional.s
	./convert.py conventional.s unconventional.s

conventional.s: main.c
	$(CC) $(PROT) $(CFLAGS) -S -o conventional.s main.c

clean:
	rm -f unconventional unconventional.s conventional.s
