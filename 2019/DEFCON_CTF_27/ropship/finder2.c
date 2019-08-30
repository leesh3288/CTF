#include <stdio.h>
#include <sys/mman.h>
#include <string.h>
#include <stdlib.h>

#define ROP_AREA_START 0x800000
#define ROP_SIZE 500000000

#define OUTPUT_AREA 0x50000000
#define OUTPUT_SIZE 0x10000000

unsigned long seed = 0;

unsigned long lcg(){
    seed = 6364136223846793005 * seed + 1442695040888963407;
    return seed;
}


char *find(char *search, char *target, int length)
{
        for (int i = 0; i < ROP_SIZE; i++)
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

int test(void)
{
        char inc_al[3] = "\xFE\xC0\xC3";
        char mul_eax[3] = "\xFE\x08\xC3";
        char dec_bytes_rax[3] = "\xFE\x08\xC3";
        char *inc_al_gadget = find((void *)ROP_AREA_START, inc_al, 3);
        char *mul_eax_gadget = find((void *)ROP_AREA_START, mul_eax, 3);
        char *dec_bytes_rax_gadget = find((void *)ROP_AREA_START, dec_bytes_rax, 3);
        unsigned long *target = (unsigned long *)OUTPUT_AREA;

        target[0] = inc_al_gadget;
        for (int i = 0; i < 30; i++)  // log2(0x40000000) == 30
        {
                target[i + 1] = mul_eax_gadget;
        }
        for (int i = 0; i < 2; i++)  // 'n' - 'l' == 2
        {
                target[i + 31] = dec_bytes_rax_gadget;
        }
        return 0;
}

int main(int argc, char **argv, char **envp)
{
        unsigned char *buf = (unsigned char *)mmap((void*)ROP_AREA_START, ROP_SIZE, PROT_READ | PROT_WRITE , MAP_FIXED | MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        mmap((void*)OUTPUT_AREA, OUTPUT_SIZE, PROT_READ | PROT_WRITE, MAP_FIXED | MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);


        if (argc >= 2)
                seed = strtoul(argv[1], NULL, 10);

        unsigned long size = ROP_SIZE;
        unsigned long tmp = 0;
        for (unsigned long i = 0; i < size; i += 8)
        {
                tmp = lcg();
                memcpy(&(buf[i]), &tmp, 8);
        }
        buf[0] = 0xc3;
        printf("testing...");

        return test();
}