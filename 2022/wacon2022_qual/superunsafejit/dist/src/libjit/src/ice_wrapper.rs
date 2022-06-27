use std::collections::HashMap;
use std::convert::TryInto;

use crate::asm;
use crate::cfg::*;
use crate::error::Error;

use iced_x86::code_asm::*;
use iced_x86::{
    Decoder, DecoderOptions, Formatter, Instruction, NasmFormatter, SymbolResolver, SymbolResult,
};

fn convert_reg(reg: &asm::Register) -> AsmRegister64 {
    match reg {
        asm::Register::Rax => rax,
        asm::Register::Rcx => rcx,
        asm::Register::Rdx => rdx,
        asm::Register::R8 => r8,
        asm::Register::R9 => r9,
        asm::Register::R10 => r10,
        asm::Register::R11 => r11,
        asm::Register::Rbx => rbx,
        asm::Register::Rdi => rdi,
        asm::Register::Rsi => rsi,
        asm::Register::R12 => r12,
        asm::Register::R13 => r13,
        asm::Register::R14 => r14,
        asm::Register::R15 => r15,
    }
}

fn encode_instruction(
    a: &mut CodeAssembler,
    instruction: &asm::Instruction,
    labels: &HashMap<usize, CodeLabel>,
) -> Result<(), Error> {
    match instruction {
        asm::Instruction::Mov { dst, src } => match a.mov(convert_reg(dst), convert_reg(src)) {
            Err(e) => Err(Error::AssemblerError),
            _ => Ok(()),
        },
        asm::Instruction::MovImm { dst, imm } => match a.mov(convert_reg(dst), *imm as i64) {
            Err(e) => Err(Error::AssemblerError),
            _ => Ok(()),
        },
        asm::Instruction::Add { dst, src } => match a.add(convert_reg(dst), convert_reg(src)) {
            Err(e) => Err(Error::AssemblerError),
            _ => Ok(()),
        },
        asm::Instruction::Sub { dst, src } => match a.sub(convert_reg(dst), convert_reg(src)) {
            Err(e) => Err(Error::AssemblerError),
            _ => Ok(()),
        },
        asm::Instruction::Load { dst, addr } => {
            match a.mov(convert_reg(dst), qword_ptr(convert_reg(addr))) {
                Err(e) => Err(Error::AssemblerError),
                _ => Ok(()),
            }
        }
        asm::Instruction::Store { src, addr } => {
            match a.mov(qword_ptr(convert_reg(addr)), convert_reg(src)) {
                Err(e) => Err(Error::AssemblerError),
                _ => Ok(()),
            }
        }
        asm::Instruction::Cmp { dst, src } => match a.cmp(convert_reg(dst), convert_reg(src)) {
            Err(e) => Err(Error::AssemblerError),
            _ => Ok(()),
        },
        asm::Instruction::Jmp { label } => {
            let l = labels.get(label).unwrap().clone();
            match a.jmp(l) {
                Err(e) => Err(Error::AssemblerError),
                _ => Ok(()),
            }
        }
        asm::Instruction::Jz { label } => {
            let l = labels.get(label).unwrap().clone();
            match a.je(l) {
                Err(e) => Err(Error::AssemblerError),
                _ => Ok(()),
            }
        }
        asm::Instruction::Jb { label } => {
            let l = labels.get(label).unwrap().clone();
            match a.jb(l) {
                Err(e) => Err(Error::AssemblerError),
                _ => Ok(()),
            }
        }
        asm::Instruction::Call { target } => {
            match a.call(convert_reg(target)) {
                Err(e) => Err(Error::AssemblerError),
                _ => Ok(()),
            }
        }
        asm::Instruction::Push { reg } => match a.push(convert_reg(reg)) {
            Err(e) => Err(Error::AssemblerError),
            _ => Ok(()),
        },
        asm::Instruction::Pop { reg } => match a.pop(convert_reg(reg)) {
            Err(e) => Err(Error::AssemblerError),
            _ => Ok(()),
        },
        asm::Instruction::Return => match a.ret() {
            Err(e) => Err(Error::AssemblerError),
            _ => Ok(()),
        },
        _ => panic!("unreachable"),
    }
}

pub fn assemble(source: &asm::TranslationUnit, code_addr: u64) -> Result<Vec<u8>, Error> {
    let mut assembler = match CodeAssembler::new(64) {
        Err(e) => {
            return Err(Error::AssemblerError);
        }
        Ok(a) => a,
    };
    let mut labels = HashMap::new();
    let mut po = cfg_traverse_po(&source.cfg, source.start);
    po.reverse();
    for &bid in po.iter() {
        labels.insert(bid, assembler.create_label());
    }
    for &bid in po.iter() {
        let block = source.blocks.get(&bid).unwrap();
        for (iid, instr) in block.instructions.iter().enumerate() {
            if iid == 0 {
                assembler.set_label(labels.get_mut(&bid).unwrap());
            }
            encode_instruction(&mut assembler, instr, &labels);
        }
    }
    match assembler.assemble(code_addr) {
        Err(e) => Err(Error::AssemblerError),
        Ok(a) => Ok(a),
    }
}

pub fn print_disassembly(bytes: &Vec<u8>, code_addr: u64) {
    let mut output = String::new();
    let bytes_code = &bytes[0..bytes.len()];
    let mut decoder = Decoder::new(64, bytes_code, DecoderOptions::NONE);
    decoder.set_ip(code_addr);
    let mut formatter = NasmFormatter::new();
    formatter.options_mut().set_first_operand_char_index(8);
    for instruction in &mut decoder {
        output.clear();
        formatter.format(&instruction, &mut output);
        println!("{:016X} {}", instruction.ip(), output);
    }
    
}
