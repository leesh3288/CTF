# Written by @RBTree_

import requests
import base64
import binascii
import json

sxor = lambda s1, s2: ''.join(chr((a ^ b) & 0xff) for a,b in zip(s1,s2))

INVALID_PADSIZE = "invalid pad size"
CORRECT_VALUE = "decryptable session value"

def login():
    data = {
        "userid": "root",
        "password": "root",
    }
    return requests.post("http://host7.dreamhack.games:8980/api/login", json=data).text

def check_video(path):
    data = {
        "path": path
    }
    # print(data)
    return requests.post("http://host7.dreamhack.games:8980/api/check/video", json=data).text

def oracle(path):
    return json.loads(check_video(base64.b64encode(path)))['success']

def padding_oracle_block(prev_block, block):
    plain_block = bytearray(len(prev_block))
    for i in range(len(block)):
        for b in range(256):
            print(i, b)
            p =plain_block[:]
            for j in range(i):
                p[15 - j] = plain_block[15 - j] ^ prev_block[15 - j] ^ (i+1)
            p[15 - i] = b

            if oracle(p + block):
                plain_block[15 - i] = (i+1) ^ prev_block[15 - i] ^ b
                break
        else:
            raise ValueError("NOT FOUND")
    return bytes(plain_block)

if __name__ == "__main__":

    leaked_iv = []

    # Initialize blocks
    ct = bytearray(base64.b64decode("KFxNCO0NAHWOSwr+sHrP2I2t9dsBClRuy8wyJsM/7RkXLg/fLM8qf7AqlpAaIQ5MwxGysMs+9HNsMgKuyjkQhndqZtAuVWaAX5z3CTg2l88="))

    pt = b'minumfile is in static/media/h1dd3nf1l35s/f14gs.m'
    for i in range(2, 6):
        pt += padding_oracle_block(ct[16 * i - 16:16 * i], ct[16 * i:16 * i + 16])
        print(pt)