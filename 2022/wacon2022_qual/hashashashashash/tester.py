#!/usr/bin/env python3

from pwn import *
import csv, time, datetime
import requests
import json, struct
from hashlib import sha256
h = lambda b: sha256(b).digest()
h2b = bytes.fromhex

api_block_height = 'https://blockstream.info/testnet/api/block-height/{}'
api_block_txs = 'https://blockstream.info/testnet/api/block/{}/txs/{}'

for i in range(2282300, 2280000, -1):
    block_id = requests.get(api_block_height.format(i)).text.strip()
    print(f'Height {i}: {block_id}')
    j = 0
    while True:
        res = requests.get(api_block_txs.format(block_id, j*25)).text.strip()
        if 'start index out of range' in res:
            break
        j_txs = json.loads(res)
        for j_tx in j_txs:
            if j_tx['locktime'] == struct.unpack('<I', b'e4r!')[0]:
                print(block_id, j_tx['txid'])
                input('YAY! > ')
        j += 1

'''
#api_block = 'https://api.blockchair.com/bitcoin/testnet/raw/block/'
#api_tx = 'https://api.blockchair.com/bitcoin/testnet/raw/transaction/'
#cur_block = '000000000000004d2a27b23972b3c04bbe7a23acedff3faec7d0c333d4886acc'

api_block = 'https://api.blockchair.com/bitcoin/raw/block/'
api_tx = 'https://api.blockchair.com/bitcoin/raw/transaction/'
cur_block = '00000000000000000001616a3fb91033ff0bf3705e7c2efa54ba6784e353acf9'

while True:
    print(f'Block: {cur_block}')
    j_block = requests.get(api_block+cur_block).json()
    txs = j_block['data'][cur_block]['decoded_raw_block']['tx']
    for tx in txs:
        print(f'Tx:    {tx}')
        j_tx = requests.get(api_tx+tx).json()
        raw_tx = h2b(j_tx['data'][tx]['raw_transaction'])
        if b'1q2w3e4r!' in raw_tx:
            print(cur_block, tx, raw_tx.hex())
            input('> ')
        time.sleep(1)
    cur_block = j_block['data'][cur_block]['decoded_raw_block']['previousblockhash']
'''

'''
# tx -> merkleroot algorithm
tx = [...]
merkleroot = "e47cbf8ff9972f20b1cc8f63058b51d7bab3d9ed9d5cc10d9726be26946e0107"

merkle_leaf = list(map(lambda x: h2b(x)[::-1], tx))

def BuildMerkleRoot(tx):
    if len(tx) == 1:
        return tx[0]
    if len(tx) % 2 == 1:
        tx = tx + [tx[-1]]
    r = []
    for i in range(0, len(tx), 2):
        r.append(h(h(tx[i] + tx[i+1])))
    return BuildMerkleRoot(r)

print(BuildMerkleRoot(merkle_leaf)[::-1].hex())
print(merkleroot)
'''

'''
# Block Header Hashing Algorithm

with open('test.tsv', newline='') as f:
    reader = csv.DictReader(f, delimiter='\t')
    blocks = list(reader)

prev = blocks[1]
cur  = blocks[2]

timestamp = int(datetime.datetime.strptime(cur['time'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp())
print(timestamp)

header = p32(int(cur['version'])) + h2b(prev['hash'])[::-1] + h2b(cur['merkle_root'])[::-1] + p32(timestamp) + p32(int(cur['bits'])) + p32(int(cur['nonce']))
assert len(header) == 80
print(header.hex())
print(h(header).hex())
print(h(h(header))[::-1].hex())
print(cur['hash'])
'''
