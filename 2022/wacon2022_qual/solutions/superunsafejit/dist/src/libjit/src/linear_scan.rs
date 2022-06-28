use crate::asm;
use crate::cfg::*;
use crate::error::Error;
use crate::vasm;

use std::collections::{HashMap, HashSet};

pub type AllocationTable = HashMap<usize, asm::Register>;
type LiveRange = HashMap<usize, (usize, usize)>;
type LiveRids = HashMap<usize, HashSet<usize>>;

struct UseDef {
    uses: HashSet<usize>,
    defs: HashSet<usize>,
}

pub struct LinearScan {
    pub allocation_table: AllocationTable,
}

fn instruction_use_defs(instr: &vasm::Instruction) -> UseDef {
    let mut uses = HashSet::new();
    let mut defs = HashSet::new();
    match instr {
        vasm::Instruction::Mov { dst, src }
        | vasm::Instruction::Add { dst, src }
        | vasm::Instruction::Sub { dst, src }
        | vasm::Instruction::Cmp { dst, src } => {
            match dst {
                vasm::Register::Virtual(rid) => {
                    defs.insert(*rid);
                    uses.insert(*rid);
                }
                _ => {}
            }
            match src {
                vasm::Register::Virtual(rid) => {
                    uses.insert(*rid);
                }
                _ => {}
            }
        }
        vasm::Instruction::MovImm { dst, imm } => match dst {
            vasm::Register::Virtual(rid) => {
                defs.insert(*rid);
            }
            _ => {}
        },
        vasm::Instruction::Load { dst, addr } => {
            match dst {
                vasm::Register::Virtual(rid) => {
                    defs.insert(*rid);
                }
                _ => {}
            };
            match addr {
                vasm::Register::Virtual(rid) => {
                    uses.insert(*rid);
                }
                _ => {}
            };
        }
        vasm::Instruction::Store { src, addr } => {
            match src {
                vasm::Register::Virtual(rid) => {
                    uses.insert(*rid);
                }
                _ => {}
            };
            match addr {
                vasm::Register::Virtual(rid) => {
                    uses.insert(*rid);
                }
                _ => {}
            };
        }
        vasm::Instruction::Call { target } => match target {
            vasm::Register::Virtual(rid) => {
                uses.insert(*rid);
            }
            _ => {}
        },
        _ => {}
    };
    UseDef {
        uses: uses,
        defs: defs,
    }
}

fn block_use_defs(block: &vasm::Block) -> UseDef {
    let mut uses = HashSet::new();
    let mut defs = HashSet::new();
    for instr in block.instructions.iter() {
        let usedef = instruction_use_defs(instr);
        for x in usedef.uses.iter() {
            uses.insert(*x);
        }
        for x in usedef.defs.iter() {
            defs.insert(*x);
        }
    }
    UseDef {
        uses: uses,
        defs: defs,
    }
}

impl LinearScan {
    pub fn lookup(&self, vreg: &vasm::Register) -> asm::Register {
        match vreg {
            vasm::Register::Virtual(rid) => match self.allocation_table.get(rid) {
                Some(r) => r.clone(),
                None => asm::Register::Rax,
            },
            vasm::Register::Rax => asm::Register::Rax,
            _ => panic!("unreachable"),
        }
    }

    pub fn new(source: &vasm::TranslationUnit) -> Result<Self, Error> {
        let cfg = &source.cfg;
        let mut live_in = LiveRids::new();
        let mut live_out = LiveRids::new();
        for (bid, _succ) in cfg.iter() {
            live_in.insert(*bid, HashSet::new());
            live_out.insert(*bid, HashSet::new());
        }
        loop {
            let mut prev_live_in = LiveRids::new();
            let mut prev_live_out = LiveRids::new();
            for (bid, block) in source.blocks.iter() {
                let usedef = block_use_defs(block);
                prev_live_in.insert(*bid, live_in.get(bid).unwrap().clone());
                prev_live_out.insert(*bid, live_out.get(bid).unwrap().clone());
                let mut live_out_new = HashSet::new();
                let mut live_in_new = HashSet::new();
                for succ in cfg.get(bid).unwrap().iter() {
                    for x in live_in.get(succ).unwrap().iter() {
                        live_out_new.insert(*x);
                    }
                }
                for x in usedef.uses.iter() {
                    live_in_new.insert(*x);
                }
                for x in live_out_new.iter() {
                    if !usedef.defs.contains(x) {
                        live_in_new.insert(*x);
                    }
                }
                live_out.insert(*bid, live_out_new);
                live_in.insert(*bid, live_in_new);
            }
            if prev_live_in == live_in && prev_live_out == live_out {
                break;
            }
        }
        let po = cfg_traverse_po(&cfg, source.start);
        let mut vregs = HashSet::new();
        let mut live_interval = HashMap::new();
        let mut live_range = LiveRange::new();
        for bid in po.iter() {
            for rid in live_in.get(bid).unwrap().iter() {
                vregs.insert(*rid);
            }
            for rid in live_out.get(bid).unwrap().iter() {
                vregs.insert(*rid);
            }
        }
        for bid in po.iter() {
            for vreg in vregs.iter() {
                if live_in.get(bid).unwrap().contains(vreg)
                    || live_out.get(bid).unwrap().contains(vreg)
                {
                    live_interval
                        .entry(*vreg)
                        .or_insert_with(HashSet::new)
                        .insert(*bid);
                }
            }
        }
        for (rid, interval) in live_interval.iter() {
            let start = interval
                .iter()
                .min_by(|a, b| a.partial_cmp(b).unwrap())
                .unwrap();
            let end = interval
                .iter()
                .max_by(|a, b| a.partial_cmp(b).unwrap())
                .unwrap();
            live_range.insert(*rid, (*start, *end));
        }

        let mut ordered_live_range = Vec::new();
        for (rid, (start, end)) in live_range.iter() {
            ordered_live_range.push((*rid, *start, *end));
        }
        ordered_live_range.sort_by(|(r1, s1, e1), (r2, s2, e2)| s1.partial_cmp(s2).unwrap());
        let mut active = Vec::new();
        let mut arch_regs = vec![
            asm::Register::Rax,
            asm::Register::Rbx,
            asm::Register::Rcx,
            asm::Register::Rdx,
            asm::Register::Rdi,
            asm::Register::Rsi,
            asm::Register::R8,
            asm::Register::R9,
            asm::Register::R10,
            asm::Register::R11,
            asm::Register::R12,
            asm::Register::R13,
            asm::Register::R14,
            asm::Register::R15,
        ];
        let mut allocation_table = HashMap::new();
        for (rid, start, end) in ordered_live_range.iter() {
            active.retain(|&(r, s, e)| e >= *start);
            if active.len() == arch_regs.len() {
                return Err(Error::OutOfRegistersError);
            }
            let mut avail = arch_regs.clone();
            for (r, _s, _e) in active.iter() {
                avail.retain(|x| x != allocation_table.get(r).unwrap());
            }
            let arch_reg = avail.pop().unwrap();
            allocation_table.insert(*rid, arch_reg);
            active.push((*rid, *start, *end));
        }
        Ok(Self {
            allocation_table: allocation_table,
        })
    }
}
