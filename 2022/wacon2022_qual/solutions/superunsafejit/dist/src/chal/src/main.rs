extern crate libjit;

use libjit::{memory, bytecode, vasm, asm, ice_wrapper, error::Error};
use std::process::exit;
use std::io::{self, BufRead, Write};
use std::collections::{HashMap, BTreeMap};

fn init_data_memory(mem_size: usize) -> Result<memory::Memory, Error> {
    memory::page_allocate(mem_size, false)
}

fn pg_round_up(length: usize) -> usize {
    (length & 0xFFFFFFFFFFFFF000) + 0x1000
}

fn read_int() -> i64 {
    let mut buffer = String::new();
    let stdin = io::stdin();
    let mut handle = stdin.lock();
    print!(">> ");
    io::stdout().flush().unwrap();
    match handle.read_line(&mut buffer) {
        Err(e) => panic!("unreachable"),
        Ok(o) => {},
    };
    if buffer.ends_with("\n") {
        buffer.pop();
    }
    match buffer.parse::<i64>() {
        Ok(o) => o,
        Err(e) => {
            println!("[!] Error: {}", e.to_string());
            println!("[-] Not a valid integer");
            exit(-1);
        }
    }
}

fn read_bytes() -> Vec<u8> {
    let mut buffer = String::new();
    let stdin = io::stdin();
    let mut handle = stdin.lock();
    print!(">> ");
    io::stdout().flush().unwrap();
    match handle.read_line(&mut buffer) {
        Err(e) => panic!("unreachable"),
        Ok(o) => {},
    };
    if buffer.ends_with("\n") {
        buffer.pop();
    }
    match hex::decode(&buffer) {
        Ok(o) => o,
        Err(e) => {
            println!("[!] Error: {}", e.to_string());
            println!("[-] Failed to read hex string");
            exit(-1);
        }
    }
}

fn compile(bytecode: &[u8], data_memory: &memory::Memory) -> Result<*const (), Error> {
    let mut function_table = HashMap::new();
    function_table.insert("deoptimize".to_string(), 0xdeadbeef);
    let pl1 = bytecode::TranslationUnit::new(bytecode)?;
    let pl2 = vasm::TranslationUnit::new(&pl1, &data_memory, &function_table)?;
    let pl3 = asm::TranslationUnit::new(&pl2)?;
    let pl41 = ice_wrapper::assemble(&pl3, 0x0)?;
    let code_mem = memory::page_allocate(pg_round_up(pl41.len()), true)?;
    let pl42 = ice_wrapper::assemble(&pl3, code_mem.pointer as u64)?;
    unsafe {
        std::ptr::copy(pl42.as_ptr(), code_mem.pointer, pl42.len());
        Ok(code_mem.pointer as *const ())
    }
}

fn call(func: *const()) {
    let return_value = unsafe {
        let foo: extern "C" fn() -> u64 = unsafe { std::mem::transmute(func) };
        (foo)()
    };
    println!("[*] Return value = {}", return_value);
}

fn print_menu() {
    println!("[1] Add function");
    println!("[2] Call function");
    println!("[3] Exit");
}

fn main() {
    let data_mem = match init_data_memory(0x100000) {
        Ok(m) => m,
        Err(e) => {
            println!("[!] Error: {}", e);
            println!("[-] Failed to initialize data memory");
            exit(-1);
        }
    };
    let mut funcs = BTreeMap::new();
    let mut func_id = 0;
    loop {
        print_menu();
        match read_int() {
            1 => {
                println!("Give me function bytecode, in hex");
                let bc = read_bytes();
                let func = match compile(&bc, &data_mem) {
                    Ok(f) => f,
                    Err(e) => {
                        println!("[!] Error: {}", e);
                        println!("[-] Failed to JIT compile bytecode");
                        exit(-1);
                    }
                };
                funcs.insert(func_id, func);
                func_id += 1;
            },
            2 => {
                if funcs.len() > 0 {
                    println!("Select ID of function to call ({}~{})", 0, funcs.len()-1);
                    let func_id = read_int();
                    let func = match funcs.get(&func_id) {
                        Some(f) => f.clone(),
                        None => {
                            println!("[!] Funtion w/ ID {} does not exist", func_id);
                            continue;
                        }
                    };
                    call(func);
                }
                else {
                    println!("[-] There are no functions compiled yet!");
                }
            },
            3 => {
                println!("[*] Thank you for using our service");
                exit(0);
            },
            _ => {
                println!("[-] Not a valid option");
                exit(-1);
            }
        } 

    }
}
