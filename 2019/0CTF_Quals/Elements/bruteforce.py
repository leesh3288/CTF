#!/usr/bin/python3.6

import subprocess
from multiprocessing.dummy import Pool as ThreadPool

d = [0x391BC2164F0A, 0x4064e4798768, 0x56e0de138176]

DELTARANGE = 0x100

def run(d1):
    print("solving d1 = {:x}".format(d1))
    for d2 in range(-DELTARANGE, DELTARANGE + 1):
        payload = "flag{" + "{:012x}-{:012x}-{:012x}".format(d[0], d[1] + d1, d[2] + d2) + "}\n"
        try:
            s = subprocess.check_output("./Elements", input=bytes(payload, 'ascii'))
            if len(s) != 0:
                print(payload)
                return payload
        except subprocess.CalledProcessError as e:
            pass
    return ""

pool = ThreadPool(8)
results = pool.map(run, list(range(-DELTARANGE, DELTARANGE + 1)))
pool.close()
pool.join()
print(''.join(results))