use crate::cfg::*;
use crate::error::Error;
use crate::linear_scan::LinearScan;
use crate::vasm;

use core::fmt;
use std::collections::{HashMap, HashSet};

#[derive(Clone, Debug)]
pub enum Instruction {
    Mov { dst: Register, src: Register },
    MovImm { dst: Register, imm: i64 },
    Add { dst: Register, src: Register },
    Sub { dst: Register, src: Register },
    Load { dst: Register, addr: Register },
    Store { src: Register, addr: Register },
    Cmp { dst: Register, src: Register },
    Jmp { label: usize },
    Jz { label: usize },
    Jb { label: usize },
    Call { target: Register },
    Push { reg: Register },
    Pop { reg: Register },
    Return,
}

#[derive(Clone, Debug, PartialEq)]
pub enum Register {
    Rax,
    Rbx,
    Rcx,
    Rdx,
    Rdi,
    Rsi,
    R8,
    R9,
    R10,
    R11,
    R12,
    R13,
    R14,
    R15,
}

impl fmt::Display for Instruction {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Instruction::Mov { dst, src } => write!(f, "mov {}, {}", dst, src),
            Instruction::MovImm { dst, imm } => write!(f, "mov {}, {:#x}", dst, imm),
            Instruction::Add { dst, src } => write!(f, "add {}, {}", dst, src),
            Instruction::Sub { dst, src } => write!(f, "sub {}, {}", dst, src),
            Instruction::Load { dst, addr } => write!(f, "mov {}, [{}]", dst, addr),
            Instruction::Store { src, addr } => write!(f, "mov [{}], {}", addr, src),
            Instruction::Cmp { dst, src } => write!(f, "cmp {}, {}", dst, src),
            Instruction::Jmp { label } => write!(f, "jmp b{}", label),
            Instruction::Jz { label } => write!(f, "jz b{}", label),
            Instruction::Jb { label } => write!(f, "jb b{}", label),
            Instruction::Call { target } => write!(f, "call {}", target),
            Instruction::Pop { reg } => write!(f, "pop {}", reg),
            Instruction::Push { reg } => write!(f, "push {}", reg),
            Instruction::Return => write!(f, "ret"),
            _ => panic!("unreachable"),
        }
    }
}

impl fmt::Display for Register {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Register::Rax => write!(f, "rax"),
            Register::Rbx => write!(f, "rbx"),
            Register::Rcx => write!(f, "rcx"),
            Register::Rdx => write!(f, "rdx"),
            Register::Rdi => write!(f, "rdi"),
            Register::Rsi => write!(f, "rsi"),
            Register::R8 => write!(f, "r8"),
            Register::R9 => write!(f, "r9"),
            Register::R10 => write!(f, "r10"),
            Register::R11 => write!(f, "r11"),
            Register::R12 => write!(f, "r12"),
            Register::R13 => write!(f, "r13"),
            Register::R14 => write!(f, "r14"),
            Register::R15 => write!(f, "r15"),
        }
    }
}

impl fmt::Display for Block {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        for instr in self.instructions.iter() {
            writeln!(f, "{}", instr)?;
        }
        Ok(())
    }
}

impl fmt::Display for TranslationUnit {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        for bid in 0..self.blocks.len() {
            let block = self.blocks.get(&bid).unwrap();
            writeln!(f, "b{}", bid)?;
            writeln!(f, "{}", block)?;
        }
        Ok(())
    }
}

pub struct Block {
    pub instructions: Vec<Instruction>,
}

pub struct TranslationUnit {
    pub blocks: HashMap<usize, Block>,
    pub cfg: CFG,
    pub start: usize,
}

impl TranslationUnit {
    pub fn new(source: &vasm::TranslationUnit) -> Result<Self, Error> {
        let linear_scan = LinearScan::new(source)?;
        let mut callee_saved_regs = Vec::new();
        for (logical, physical) in linear_scan.allocation_table.iter() {
            if !callee_saved_regs.contains(physical) {
                callee_saved_regs.push(physical.clone());
            }
        }
        let mut blocks = HashMap::new();
        for (&bid, block) in source.blocks.iter() {
            let mut instructions = Vec::new();
            if bid == source.start {
                for reg in callee_saved_regs.iter() {
                    instructions.push(Instruction::Push { reg: reg.clone() });
                }
            }
            for instr in block.instructions.iter() {
                let asm_instrs = match instr {
                    vasm::Instruction::Mov { dst, src } => vec![Instruction::Mov {
                        dst: linear_scan.lookup(dst),
                        src: linear_scan.lookup(src),
                    }],
                    vasm::Instruction::MovImm { dst, imm } => vec![Instruction::MovImm {
                        dst: linear_scan.lookup(dst),
                        imm: *imm,
                    }],
                    vasm::Instruction::Add { dst, src } => vec![Instruction::Add {
                        dst: linear_scan.lookup(dst),
                        src: linear_scan.lookup(src),
                    }],
                    vasm::Instruction::Sub { dst, src } => vec![Instruction::Sub {
                        dst: linear_scan.lookup(dst),
                        src: linear_scan.lookup(src),
                    }],
                    vasm::Instruction::Load { dst, addr } => vec![Instruction::Load {
                        dst: linear_scan.lookup(dst),
                        addr: linear_scan.lookup(addr),
                    }],
                    vasm::Instruction::Store { src, addr } => vec![Instruction::Store {
                        src: linear_scan.lookup(src),
                        addr: linear_scan.lookup(addr),
                    }],
                    vasm::Instruction::Cmp { dst, src } => vec![Instruction::Cmp {
                        dst: linear_scan.lookup(dst),
                        src: linear_scan.lookup(src),
                    }],
                    vasm::Instruction::Jmp { label } => vec![Instruction::Jmp { label: *label }],
                    vasm::Instruction::Jz { label } => vec![Instruction::Jz { label: *label }],
                    vasm::Instruction::Jb { label } => vec![Instruction::Jb { label: *label }],
                    vasm::Instruction::Call { target } => vec![Instruction::Call {
                        target: linear_scan.lookup(target),
                    }],
                    vasm::Instruction::Return => {
                        let mut instrs = Vec::new();
                        for reg in callee_saved_regs.iter().rev() {
                            instrs.push(Instruction::Pop { reg: reg.clone() });
                        }
                        instrs.push(Instruction::Return);
                        instrs
                    }
                };
                instructions.extend(asm_instrs);
            }
            blocks.insert(
                bid,
                Block {
                    instructions: instructions,
                },
            );
        }
        Ok(Self {
            blocks: blocks,
            cfg: source.cfg.clone(),
            start: source.start,
        })
    }
}
