#!/usr/bin/env python

import sys
import random
import struct
import subprocess
import time
import os
import errno
import ctypes
import time
import copy
import pickle
import math
import codecs
import gzip
import json
import shutil
import hashlib
from datetime import datetime
from collections import OrderedDict

import game


PTRACE_TRACEME = 0 
PTRACE_PEEKTEXT = 1 
PTRACE_PEEKDATA = 2 
PTRACE_PEEKUSER = 3 
PTRACE_POKETEXT = 4 
PTRACE_POKEDATA = 5 
PTRACE_POKEUSER = 6 
PTRACE_CONT = 7 
PTRACE_KILL = 8 
PTRACE_SINGLESTEP = 9
PTRACE_GETREGS = 12
PTRACE_SETREGS = 13
PTRACE_GETFPREGS = 14
PTRACE_SETFPREGS = 15
PTRACE_ATTACH = 16
PTRACE_DETACH = 17
PTRACE_GETFPXREGS = 18
PTRACE_SETFPXREGS = 19
PTRACE_SYSCALL = 24


PTRACE_SETOPTIONS  = 0x4200
PTRACE_GETEVENTMSG = 0x4201
PTRACE_GETSIGINFO  = 0x4202
PTRACE_SETSIGINFO  = 0x4203


PTRACE_O_TRACESYSGOOD   = 0x00000001
PTRACE_O_TRACEFORK      = 0x00000002
PTRACE_O_TRACEVFORK     = 0x00000004
PTRACE_O_TRACECLONE     = 0x00000008
PTRACE_O_TRACEEXEC      = 0x00000010
PTRACE_O_TRACEVFORKDONE = 0x00000020
PTRACE_O_TRACEEXIT      = 0x00000040
PTRACE_O_MASK           = 0x0000007f


from ctypes import *
from ctypes import get_errno, cdll 
from ctypes.util import find_library

libc = CDLL("libc.so.6", use_errno=True)
ptrace = libc.ptrace
ptrace.argtypes = [c_uint, c_uint, c_long, c_long]
ptrace.restype = c_long

class user_regs_struct(Structure):
    _fields_ = (
        ("r15", c_ulong),
        ("r14", c_ulong),
        ("r13", c_ulong),
        ("r12", c_ulong),
        ("rbp", c_ulong),
        ("rbx", c_ulong),
        ("r11", c_ulong),
        ("r10", c_ulong),
        ("r9", c_ulong),
        ("r8", c_ulong),
        ("rax", c_ulong),
        ("rcx", c_ulong),
        ("rdx", c_ulong),
        ("rsi", c_ulong),
        ("rdi", c_ulong),
        ("orig_rax", c_ulong),
        ("rip", c_ulong),
        ("cs", c_ulong),
        ("eflags", c_ulong),
        ("rsp", c_ulong),
        ("ss", c_ulong),
        ("fs_base", c_ulong),
        ("gs_base", c_ulong),
        ("ds", c_ulong),
        ("es", c_ulong),
        ("fs", c_ulong),
        ("gs", c_ulong)
    )


COMPUTING_AREA_START = 0x20000000
SECCOMP_AREA = 0x60000000
SECCOMP_SIZE = 0x1000
OUTPUT_AREA = 0x50000000
OUTPUT_SIZE = 0x10000000
ROP_AREA_START = 0x00800000
COMPUTING_HEAP_START = 0x40000000
COMPUTING_STACK_START = 0x30000000

BASEPATH = "/dev/shm/ropship/"

STATEDUMPINTERVAL = 100
COMPUTING_CHAIN_TIMEOUT = 45.0 
COMPUTING_MOVES_TIMEOUT = 0.10 
GAMENTICK = 1000 

def serialize(obj):
    if type(obj) == bytes:
        return codecs.decode(obj)
    return obj.__dict__


def run_cmd(args, timeout=None, shell=False, autoerror=False, traceme=False, wait=True):
    def pkiller():
        from ctypes import cdll
        cdll['libc.so.6'].prctl(1, 9)
        if traceme:
            ptrace(PTRACE_TRACEME, 0, 0, 0)

    pipe = subprocess.PIPE
    print(repr(args))
    ntime = time.time()
    p = subprocess.Popen(args, stdout=pipe, stderr=pipe, shell=shell, preexec_fn=pkiller)
    if not wait:
        return p

    tt = False
    try:
        stdout, stderr = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        tt = True
        p.kill()
        stdout, stderr = p.communicate()
        pass
    etime = time.time() - ntime
    rc = p.returncode
    p.wait()
    if autoerror and rc!=0:
        print("CMD:" + " ".join(fargs))
        print("STDOUT")
        print(stdout.decode('utf-8'))
        print("STDERR")
        print(stderr.decode('utf-8'))
        print("CMD: " + str(rc))

    return (stdout, stderr, rc, etime, tt)


def wait_status_to_string(status):
    def num_to_sig(num):
        sigs = ["SIGHUP", "SIGINT", "SIGQUIT", "SIGILL", "SIGTRAP", "SIGABRT", "SIGBUS", "SIGFPE", "SIGKILL", "SIGUSR1", "SIGSEGV", "SIGUSR2", "SIGPIPE", "SIGALRM", "SIGTERM", "SIGSTKFLT", "SIGCHLD", "SIGCONT", "SIGSTOP", "SIGTSTP", "SIGTTIN", "SIGTTOU", "SIGURG", "SIGXCPU", "SIGXFSZ", "SIGVTALRM", "SIGPROF", "SIGWINCH", "SIGIO", "SIGPWR", "SIGSYS"]
        if num-1 < len(sigs):
            return sigs[num-1]
        else:
            return str(num)


    ff = [os.WCOREDUMP, os.WIFSTOPPED, os.WIFSIGNALED, os.WIFEXITED, os.WIFCONTINUED]
    status_list = []
    status_list.append(str(status))
    for f in ff:
        if f(status):
            status_list.append(f.__name__)
    status_list.append(num_to_sig(os.WEXITSTATUS(status)))
    status_list.append(num_to_sig(os.WSTOPSIG(status)))
    status_list.append(num_to_sig(os.WTERMSIG(status)))
    if(os.WIFSTOPPED(status)):
        ss = (status & 0xfff00) >> 8
        ptrace_sigs = ["PTRACE_EVENT_FORK", "PTRACE_EVENT_VFORK", "PTRACE_EVENT_CLONE", "PTRACE_EVENT_EXEC", "PTRACE_EVENT_VFORK_DONE", "PTRACE_EVENT_EXIT"]
        if ss > 0 and ss-1 < len(ptrace_sigs):
            status_list.append(ptrace_sigs[ss-1])
    return "|".join(status_list)


def readn(fd, n, pos=-1):
    if pos >= 0:
        os.lseek(fd, pos, 0) 
    buf = b""
    e = n
    while e > 0:
        tbuf = os.read(fd, e)
        if len(tbuf) == 0:
            raise Exception("short read %d vs. %d" % (len(tbuf), n))
        buf += tbuf
        e -= len(tbuf)
    return buf

def writen(fd, buf, pos=-1):
    if pos >= 0:
        os.lseek(fd, pos, 0) 
    e = len(buf)
    while True:
        nw = os.write(fd, buf)
        buf = buf[nw:]
        if buf == b"":
            break

def get_moves(state, processes):
    defcon_id_to_team = {team.defcon_id: team for tid, team in state.teams.items()}
    defcon_id_to_tid = {team.defcon_id: team.tid for tid, team in state.teams.items()}
    shuffled_processes = sorted(processes.values(), key=lambda k: random.random())

    tpid = -1 
    tpid = processes[6].pid 

    for defcon_id, p in processes.items():
        pid = p.pid
        try:
            fd = os.open("/proc/%d/mem" % pid, os.O_RDWR)
            writen(fd, b"n".ljust(8, b"\x00"), COMPUTING_HEAP_START)
            writen(fd, struct.pack("<Q", state.tick), COMPUTING_HEAP_START+8)
            writen(fd, struct.pack("<Q", defcon_id_to_team[defcon_id].tid), COMPUTING_HEAP_START+16)
            for i in range(len(state.teams)):
                team = state.teams[i]
                values = []
                values.append(team.tid)
                values.append(team.defcon_id)
                values.append(int(team.score))
                values.append(int(team.shield))
                if team.ship != None:
                    values.append(1)
                    values.append(int(team.ship.location.x))
                    values.append(int(team.ship.location.y))
                    values.append(int(team.ship.location.a/math.pi*180.0))
                    values.append(int(team.ship.fspeed * 0x100))
                    values.append(int(team.ship.aspeed * 0x100))
                else:
                    values.extend([0,0xffff,0xffff,0xffff,0xffff,0xffff])
                writen(fd, struct.pack("<"+"q"*len(values), *values), COMPUTING_HEAP_START+0x100+i*0x100)
            writen(fd, b"\x00"*(5*16*0x30), COMPUTING_HEAP_START+0x2000)
            j = 0
            for i in range(len(state.teams)):
                team = state.teams[i]
                for bullet in team.bullets:
                    values = []
                    values.append(1)
                    values.append(team.tid)
                    values.append(int(bullet.location.x))
                    values.append(int(bullet.location.y))
                    values.append(int(bullet.location.a/math.pi*180.0))
                    writen(fd, struct.pack("<"+"q"*len(values), *values), COMPUTING_HEAP_START+0x2000+j*0x30)
                    j+=1
            os.close(fd)
        except OSError as e:
            print("+++", "Exception setting process", type(e), pid)
            pass

    for p in shuffled_processes: 
        pid = p.pid

        regs = user_regs_struct()
        res = ptrace(PTRACE_GETREGS, pid, 0, ctypes.addressof(regs))


        regs.rip = ROP_AREA_START
        regs.rsp = COMPUTING_STACK_START
        regs.rax = 0x0
        regs.rbx = 0x0
        regs.rcx = 0x0
        regs.rdx = 0x0
        regs.rsi = 0x0
        regs.rdi = 0x0
        regs.rbp = 0x0
        regs.rax = 0x0
        regs.r8 = 0x0
        regs.r9 = 0x0
        regs.r10 = 0x0
        regs.r11 = 0x0
        regs.r12 = 0x0
        regs.r13 = 0x0
        regs.r14 = 0x0
        regs.r15 = 0x0
        regs.eflags = 0x0

        ptrace(PTRACE_SETREGS, pid, 0, ctypes.addressof(regs))
        ptrace(PTRACE_CONT, pid, 0, 0)

    time.sleep(COMPUTING_MOVES_TIMEOUT)

    for p in shuffled_processes:
        try:
            p.send_signal(19) 
        except OSError as e:
            print("+++", "Exception stopping process", type(e), pid)
            pass
        
        
    for defcon_id, p in processes.items(): 
        pid = p.pid
        try:
            pid, status = os.waitpid(pid, 0)
            while status != 4991: 
                print("***", defcon_id, pid, wait_status_to_string(status))
                ptrace(PTRACE_CONT, pid, 0, 0)
                pid, status = os.waitpid(pid, 0)
        except OSError as e:
            print("+++", "Exception waiting process", type(e), pid)
            pass
            
            

    moves = {}
    for defcon_id, p in processes.items():
        pid = p.pid
        try:
            fd = os.open("/proc/%d/mem" % pid, os.O_RDWR)
            move_str = readn(fd, 8, COMPUTING_HEAP_START)
            move_int = move_str[0]
            if move_int not in map(ord, [b"n", b"u", b"l", b"r", b"d", b"s", b"a"]):
                move = b"n"
            else:
                move = bytes((move_int,))
            os.close(fd)
        except OSError as e:
            print("+++", "Exception getting move for process", type(e), pid)
            move = b"n"
        moves[defcon_id_to_tid[defcon_id]] = move

    print(state.tick, {state.teams[tid].defcon_id: "%c"%ord(v) for tid,v in moves.items()})
    return moves


def dump_states(states):
    print("="*3, datetime.now(), "dumping states")
    gzip.compress(json.dumps(states, default=serialize,separators=(',', ':')).encode("utf-8"))
    with open(os.path.join(BASEPATH, "states_tmp"), "wb") as fp:
        fp.write(gzip.compress(json.dumps(states, default=serialize,separators=(',', ':')).encode("utf-8")))
    shutil.move(os.path.join(BASEPATH, "states_tmp"), os.path.join(BASEPATH, "states"))


def get_file_hash(fname):
    content = b""
    try:
        with open(fname, "rb") as fp:
            content = fp.read() 
    except IOError:
        content = b""
    return hashlib.sha256(content).hexdigest()


def main(defconround, teams):
    seed = random.randint(0, pow(2,64)-1)
    print("=== seed:", seed)
    rnd_size = 500 * 1000000
    rnd_path = os.path.join(BASEPATH,"rnd.bin")
    input_path = os.path.join(BASEPATH,"inputs/")
    chain_path = os.path.join(BASEPATH,"chains/")
    run_cmd(["./rnd_generator", str(seed), str(rnd_size), rnd_path])
    
    processes = OrderedDict()
    solution_hash_dict = {}
    for defcon_id in teams.keys():
        fname = os.path.join(input_path, "team%d"%defcon_id) 
        solution_hash_dict[defcon_id] = get_file_hash(fname)
        p = run_cmd(["./stub_process", rnd_path, fname], traceme=True, wait=False)
        processes[defcon_id] = p
        print(p)

    for p in processes.values(): 
        pid = p.pid
        pid, status = os.waitpid(pid, 0)
        print(pid, wait_status_to_string(status))
        ptrace(PTRACE_CONT, pid, 0, 0)

    for p in processes.values(): 
        pid = p.pid
        pid, status = os.waitpid(pid, 0)
        print(pid, wait_status_to_string(status))

        regs = user_regs_struct()
        res = ptrace(PTRACE_GETREGS, pid, 0, ctypes.addressof(regs))
        
        

        regs.rip = COMPUTING_AREA_START
        ptrace(PTRACE_SETREGS, pid, 0, ctypes.addressof(regs))

        fd = os.open("/proc/%d/mem" % pid, os.O_RDWR)
        writen(fd, b"\xcc"*SECCOMP_SIZE, SECCOMP_AREA)
        os.close(fd)

        res = ptrace(PTRACE_CONT, pid, 0, 0)

    time.sleep(COMPUTING_CHAIN_TIMEOUT)

    for p in processes.values():
        p.send_signal(19) 

    for defcon_id, p in processes.items():
        pid = p.pid
        pid, status = os.waitpid(pid, 0)
        print(pid, wait_status_to_string(status))
        try:
            fd = os.open("/proc/%d/mem" % pid, os.O_RDWR)
            cc = readn(fd, OUTPUT_SIZE, OUTPUT_AREA)
            os.close(fd)
            p.kill()
        except OSError as e:
            print("+++", "Getting chain for proces", type(e), pid)
            cc = b""
        p.wait() 
        with open(os.path.join(BASEPATH,"chains/team%d.chain"%defcon_id), "wb") as out_fd:
            out_fd.write(cc)


    print("="*5, datetime.now(), "start rop chains")
    processes = OrderedDict()
    for defcon_id in teams.keys():
        p = run_cmd(["./stub_ropping", rnd_path, os.path.join(chain_path, "team%d.chain"%defcon_id)], traceme=True, wait=False)
        processes[defcon_id] = p
        print(p)

    for p in processes.values(): 
        pid = p.pid
        pid, status = os.waitpid(pid, 0)
        print(pid, wait_status_to_string(status))
        ptrace(PTRACE_CONT, pid, 0, 0)

    for p in processes.values(): 
        pid = p.pid
        pid, status = os.waitpid(pid, 0)
        print(pid, wait_status_to_string(status))

        fd = os.open("/proc/%d/mem" % pid, os.O_RDWR)
        writen(fd, b"\xcc"*SECCOMP_SIZE, SECCOMP_AREA)
        os.close(fd)


    states = []
    state = game.init(teams, defconround, seed)
    for tid, team in state.teams.items():
        team.solution_hash = solution_hash_dict[team.defcon_id]

    print("=", state.tick)
    states.append(copy.deepcopy(state))
    while True:
        moves = get_moves(state, processes)
        
        state = game.next_state(state, moves)
        states.append(copy.deepcopy(state))

        if state.tick >= GAMENTICK-1:
            dump_states(states)
            break

        if (len(states) % STATEDUMPINTERVAL) == 0:
            dump_states(states)

    for p in processes.values():
        try:
            p.kill()
        except OSError as e:
            print("+++", "Exception killing process", type(e), pid)
        p.wait() 


def decode_dict(tstr):
    d = {}
    for kv in tstr.split(b"_"):
        k, v = kv.split(b"-")
        d[int(k)] = codecs.decode(codecs.decode(v, "hex"))
    return d


def encode_dict(d):
    assert all((type(k)==int and type(v)==str for k, v in d.items()))
    return b"_".join((codecs.encode(str(k))+b"-"+codecs.encode(codecs.encode(v), "hex") for k, v in d.items()))


if __name__ == "__main__":
    cdll['libc.so.6'].prctl(1, 9)

    defconround = int(sys.argv[1])
    teams = decode_dict(sys.argv[2].encode(sys.getfilesystemencoding(), 'surrogateescape'))


    print("="*10, "START", defconround, datetime.now())
    main(defconround, teams)
    print("="*10, "END", defconround, datetime.now())

