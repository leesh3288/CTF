#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

struct one_time_pad {
    int in_use;
    size_t len;
    char *data;
};

struct one_time_pad pad[8];
char *line = NULL;
size_t lsize = 0;
int rewrites = 1;

void fail(const char *err) {
    puts(err);
    exit(1);
}

int get_free(void){
    for (int i = 0; i < sizeof(pad) / sizeof(pad[0]); ++i) {
        if (!pad[i].in_use)
            return i;
    }
    return -1;
}

ssize_t read_line() {
    ssize_t rl = getline(&line, &lsize, stdin);
    if (rl < 0)
        fail("error while reading a line");
    if (!rl || line[rl - 1] != '\n')
        rl += 1;
    line[rl - 1] = 0;
    return rl;
}

unsigned read_idx() {
    ssize_t rl = read_line();
    char *tmp;
    unsigned idx = strtoul(line, &tmp, 0);
    if (tmp + 1 != line + rl || idx >= sizeof(pad) / sizeof(pad[0]))
        fail("quit your shady BS");
    return idx;
}

void write(void) {
    int idx = get_free();
    if (idx < 0)
        fail("for security reasons only a small number of one time pads can be stored");
    read_line();
    pad[idx].in_use = 1;
    pad[idx].len = strlen(line);
    pad[idx].data = strdup(line);
}

void read(void) {
    unsigned idx = read_idx();
    if (pad[idx].in_use) {
        puts(pad[idx].data);
        free(pad[idx].data);
        pad[idx].in_use = 0;
    } else
        fail("you can only use a one time pad once dummy!");
}

void rewrite(void) {
    if (rewrites) {
        --rewrites;
    } else {
        fail("You are a liabilty!");
    }
    unsigned idx = read_idx();
    ssize_t rl = read_line();
    if (rl > pad[idx].len)
        fail("you don't have enough space");
    strcpy(pad[idx].data, line);
}

int main(int argc, char **argv) {
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);
    while (1) {
        puts("w̲rite");
        puts("r̲ead");
        puts("re̲write");
        printf("> ");
        read_line();
        switch(line[0]) {
            case 'w':
                write();
                break;
            case 'r':
                read();
                break;
            case 'e':
                rewrite();
                break;
            default:
                return 0;
        }
    }
}