use crate::error::Error;

use core::fmt;
use std::collections::{HashMap, HashSet};

fn u16(bytes: &[u8]) -> u16 {
    let mut rv: u16 = 0;
    for i in 0..2 {
        rv += (bytes[i] as u16) * (1 << (i * 8));
    }
    rv
}

fn u32(bytes: &[u8]) -> u32 {
    let mut rv: u32 = 0;
    for i in 0..4 {
        rv += (bytes[i] as u32) * (1 << (i * 8));
    }
    rv
}

#[derive(Clone, Debug)]
pub enum Instruction {
    LoadImm {
        dst_reg: u16,
        imm: i32,
    },
    LoadMem {
        dst_reg: u16,
        base_reg: u16,
        offset_imm: i32,
    },
    StoreMem {
        src_reg: u16,
        base_reg: u16,
        offset_imm: i32,
    },
    Add {
        dst_reg: u16,
        src_reg: u16,
    },
    Sub {
        dst_reg: u16,
        src_reg: u16,
    },
    Call {
        fid: i32,
    },
}

pub enum BlockExit {
    Jmp {
        bid: usize,
    },
    Jez {
        cond_reg: u16,
        bid_isz: usize,
        bid_isnz: usize,
    },
    Return,
}

pub struct Block {
    pub instructions: Vec<Instruction>,
    pub exit: BlockExit,
}

pub struct TranslationUnit {
    pub blocks: HashMap<usize, Block>,
}

impl fmt::Display for Instruction {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Instruction::LoadImm { dst_reg, imm } => write!(f, "mov r{}, {:#x}", dst_reg, imm),
            Instruction::LoadMem {
                dst_reg,
                base_reg,
                offset_imm,
            } => write!(f, "mov r{}, [r{} + {:#x}]", dst_reg, base_reg, offset_imm),
            Instruction::StoreMem {
                src_reg,
                base_reg,
                offset_imm,
            } => write!(f, "mov [r{} + {:#x}], r{}", base_reg, offset_imm, src_reg),
            Instruction::Add { dst_reg, src_reg } => write!(f, "add r{}, r{}", dst_reg, src_reg),
            Instruction::Sub { dst_reg, src_reg } => write!(f, "sub r{}, r{}", dst_reg, src_reg),
            Instruction::Call { fid } => write!(f, "call f{}", fid),
            _ => panic!("unreachable"),
        }
    }
}

impl fmt::Display for BlockExit {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            BlockExit::Jmp { bid } => write!(f, "jmp b{}", bid),
            BlockExit::Jez {
                cond_reg,
                bid_isz,
                bid_isnz,
            } => write!(f, "jez r{}, b{}, b{}", cond_reg, bid_isz, bid_isnz),
            BlockExit::Return => write!(f, "ret"),
        }
    }
}

impl fmt::Display for Block {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        for instr in self.instructions.iter() {
            writeln!(f, "{}", instr)?;
        }
        writeln!(f, "{}", self.exit)?;
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

impl TranslationUnit {
    fn analyze_block_ranges(bytes: &[u8]) -> Result<Vec<(usize, usize)>, Error> {
        let mut offset = 0;
        let mut boundaries = HashSet::new();
        boundaries.insert(0);
        boundaries.insert(bytes.len());
        while offset < bytes.len() && offset + 7 <= bytes.len() {
            let instr = &bytes[offset..offset + 7];
            match instr[0] {
                0 | 1 | 2 | 3 | 4 | 5 | 6 => {
                    offset += 7;
                    continue;
                }
                7 | 8 => {
                    let imm = u32(&instr[3..7]) as i32;
                    let target = offset as i32 + 7 + imm;
                    if target % 7 != 0 || target < 0 || target as usize >= bytes.len() {
                        return Err(Error::InvalidJumpTargetError);
                    }
                    boundaries.insert(target as usize);
                    boundaries.insert(offset + 7);
                    offset += 7;
                }
                _ => {
                    return Err(Error::InvalidOpcodeError);
                }
            }
        }
        let mut boundaries_vec: Vec<usize> = boundaries.into_iter().collect();
        let mut block_ranges = Vec::new();
        boundaries_vec.sort();
        for i in 0..boundaries_vec.len() - 1 {
            block_ranges.push((boundaries_vec[i], boundaries_vec[i + 1]));
        }
        Ok(block_ranges)
    }

    fn analyze_instructions(
        bytes: &[u8],
        begin: usize,
        end: usize,
    ) -> Result<Vec<Instruction>, Error> {
        let mut offset = begin;
        let mut instructions = Vec::new();
        while offset < end && offset + 7 <= end {
            let instr_bytes = &bytes[offset..offset + 7];
            let instr = match instr_bytes[0] {
                0 => Instruction::LoadImm {
                    dst_reg: u16(&instr_bytes[1..3]),
                    imm: u32(&instr_bytes[3..7]) as i32,
                },
                1 => Instruction::LoadMem {
                    dst_reg: u16(&instr_bytes[1..3]),
                    base_reg: u16(&instr_bytes[3..5]),
                    offset_imm: u16(&instr_bytes[5..7]) as i32,
                },
                2 => Instruction::StoreMem {
                    src_reg: u16(&instr_bytes[1..3]),
                    base_reg: u16(&instr_bytes[3..5]),
                    offset_imm: u16(&instr_bytes[5..7]) as i32,
                },
                3 => Instruction::Add {
                    src_reg: u16(&instr_bytes[1..3]),
                    dst_reg: u16(&instr_bytes[3..5]),
                },
                4 => Instruction::Sub {
                    src_reg: u16(&instr_bytes[1..3]),
                    dst_reg: u16(&instr_bytes[3..5]),
                },
                7 | 8 => {
                    offset += 7;
                    continue;
                }
                9 => Instruction::Call {
                    fid: u32(&instr_bytes[3..7]) as i32,
                },
                _ => {
                    return Err(Error::InvalidOpcodeError);
                }
            };
            instructions.push(instr);
            offset += 7;
        }
        Ok(instructions)
    }

    fn analyze_block_exit(
        bytes: &[u8],
        begin: usize,
        end: usize,
        bid: usize,
        block_ranges: &Vec<(usize, usize)>,
    ) -> Result<BlockExit, Error> {
        if end < 7 {
            return Ok(BlockExit::Return);
        }
        let instr = &bytes[end - 7..end];
        match instr[0] {
            7 => {
                let imm = u32(&instr[3..7]) as i32;
                let target = end as i32 + imm;
                let bid = match block_ranges.iter().position(|(s, e)| *s == target as usize) {
                    Some(v) => v,
                    None => panic!("unreachable"),
                };
                Ok(BlockExit::Jmp { bid: bid })
            }
            8 => {
                let imm = u32(&instr[3..7]) as i32;
                let target_z = end as i32 + imm;
                let target_nz = end as i32;
                let bid_z = match block_ranges
                    .iter()
                    .position(|(s, e)| *s == target_z as usize)
                {
                    Some(v) => v,
                    None => panic!("unreachable"),
                };
                let bid_nz = match block_ranges
                    .iter()
                    .position(|(s, e)| *s == target_nz as usize)
                {
                    Some(v) => v,
                    None => panic!("unreachable"),
                };
                Ok(BlockExit::Jez {
                    cond_reg: u16(&instr[1..3]),
                    bid_isz: bid_z,
                    bid_isnz: bid_nz,
                })
            }
            _ => {
                if end == bytes.len() {
                    Ok(BlockExit::Return)
                } else {
                    Ok(BlockExit::Jmp { bid: bid + 1 })
                }
            }
        }
    }

    pub fn new(bytes: &[u8]) -> Result<Self, Error> {
        let block_ranges = TranslationUnit::analyze_block_ranges(bytes)?;
        let mut blocks = HashMap::new();
        let mut bid = 0;
        for (begin, end) in block_ranges.iter() {
            let instrs = TranslationUnit::analyze_instructions(bytes, *begin, *end)?;
            let exit =
                TranslationUnit::analyze_block_exit(bytes, *begin, *end, bid, &block_ranges)?;
            let block = Block {
                instructions: instrs,
                exit: exit,
            };
            blocks.insert(bid, block);
            bid += 1;
        }
        Ok(Self { blocks: blocks })
    }

    pub fn blocks_cnt(&self) -> usize {
        self.blocks.len()
    }
}
