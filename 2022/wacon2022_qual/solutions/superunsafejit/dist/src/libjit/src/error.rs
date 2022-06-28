use core::fmt;

#[derive(Clone, Debug)]
pub enum Error {
    InvalidOpcodeError,
    InvalidJumpTargetError,
    OOMError,
    FunctionNotFoundError,
    OutOfRegistersError,
    AssemblerError,
    UnreachableError,
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            InvalidOpcodeError => {
                write!(f, "{}", "InvalidOpcodeError")
            }
            InvalidJumpTargetError => {
                write!(f, "{}", "InvalidJumpTargetError")
            }
            OOMError => {
                write!(f, "{}", "OOMError")
            }
            FunctionNotFoundError => {
                write!(f, "{}", "FunctionNotFoundError")
            }
            OutOfRegistersError => {
                write!(f, "{}", "OutoOfRegistersError")
            }
            AssemblerError => {
                write!(f, "{}", "AssemblerError")
            }
        }
    }
}
