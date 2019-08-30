
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/prctl.h>


#define STR(x) #x
#define XSTR(s) STR(s)

#define ROP_AREA_START 0x00800000   

#define COMPUTING_AREA_START 0x20000000
#define COMPUTING_AREA_SIZE 0x1000000 

#define COMPUTING_STACK_START 0x30000000
#define COMPUTING_STACK_SIZE 0x10000000 
#define COMPUTING_STACK_END COMPUTING_STACK_START + COMPUTING_STACK_SIZE - 8

#define COMPUTING_HEAP_START 0x40000000
#define COMPUTING_HEAP_SIZE 0x10000000 

#define OUTPUT_AREA 0x50000000
#define OUTPUT_SIZE 0x10000000 

#define SECCOMP_AREA 0x60000000
#define SECCOMP_SIZE 0x1000

#define MEMORY_TOP 0x7ffffffff000
#define UPPER_MEMORY MEMORY_TOP - (SECCOMP_AREA + SECCOMP_SIZE)


struct sock_filter {           
   __u16 code;                 
   __u8  jt;                  
   __u8  jf;                  
   __u32 k;                    
};

struct sock_fprog {
   unsigned short      len;    
   struct sock_filter *filter;
};


size_t getFilesize(const char* filename) {
    struct stat st;
    stat(filename, &st);
    return st.st_size;
}


void seccomp_trampoline(){

    asm volatile (
        "mov rax, "XSTR(COMPUTING_HEAP_START)"\n" 
        "mov qword ptr [rax], 0x6\n"
        "mov rax, "XSTR(COMPUTING_HEAP_START+8)"\n" 
        "mov word ptr [rax], 0x1\n" 
        "mov rax, "XSTR(COMPUTING_HEAP_START+8+8)"\n"
        "mov qword ptr [rax], "XSTR(COMPUTING_HEAP_START)"\n" 

        "mov rax, 157\n"
        "mov rdi, 38\n"
        "mov rsi, 1\n"
        "mov rdx, 0\n"
        "mov r10, 0\n"
        "mov r8, 0\n"
        "syscall\n" 

        "mov rax, 11\n"
        "mov rdi, 0\n"
        "mov rsi, "XSTR(ROP_AREA_START)"\n"
        "syscall\n" 
        "mov rax, 11\n"
        "mov rdi, "XSTR(SECCOMP_AREA + SECCOMP_SIZE)"\n"
        "mov rsi, "XSTR(UPPER_MEMORY)"\n"
        "syscall\n" 

        "mov rax, 157\n"
        "mov rdi, 22\n"
        "mov rsi, 2\n"
        "mov rdx, "XSTR(COMPUTING_HEAP_START+8)"\n"
        "mov r10, 0\n"
        "mov r8, 0\n"
        "syscall\n" 

        "mov rax, "XSTR(COMPUTING_HEAP_START)"\n"
        "mov qword ptr [rax], 0x0\n"
        "mov qword ptr [rax+8], 0x0\n"
        "mov qword ptr [rax+16], 0x0\n"
        "mov rsp, "XSTR(COMPUTING_STACK_END)"\n"
        "xor r15, r15\n"
        "xor r14, r14\n"
        "xor r13, r13\n"
        "xor r12, r12\n"
        "xor rbp, rbp\n"
        "xor rbx, rbx\n"
        "xor r11, r11\n"
        "xor r10, r10\n"
        "xor r9, r9\n"
        "xor r8, r8\n"
        "xor rax, rax\n"
        "xor rcx, rcx\n"
        "xor rdx, rdx\n"
        "xor rsi, rsi\n"
        "xor rdi, rdi\n"

        "int 3\n"

        "int 3\n"
        "int 3\n"
        "int 3\n"
        "int 3\n"
    );
}



int main(int argc, char** argv) {
    size_t filesize;
    int fd;

    filesize = getFilesize(argv[1]);
    fd = open(argv[1], O_RDONLY, 0);
    mmap((void*) ROP_AREA_START, filesize, PROT_READ, MAP_FIXED | MAP_PRIVATE | MAP_POPULATE, fd, 0);
    close(fd);

    filesize = getFilesize(argv[2]);
    fd = open(argv[2], O_RDONLY, 0);
    mmap((void*) COMPUTING_AREA_START, COMPUTING_AREA_SIZE, PROT_READ | PROT_EXEC, MAP_FIXED | MAP_PRIVATE | MAP_POPULATE, fd, 0);
    close(fd);

    mmap((void*) COMPUTING_STACK_START, COMPUTING_STACK_SIZE, PROT_READ | PROT_WRITE, MAP_FIXED | MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    mmap((void*) COMPUTING_HEAP_START, COMPUTING_HEAP_SIZE, PROT_READ | PROT_WRITE, MAP_FIXED | MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);

    mmap((void*) OUTPUT_AREA, OUTPUT_SIZE, PROT_READ | PROT_WRITE, MAP_FIXED | MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    
    mmap((void*) SECCOMP_AREA, SECCOMP_SIZE, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_FIXED | MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    unsigned char* ptr = (unsigned char*) seccomp_trampoline;
    unsigned long i=0;
    while(1){
        ((unsigned char*)SECCOMP_AREA)[i] = ptr[i];
        if(ptr[i] == 0xcc && ptr[i+1] == 0xcc & ptr[i+2] == 0xcc & ptr[i+3] == 0xcc){
            break;
        }
        i++;
    }
    mprotect((void*) SECCOMP_AREA, SECCOMP_SIZE, PROT_READ | PROT_EXEC);
    ((void (*)(void))SECCOMP_AREA)();;

    sleep(1000);
}




