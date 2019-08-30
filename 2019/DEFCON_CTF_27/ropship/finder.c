// -mcmodel=large

#include <sys/mman.h>
#include <stdlib.h>

#define ROP_AREA_START 0x00800000  
#define ROP_AREA_SIZE (500ULL * 1000000) 

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

unsigned long seed = 0;

unsigned long lcg(){
    seed = 6364136223846793005 * seed + 1442695040888963407;
    return seed;
}

typedef struct st_gadget{
    int len;
    ull val;
    void *addr;
} st_gadget;

typedef unsigned long long ull;

char *find(char *search, char *target, int length)
{
    for (int i = 0; i < ROP_AREA_START; i++)
    {
        int is_search = 1;
        for (int j = 0; j < length; j++)
        {
            if (search[i + j] != target[j])
            {
                is_search = 0;
                break;
            }
        }
        if (is_search)
                return &search[i];
    }
    return NULL;
}

int main(void)
{
    unsigned char *buf = (unsigned char *)mmap((void*)ROP_AREA_START, ROP_AREA_START, PROT_READ | PROT_WRITE , MAP_FIXED | MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    mmap((void*)OUTPUT_AREA, OUTPUT_SIZE, PROT_READ | PROT_WRITE, MAP_FIXED | MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);

    volatile st_gadget target_mov[] = { {3, 0x8937c3, 0} };
    volatile char *rop_area = ROP_AREA_START;

    volatile ull hashed = 0;
    for (volatile ull ofs = 0; ofs < ROP_AREA_SIZE; ofs++)
    {

    }

    return 0;
}