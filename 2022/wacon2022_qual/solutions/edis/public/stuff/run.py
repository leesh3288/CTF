#!/usr/bin/env python3
import redis
import subprocess
import socket
import psutil
import atexit
import signal
import time

def findFreePort():
	s = socket.socket()
	s.bind(('', 0))
	p = s.getsockname()[1]
	s.close()
	return p

def cleanUp(a,b):
	parent = psutil.Process(p.pid)
	for child in parent.children(recursive=True):
		child.kill()
	parent.kill()
	exit(0)

redisPort = findFreePort()
p = subprocess.Popen(['./run-redis.sh',str(redisPort)])

atexit.register(cleanUp,None,None)
signal.signal(signal.SIGALRM,cleanUp)
signal.alarm(60)

print('Welcome to edis!')
time.sleep(1)
r = redis.Redis(host='localhost',port=redisPort)
while(1):
	s = input('> ')
	assert(s.split(' ')[0].lower() in ['get','set','b64decode'])
	print(r.execute_command(s))
