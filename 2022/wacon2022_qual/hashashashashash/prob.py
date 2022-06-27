#!/usr/bin/python3
import hashlib
import signal
import string

def leading_zero(s):
    cnt = 0
    while cnt < len(s) and s[cnt] == '0':
        cnt += 1
    return cnt

def is_strong_phrase(s):
    if len(s) < 16: return False
    if len(set(string.ascii_lowercase) & set(s)) < 3: return False
    if len(set(string.ascii_uppercase) & set(s)) < 3: return False
    if len(set(string.digits) & set(s)) < 3: return False
    if len(set(string.punctuation) & set(s)) < 3: return False
    for i in range(len(s)):
        if abs(ord(s[i]) - ord(s[i-1])) < 5:
            return False
    return True

signal.alarm(60)

FLAG = open("flag.txt", 'rb').read()
SALT = '1q2w3e4r!'
target = 16**12

phrase = input("Select a STRONG phrase(Don't think too much! I just don't want you struggle with a connection lost) > ")
if not is_strong_phrase(phrase):
  print("bye..")
  exit(-1)

seed = hashlib.sha256((phrase + SALT).encode()).digest()
print(f"seed = {seed.hex()}")

while target >= 0:
    dat = bytes.fromhex(input("data > "))
    if seed[:16] not in dat:
        print("bye..")
        exit(-1)
    seed = hashlib.sha256(dat).digest()
    rev = input("reverse?(y/n) > ")
    if rev == 'y':
        seed = seed[::-1]
    print(f"seed = {seed.hex()}")
    target -= 16**leading_zero(seed.hex())
print(FLAG)
exit(0)