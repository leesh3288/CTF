#include <signal.h>
#include <stdio.h>
#include <stdbool.h>
#include <strings.h>
#include <unistd.h>

#define ALARM_SECONDS 30
#define MEMSZ 0x20
#define ARRLEN(arr) (sizeof(arr)/sizeof(arr[0]))
#define UNUSED __attribute__((unused))

void initialize() __attribute__((constructor));
void handle_sigalrm(int);
bool loop(long, long*);
void echo();
long getidx(long);
long getlong();

int main(void)
{
    long mem[MEMSZ];
    do {
        bzero(mem, sizeof(mem));
    } while (loop(ARRLEN(mem), mem));
    _exit(0);
}

void initialize()
{
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
    signal(SIGALRM, handle_sigalrm);
    alarm(ALARM_SECONDS);
}

void handle_sigalrm(int sig UNUSED)
{
    _exit(-1);
}

bool loop(long len, long *mem)
{
    while (1)
    {
        switch (getlong())
        {
            case 0:
                return true;
            case 1: {
                echo();
            } break;
            case 2: {
                mem[getidx(len)] = getlong();
            } break;
            case 3: {
                printf("%ld\n", mem[getidx(len)]);
            } break;
            default:
                return false;
        }
    }
}

void echo()
{
    char buf[80];
    if (scanf("%80s", buf) != 1)
        _exit(1);
    puts(buf);
}

long getidx(long len)
{
    long idx = getlong();
    if (idx < 0) return 0;
    else if (idx >= len) return len - 1;
    return idx;
}

long getlong()
{
    long val;
    if (scanf("%ld", &val) != 1)
        _exit(1);
    return val;
}
