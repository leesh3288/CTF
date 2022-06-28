use std::collections::{HashMap, HashSet};

pub type CFG = HashMap<usize, HashSet<usize>>;

fn cfg_traverse_po_rec(cfg: &CFG, current: usize, visited: &mut Vec<usize>) -> Vec<usize> {
    let mut order = Vec::new();
    visited.push(current);
    if cfg.contains_key(&current) {
        for next in cfg[&current].iter() {
            if !visited.contains(next) {
                order.extend(cfg_traverse_po_rec(cfg, *next, visited));
            }
        }
    }
    order.push(current);
    order
}

pub fn cfg_traverse_po(cfg: &CFG, start: usize) -> Vec<usize> {
    let mut visited = Vec::new();
    let mut po = cfg_traverse_po_rec(cfg, start, &mut visited);
    po
}
