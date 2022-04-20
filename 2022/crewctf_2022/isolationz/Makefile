all: chall.c __malloc.h utils.h
	gcc chall.c -o chall -lm -g
	bash -c "patchelf --set-interpreter /home/ctf/ld-linux-x86-64.so.2 ./chall"
