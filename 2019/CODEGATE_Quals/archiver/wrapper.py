import os
import sys
import md5
import random
import string
import subprocess
import signal
from struct import *

def rand_string(size=40):
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in xrange(size))

filename = "/tmp/dummy_" + rand_string()

def handler(signum, frame):
    delete()
    sys.exit(1)
    return

def delete():
    try:
        os.remove(filename)
    except:
        pass
    return

signal.signal(signal.SIGALRM, handler)
signal.alarm(10)

os.chdir("/home/archiver/")

FNULL = open(os.devnull, "rb")

size = unpack("<I", sys.stdin.read(4))[0]
if 4096 < size:
    print "Too big, Sorry!"
    sys.exit(1)

data = sys.stdin.read(size)
f = open(filename, "wb")
f.write(data)
f.close()

p = subprocess.Popen(["./archiver", filename], stdin=FNULL, stdout=subprocess.PIPE)
print(p.stdout.read())
delete()