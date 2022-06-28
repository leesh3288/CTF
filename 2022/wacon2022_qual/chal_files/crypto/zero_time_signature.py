#!/usr/bin/python3
import hashlib
import os
import signal

MESSAGE_LEN = 18
SPELL = 'gimme a flag plz^^'
FLAG = open("flag.txt").read()

def forward(msg, step):
    for _ in range(step):
        msg = hashlib.sha256(msg).digest()
    return msg

def keygen():
    priv = [[] for _ in range(MESSAGE_LEN + 1)]
    for i in range(MESSAGE_LEN):
        priv[i].append((os.urandom(32)))
        for j in range(256):
            priv[i].append(hashlib.sha256(priv[i][-1]).digest())
        
    priv[MESSAGE_LEN].append((os.urandom(32)))
    for j in range(256 * MESSAGE_LEN):
        priv[MESSAGE_LEN].append(hashlib.sha256(priv[MESSAGE_LEN][-1]).digest())  

    pub = [L[-1] for L in priv]
    priv[MESSAGE_LEN].reverse()
    return priv, pub

def sign(msg, priv):
    assert(len(msg) == MESSAGE_LEN)
    assert(len(priv) == MESSAGE_LEN+1)
    tot = 0
    sig = []
    for i, c in enumerate(msg):
        sig.append(priv[i][256 - ord(c)])
        tot += ord(c)
    sig.append(priv[MESSAGE_LEN][256 * MESSAGE_LEN - tot])
    return sig

def verify(msg, signature, pub):
    assert(len(msg) == MESSAGE_LEN)
    assert(len(signature) == MESSAGE_LEN+1)
    assert(len(pub) == MESSAGE_LEN+1)
    tot = 0
    for i, c in enumerate(msg):
        if forward(signature[i], ord(c)) != pub[i]:
            return False
        tot += ord(c)
    return forward(signature[MESSAGE_LEN], 256 * MESSAGE_LEN - tot) == pub[MESSAGE_LEN]
    
priv, pub = keygen()
for i, c in enumerate(pub):
    print(f"pub[{i}] = {pub[i].hex()}")

print("You can sign for the ONLY ONE message")
msg = input("message > ")

if len(msg) != MESSAGE_LEN or msg == SPELL:
    print("no...")
    exit(-1)

sig1 = sign(msg, priv)
for i, c in enumerate(sig1):
    print(f"sig1[{i}] = {sig1[i].hex()}")

print("Can you forge a signature for the magical message 'gimme a flag plz^^'?")

sig2 = []
for i in range(MESSAGE_LEN+1):
    tmp = input(f"sig2[{i}] (in hex) > ")
    sig2.append(bytes.fromhex(tmp))

if verify(SPELL, sig2, pub):
    print("Good job!", FLAG)
else:
    print("no...")
    exit(-1)