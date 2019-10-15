# -*- coding: utf-8 -*-

import sys


class Code(object):
    text_table = "🈳➕➖❌❓❎👫💀💯🚀🈶🈚⏬🔝📤📥🆕🆓📄📝🔡🔢🛑"
    data_table = "😀😁😂🤣😜😄😅😆😉😊😍"
    inst_str = ["NOP", "ADD", "SUB", "MUL", "MOD", "XOR", "AND", "LESS", "EQ",
                "JMP", "JMPT", "JMPF", "PUSH", "POP", "GET_BYTE", "SET_BYTE",
                "NEW_GBUF", "DEL_GBUF", "READ_GBUF", "WRITE_GBUF", "", "",
                "HALT"]

    def __init__(self, filename):
        with open(filename, "r") as f:
            self.text = f.read()

    def debug(self, pc, opcode):
        instr = self.inst_str[opcode - 1]
        print("Instruction(0x{:04X}): {}".format(pc, instr))
        if 2 <= opcode <= 9:
            oper1, oper2 = self.stack[-1], self.stack[-2]
            print("{} {:d}, {:d}".format(instr, oper1, oper2))
        elif opcode == 10:
            print("JMP to 0x{:04X}".format(self.stack[-1]))
        elif opcode == 11:
            if self.stack[-2]:
                print("JMP to 0x{:04X}".format(self.stack[-1]))
        elif opcode == 12:
            if not self.stack[-2]:
                print("JMP to 0x{:04X}".format(self.stack[-1]))
        elif opcode == 13:
            val = self.data_table.find(self.text[pc + 1])
            print("PUSH {:d}".format(val))
        elif opcode == 15:
            idx = self.stack[-1]
            target = self.gbuf[idx]
            assert target
            print("TARGET STRING: {}".format(bytes(target)))
            i = self.stack[-2]
            print("TARGET CHAR: '{}' ({:d})".format(chr(target[i]), i))
        elif opcode == 16:
            idx = self.stack[-1]
            target = self.gbuf[idx]
            assert target
            print("TARGET STRING: {}".format(bytes(target)))
            i = self.stack[-2]
            char = self.stack[-3]
            print("TARGET CHAR: '{}' ({:d})".format(chr(char % 0x100), i))
        elif opcode == 17:
            length = self.stack[-1]
            for i in range(len(self.gbuf)):
                if not self.gbuf[i]:
                    break
            print("NEW STRING ({:d}) in slot {:d}".format(length, i))
        elif opcode == 18:
            idx = self.stack[-1]
            print("DELETE STRING: \"{}\" ({:d})".format(self.gbuf[idx], idx))
        elif opcode == 19:
            idx = self.stack[-1]
            print("READ STRING ({:d})".format(len(self.gbuf[idx])))
        elif opcode == 20:
            idx = self.stack[-1]
            print("WRITE STRING: \"{}\" ({:d})".format(self.gbuf[idx], idx))

    def interpret(self, debug=False):
        self.pc = 0
        self.stack = []
        self.gbuf = [None] * 10

        while self.pc < len(self.text):
            opcode = self.text_table.find(self.text[self.pc]) + 1

            if debug:
                self.debug(self.pc, opcode)

            if opcode == 1:
                self.pc += 1
            elif opcode == 2:
                self.stack.append(self.stack.pop() + self.stack.pop())
                self.pc += 1
            elif opcode == 3:
                self.stack.append(self.stack.pop() - self.stack.pop())
                self.pc += 1
            elif opcode == 4:
                self.stack.append(self.stack.pop() * self.stack.pop())
                self.pc += 1
            elif opcode == 5:
                self.stack.append(self.stack.pop() % self.stack.pop())
                self.pc += 1
            elif opcode == 6:
                self.stack.append(self.stack.pop() ^ self.stack.pop())
                self.pc += 1
            elif opcode == 7:
                self.stack.append(self.stack.pop() & self.stack.pop())
                self.pc += 1
            elif opcode == 8:
                self.stack.append(self.stack.pop() < self.stack.pop())
                self.pc += 1
            elif opcode == 9:
                self.stack.append(self.stack.pop() == self.stack.pop())
                self.pc += 1
            elif opcode == 10:
                self.pc = self.stack.pop()
            elif opcode == 11:
                nextpc = self.stack.pop()
                if self.stack.pop():
                    self.pc = nextpc
                else:
                    self.pc += 1
            elif opcode == 12:
                nextpc = self.stack.pop()
                if self.stack.pop():
                    self.pc += 1
                else:
                    self.pc = nextpc
            elif opcode == 13:
                val = self.data_table.find(self.text[self.pc + 1])
                assert val != -1
                self.stack.append(val)
                self.pc += 2
            elif opcode == 14:
                self.stack.pop()
                self.pc += 1
            elif opcode == 15:
                idx = self.stack.pop()
                str_idx = self.stack.pop()
                assert self.gbuf[idx]
                assert str_idx < len(self.gbuf[idx])
                self.stack.append(self.gbuf[idx][str_idx])
                self.pc += 1
            elif opcode == 16:
                idx = self.stack.pop()
                str_idx = self.stack.pop()
                val = self.stack.pop()
                assert self.gbuf[idx]
                assert str_idx < len(self.gbuf[idx])
                self.gbuf[idx][str_idx] = val % 0x100
                self.pc += 1
            elif opcode == 17:
                length = self.stack.pop()
                assert length <= 1500
                for i in range(len(self.gbuf)):
                    if not self.gbuf[i]:
                        self.gbuf[i] = bytearray(length)
                self.pc += 1
            elif opcode == 18:
                idx = self.stack.pop()
                assert self.gbuf[idx]
                self.gbuf[idx] = None
                self.pc += 1
            elif opcode == 19:
                idx = self.stack.pop()
                assert self.gbuf[idx]
                read = sys.stdin.buffer.read(len(self.gbuf[idx]))
                self.gbuf[idx] = bytearray(read)
                self.pc += 1
            elif opcode == 20:
                idx = self.stack.pop()
                assert self.gbuf[idx]
                sys.stdout.buffer.write(self.gbuf[idx])
                sys.stdout.buffer.flush()
                self.pc += 1
            elif opcode == 21:
                self.pc += 1
            elif opcode == 22:
                self.pc += 1
            elif opcode == 23:
                break

            if debug:
                print("========== STACK ==========")
                print(self.stack)
                print("===========================")
                print("========== GBUF ==========")
                for i, s in enumerate(self.gbuf):
                    if s:
                        print("{:d}: {}".format(i, bytes(s)))
                print("==========================")

    def __str__(self):
        pass


code = Code("chal.evm")
code.interpret()