
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

unsigned long seed = 0;

unsigned long lcg(){
    seed = 6364136223846793005 * seed + 1442695040888963407;
    return seed;
}

int main(int argc, char** argv){
    seed = strtoul(argv[1], NULL, 10);
    unsigned long size = strtoul(argv[2], NULL, 10);
    unsigned char* buf = (unsigned char*) malloc(size);
    for(unsigned long i=0; i<size; i+=8){
        unsigned long tmp = lcg();
        memcpy(&(buf[i]), &tmp, 8);
    }
    buf[0] = 0xc3;

    FILE* fp = fopen(argv[3], "wb");
    fwrite(buf, size, 1, fp);
    fclose(fp);
    return 0;
}

