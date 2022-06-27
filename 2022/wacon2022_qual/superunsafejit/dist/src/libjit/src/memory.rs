use crate::error::Error;

extern crate libc;

pub struct Memory {
    pub pointer: *mut u8,
    pub length: usize,
    pub executable: bool,
}

pub fn page_allocate(length: usize, executable: bool) -> Result<Memory, Error> {
    let pointer = unsafe {
        libc::mmap(
            0 as *mut libc::c_void,
            length,
            libc::PROT_READ | libc::PROT_WRITE | if executable { libc::PROT_EXEC } else { 0 },
            libc::MAP_ANON | libc::MAP_PRIVATE,
            -1,
            0,
        )
    } as *mut u8;
    if pointer != 0 as *mut u8 {
        Ok(Memory {
            pointer: pointer,
            length: length,
            executable: executable,
        })
    } else {
        Err(Error::OOMError)
    }
}

pub fn page_free(pointer: *const u8, length: usize) {
    unsafe {
        libc::munmap(0 as *mut libc::c_void, length);
    }
}
