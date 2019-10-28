#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
#include <assert.h>
#include <fcntl.h>
#include <dlfcn.h>

#define ASLR_ENTROPEH 3 // should be enough...
#define MORETIME 23 // because illuminati
#define LONGNESS 64 // cause that's how long a long long is

// These are just some utility macros for the shellcoding part.
#define PUSH(reg) "push %" #reg "\n"
#define POP(reg) "pop %" #reg "\n"
#define CLEAR(reg) "xor %" #reg ", %" # reg "\n"

#define PUSH_ALL() do { asm volatile ( \
      PUSH(rax) PUSH(rbx) PUSH(rcx) PUSH(rdx) \
      PUSH(rsi) PUSH(rdi) \
      PUSH(r8) PUSH(r9) PUSH(r10) PUSH(r11) \
      PUSH(r12) PUSH(r13) PUSH(r14) PUSH(r15) \
      PUSH(rbp) \
      ); } while(0)

#define POP_ALL() do { asm volatile ( \
      "1:\n" \
      POP(rbp) \
      POP(r15) POP(r14) POP(r13) POP(r12) \
      POP(r11) POP(r10) POP(r9) POP(r8) \
      POP(rdi) POP(rsi) \
      POP(rdx) POP(rcx) POP(rbx) POP(rax) \
    ); } while(0)

long read_long() {
  char buf[LONGNESS];
  bzero(buf, LONGNESS);
  for (unsigned char i = 0; i < LONGNESS; i++) {
    if ((read(STDIN_FILENO, buf+i, 1) != 1) || (buf[i] == '\n')) {
      buf[i] = 0;
      break;
    }
  }
  return strtol(buf, NULL, 10);
}

__attribute__((always_inline))
inline void do_shellcode() {
  // Wanna try shellcoding? Here you go!
  char *playground = NULL;
  int urandom = -1;

  // We even roll our own ASLR for MAXIMUM SEKURITEH!
  urandom = open("/dev/urandom", O_RDONLY);
  if (urandom == -1) {
    perror("YNORANDOMNESS?!");
    exit(1);
  }

  if (read(urandom, &playground, ASLR_ENTROPEH) == -1) {
    perror("NEED MOAR ENTROPEH");
    exit(1);
  }
  close(urandom);
  // XXX: check if close() failed...

  // Make sure we're page-aligned
  playground = (char*) ((unsigned long long) playground << 12);

  // No 32-bit magic!
  playground = (char*) ((unsigned long long) playground | (1UL<<33));

  playground = mmap(playground,
      1 << 12,
      PROT_READ | PROT_WRITE | PROT_EXEC,
      MAP_PRIVATE | MAP_ANON | MAP_EXCL | MAP_FIXED,
      -1,
      0);

  if (playground == MAP_FAILED) {
    perror("RESPECT MAH MMAP");
    exit(1);
  }

  puts("All your shellcode are belong to us!\n");
  read(STDIN_FILENO, playground, 0x5);

  // In case your shellcode gets lost, here's the way back:
  memcpy(playground+0x5, "H\xb8", 2); // mov rax
  memcpy(playground+0xf, "H\xbc", 2); // mov rsp
  memcpy(playground+0x19, "\xff\xe0", 2); // jmp rax

  // Push ALL THE THINGS!!!11elf
  PUSH_ALL();

  // Clear ALL THE THINGS!!! *well nearly...
  asm volatile(
      CLEAR(rsi) CLEAR(rdi)
      CLEAR(r8) CLEAR(r9) CLEAR(r10) CLEAR(r11)
      CLEAR(r12) CLEAR(r13) CLEAR(r14) CLEAR(r15)
      CLEAR(rbx) CLEAR(rcx) CLEAR(rdx)
  );

  asm volatile(
      "movabs $1f, %%rdx\n"
      "mov %%rdx, 0x7(%%rax)\n"
      "mov %%rsp, 0x11(%%rax)\n"
      "xor %%rdx, %%rdx\n"
      "xor %%rbp, %%rbp\n"
      "xor %%rsp, %%rsp\n"
      "jmp *%0\n"
      :: "a"(playground) :
  );

  // Pop ALL TEH THINGS!!!
  POP_ALL();
}

__attribute__((always_inline))
inline void do_rop() {
  char ropmebaby[1*MORETIME];
  long smells_fishy = 0;

  printf("yay, you didn't crash this thing! Have a pointer, you may need it: %p\n", dlsym(RTLD_NEXT, "system"));

  printf("You shouldn't need this pointer, but this is an easy challenge: %p\n", &ropmebaby[0]);
  fflush(stdout);

  printf("How much is the fish?\n");
  fflush(stdout);
  smells_fishy = read_long();
  printf("Okay, gimme your %ld bytes of ropchain!\n", smells_fishy);
  fflush(stdout);
  read(STDIN_FILENO, ropmebaby, smells_fishy);
}

int main() {
  setvbuf(stdout, NULL, _IONBF, 0);
  setvbuf(stdin, NULL, _IONBF, 0);
  setvbuf(stderr, NULL, _IONBF, 0);

  do_shellcode();
  do_rop();
  return 0;
}
