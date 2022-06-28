use crate::bytecode;
use crate::cfg::*;
use crate::error::Error;
use crate::memory::Memory;

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
    Return,
}

#[derive(PartialEq, Eq, Hash, Clone, Debug)]
pub enum Register {
    Virtual(usize),
    Rax,
    Rsp,
    Rdi,
    Rsi,
    Rdx,
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
            Instruction::Return => write!(f, "ret"),
        }
    }
}

impl fmt::Display for Register {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Register::Virtual(rid) => write!(f, "r{}", rid),
            Register::Rax => write!(f, "rax"),
            Register::Rsp => write!(f, "rsp"),
            Register::Rdi => write!(f, "rdi"),
            Register::Rsi => write!(f, "rsi"),
            Register::Rdx => write!(f, "rdx"),
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

type FunctionTable = HashMap<String, u64>;

pub struct TranslationUnit {
    pub blocks: HashMap<usize, Block>,
    free_rid: usize,
    free_bid: usize,
    pub cfg: CFG,
    pub start: usize,
}

fn get_function(function_table: &FunctionTable, name: &str) -> Result<u64, Error> {
    match function_table.get(name) {
        Some(addr) => Ok(*addr),
        None => Err(Error::FunctionNotFoundError),
    }
}

fn bytecode_to_cfg(bytecode: &bytecode::TranslationUnit) -> Result<CFG, Error> {
    let mut stack = vec![0];
    let mut cfg = CFG::new();
    while stack.len() > 0 {
        let bid = stack.pop().unwrap();
        if cfg.contains_key(&bid) {
            continue;
        }
        let block = match bytecode.blocks.get(&bid) {
            Some(b) => b,
            None => panic!("unreachable"),
        };
        match block.exit {
            bytecode::BlockExit::Jmp { bid: bid_target } => {
                cfg.entry(bid)
                    .or_insert_with(HashSet::new)
                    .insert(bid_target);
                stack.push(bid_target);
            }
            bytecode::BlockExit::Jez {
                cond_reg: _,
                bid_isz,
                bid_isnz,
            } => {
                cfg.entry(bid).or_insert_with(HashSet::new).insert(bid_isz);
                cfg.entry(bid).or_insert_with(HashSet::new).insert(bid_isnz);
                stack.push(bid_isz);
                stack.push(bid_isnz);
            }
            bytecode::BlockExit::Return => {
                cfg.entry(bid).or_insert_with(HashSet::new);
            }
            _ => panic!("unreachable"),
        };
    }
    Ok(cfg)
}

impl TranslationUnit {
    fn allocate_vreg(&mut self) -> Register {
        self.free_rid += 1;
        Register::Virtual(self.free_rid - 1)
    }

    fn allocate_bid(&mut self) -> usize {
        self.free_bid += 1;
        self.free_bid - 1
    }

    fn translate_bounds_check(
        &mut self,
        addr: Register,
        memory: &Memory,
        function_table: &FunctionTable,
        bid: usize,
    ) -> Result<usize, Error> {
        let bid_then = self.allocate_bid();
        let bid_else = self.allocate_bid();
        let temp = self.allocate_vreg();
        let mut block_then = Block {
            instructions: Vec::new(),
        };
        let mut else_instructions = Vec::new();
        else_instructions.push(Instruction::MovImm {
            dst: temp.clone(),
            imm: get_function(function_table, "deoptimize")? as i64,
        });
        else_instructions.push(Instruction::Call { target: temp });
        else_instructions.push(Instruction::Return);
        let mut block_else = Block {
            instructions: else_instructions,
        };
        self.blocks.insert(bid_then, block_then);
        self.blocks.insert(bid_else, block_else);
        self.cfg
            .entry(bid)
            .or_insert_with(HashSet::new)
            .insert(bid_then);
        self.cfg
            .entry(bid)
            .or_insert_with(HashSet::new)
            .insert(bid_else);
        self.cfg.entry(bid_then).or_insert_with(HashSet::new);
        self.cfg.entry(bid_else).or_insert_with(HashSet::new);
        let temp_reg = self.allocate_vreg();
        let block = match self.blocks.get_mut(&bid) {
            Some(b) => b,
            None => panic!("unreachable"),
        };
        let lower_bound = memory.pointer as u64;
        let upper_bound = lower_bound + memory.length as u64 - 8;
        block.instructions.push(Instruction::MovImm {
            dst: temp_reg.clone(),
            imm: lower_bound as i64,
        });
        block.instructions.push(Instruction::Cmp {
            dst: addr.clone(),
            src: temp_reg.clone(),
        });
        block.instructions.push(Instruction::Jb { label: bid_else });
        block.instructions.push(Instruction::MovImm {
            dst: temp_reg.clone(),
            imm: upper_bound as i64,
        });
        block.instructions.push(Instruction::Cmp {
            dst: temp_reg,
            src: addr,
        });
        block.instructions.push(Instruction::Jb { label: bid_else });
        block
            .instructions
            .push(Instruction::Jmp { label: bid_then });
        Ok(bid_then)
    }

    fn translate_instruction(
        &mut self,
        source: &bytecode::Instruction,
        memory: &Memory,
        function_table: &FunctionTable,
        bid: usize,
    ) -> Result<usize, Error> {
        match source {
            bytecode::Instruction::LoadImm { dst_reg, imm } => {
                let block = match self.blocks.get_mut(&bid) {
                    Some(b) => b,
                    None => panic!("unreachable"),
                };
                block.instructions.push(Instruction::MovImm {
                    dst: Register::Virtual(*dst_reg as usize),
                    imm: *imm as i64,
                });
                Ok(bid)
            }
            bytecode::Instruction::LoadMem {
                dst_reg,
                base_reg,
                offset_imm,
            } => {
                let addr_reg = self.allocate_vreg();
                let imm_reg = self.allocate_vreg();
                let block = match self.blocks.get_mut(&bid) {
                    Some(b) => b,
                    None => panic!("unreachable"),
                };
                block.instructions.push(Instruction::MovImm {
                    dst: addr_reg.clone(),
                    imm: memory.pointer as i64,
                });
                block.instructions.push(Instruction::MovImm {
                    dst: imm_reg.clone(),
                    imm: *offset_imm as i64,
                });
                block.instructions.push(Instruction::Add {
                    dst: imm_reg.clone(),
                    src: Register::Virtual(*base_reg as usize),
                });
                block.instructions.push(Instruction::Add {
                    dst: addr_reg.clone(),
                    src: imm_reg,
                });
                
                /*
                let bid =
                    self.translate_bounds_check(addr_reg.clone(), memory, function_table, bid)?;
                */
                
                match self.blocks.get_mut(&bid) {
                    Some(b) => {
                        b.instructions.push(Instruction::Load {
                            dst: Register::Virtual(*dst_reg as usize),
                            addr: addr_reg,
                        });
                        Ok(bid)
                    }
                    None => panic!("unreachable"),
                }
            }
            bytecode::Instruction::StoreMem {
                src_reg,
                base_reg,
                offset_imm,
            } => {
                let addr_reg = self.allocate_vreg();
                let imm_reg = self.allocate_vreg();
                let block = match self.blocks.get_mut(&bid) {
                    Some(b) => b,
                    None => panic!("unreachable"),
                };
                block.instructions.push(Instruction::MovImm {
                    dst: addr_reg.clone(),
                    imm: memory.pointer as i64,
                });
                block.instructions.push(Instruction::MovImm {
                    dst: imm_reg.clone(),
                    imm: *offset_imm as i64,
                });
                block.instructions.push(Instruction::Add {
                    dst: imm_reg.clone(),
                    src: Register::Virtual(*base_reg as usize),
                });
                block.instructions.push(Instruction::Add {
                    dst: addr_reg.clone(),
                    src: imm_reg,
                });
                
                /*
                let bid =
                    self.translate_bounds_check(addr_reg.clone(), memory, function_table, bid)?;
                */

                match self.blocks.get_mut(&bid) {
                    Some(b) => {
                        b.instructions.push(Instruction::Store {
                            src: Register::Virtual(*src_reg as usize),
                            addr: addr_reg,
                        });
                        Ok(bid)
                    }
                    None => panic!("unreachable"),
                }
            }
            bytecode::Instruction::Add { dst_reg, src_reg } => match self.blocks.get_mut(&bid) {
                Some(b) => {
                    b.instructions.push(Instruction::Add {
                        dst: Register::Virtual(*dst_reg as usize),
                        src: Register::Virtual(*src_reg as usize),
                    });
                    Ok(bid)
                }
                None => panic!("unreachable"),
            },
            bytecode::Instruction::Sub { dst_reg, src_reg } => match self.blocks.get_mut(&bid) {
                Some(b) => {
                    b.instructions.push(Instruction::Sub {
                        dst: Register::Virtual(*dst_reg as usize),
                        src: Register::Virtual(*src_reg as usize),
                    });
                    Ok(bid)
                }
                None => panic!("unreachable"),
            },
            _ => panic!("unimplemented"),
        }
    }

    fn translate_block_exit(
        &mut self,
        source: &bytecode::BlockExit,
        bid: usize,
        block_mappings: &HashMap<usize, usize>,
    ) -> Result<usize, Error> {
        match source {
            bytecode::BlockExit::Jmp { bid: target_bid } => match self.blocks.get_mut(&bid) {
                Some(b) => {
                    let &vasm_bid = block_mappings.get(target_bid).unwrap();
                    b.instructions.push(Instruction::Jmp { label: vasm_bid });
                    self.cfg
                        .entry(bid)
                        .or_insert_with(HashSet::new)
                        .insert(vasm_bid);
                    Ok(vasm_bid)
                }
                None => panic!("unreachable"),
            },
            bytecode::BlockExit::Jez {
                cond_reg,
                bid_isz,
                bid_isnz,
            } => {
                let temp = self.allocate_vreg();
                match self.blocks.get_mut(&bid) {
                    Some(b) => {
                        b.instructions.push(Instruction::MovImm {
                            dst: temp.clone(),
                            imm: 0,
                        });
                        b.instructions.push(Instruction::Cmp {
                            dst: Register::Virtual(*cond_reg as usize),
                            src: temp,
                        });
                        let &vasm_bid_isz = block_mappings.get(bid_isz).unwrap();
                        let &vasm_bid_isnz = block_mappings.get(bid_isnz).unwrap();
                        b.instructions.push(Instruction::Jz {
                            label: vasm_bid_isz,
                        });
                        b.instructions.push(Instruction::Jmp {
                            label: vasm_bid_isnz,
                        });
                        self.cfg
                            .entry(bid)
                            .or_insert_with(HashSet::new)
                            .insert(vasm_bid_isz);
                        self.cfg
                            .entry(bid)
                            .or_insert_with(HashSet::new)
                            .insert(vasm_bid_isnz);
                        Ok(bid)
                    }
                    None => panic!("unreachable"),
                }
            }
            Return => match self.blocks.get_mut(&bid) {
                Some(b) => {
                    b.instructions.push(Instruction::Mov {
                        dst: Register::Rax,
                        src: Register::Virtual(0x0),
                    });
                    b.instructions.push(Instruction::Return);
                    self.cfg.entry(bid).or_insert_with(HashSet::new);
                    Ok(bid)
                }
                None => panic!("unreachable"),
            },
        }
    }

    pub fn new(
        bytecode: &bytecode::TranslationUnit,
        memory: &Memory,
        function_table: &FunctionTable,
    ) -> Result<Self, Error> {
        let mut blocks = HashMap::new();
        blocks.insert(
            0,
            Block {
                instructions: Vec::new(),
            },
        );
        let bytecode_cfg = bytecode_to_cfg(bytecode)?;
        let mut rv = TranslationUnit {
            blocks: blocks,
            free_rid: 0x10000,
            free_bid: 0x0,
            cfg: CFG::new(),
            start: 0,
        };
        let rpo = cfg_traverse_po(&bytecode_cfg, 0);
        let mut current_block = 0;
        let mut block_mappings = HashMap::new();
        for bid in rpo.iter() {
            current_block = rv.allocate_bid();
            block_mappings.insert(*bid, current_block);
            rv.blocks.insert(
                current_block,
                Block {
                    instructions: Vec::new(),
                },
            );
            let bc_block = match bytecode.blocks.get(bid) {
                Some(b) => b,
                None => panic!("unreachable"),
            };
            for bc_instr in bc_block.instructions.iter() {
                current_block =
                    rv.translate_instruction(bc_instr, memory, function_table, current_block)?;
            }
            rv.translate_block_exit(&bc_block.exit, current_block, &block_mappings)?;
        }
        rv.start = *block_mappings.get(&0).unwrap();
        Ok(rv)
    }
}
