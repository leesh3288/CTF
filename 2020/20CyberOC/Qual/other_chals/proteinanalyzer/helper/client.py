import socket
import base64
import sys 

def recvall(s):
    s.settimeout(5)
    ret = ''
    while True:
        c = s.recv(4096)
        if c == '':
            break
        else:
            ret += c
    s.settimeout(None)
    return ret

def recvuntil(s, e):
    ret = ''
    while True:
        c = s.recv(1)
        if c == e:
            break
        else:
            ret += c
    return ret + c

def readline(s):
    return recvuntil(s, '\n')
    
IP = "127.0.0.1"
PORT = 13100

if len(sys.argv) != 3:
    print("usage : %s <file-name> <report-name>" % sys.argv[0])
    exit(1)

with open(sys.argv[1], "r") as f:
    data = base64.b64encode(f.read())


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((IP, PORT))

# send file length
recvuntil(s, ":")
s.send(str(len(data)) + '\n')

# send file content
recvuntil(s, ":")
s.send(data)

# get file name
file_name = readline(s).split()[5].strip()

report = ""
report += recvuntil(s, ":")

s.send(file_name + "\n")
report += file_name + "\n"

report += recvall(s)

with open(sys.argv[2], "w") as f:
    f.write(report)
