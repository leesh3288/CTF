#!/usr/bin/python3

import tempfile
import sys,os
import signal
import base64
import subprocess

def _print(content):
	print(content,  end = "")
	sys.stdout.flush()

if __name__ == "__main__":
	signal.alarm(60)
	try:
		_print("length of base64 encoded file : ")
		size = int(sys.stdin.readline())
		if size > 0x1000000:
			print("size is too big!")
			exit(-1)
		_print("file content : ")
		pay = sys.stdin.read(size)
		f = tempfile.NamedTemporaryFile(prefix='',suffix='.pdb', delete=False)
		f.write(base64.b64decode(pay))
		f.close()

		_print("your file is uploaded in %s\n" % f.name)

		subprocess.run(["./protein"], stderr=sys.stdout.buffer)
		os.unlink(f.name)
	except :
		_print("error occured\n")