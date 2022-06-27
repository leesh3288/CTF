#!/usr/bin/env python3

from pwn import *
from hashlib import sha256
h = lambda b: sha256(b).digest()
h2b = bytes.fromhex

context.log_level = 'debug'

p = remote('175.123.252.143', 9001)

p.sendlineafter('> ', '1q2w3e4r!Q@W#E$R')

st = '010000000156672a04cced3043333aead889c50db10d944a81d65811079703b25e6f2b594b010000006b483045022100c7bdfb8cbc23ab9f99faa20e39032f0a2688ded15cec6080af11f66ef8e9d6b20220744d482239fc1a91c6962b1a3a01b71913bcd84fb0bd66430703d2ffd432f0c3012103d3e1a00cc6e105e9d8c04260b7b7dc7c55f6e87b8f3725601f4010097189bba2ffffffff02e8030000000000001976a914ccd190982a149189b0ad878b14cebffd66b5d3bc88acc0000200000000001976a914ccd190982a149189b0addd4faa79d3a9cfe0ef92b64c7479bed4'
p.sendlineafter('> ', st)
p.sendlineafter('> ', 'n')
st = h(h2b(st)).hex()
p.sendlineafter('> ', st)
p.sendlineafter('> ', 'n')
st = h(h2b(st)).hex()
assert h2b('3ee999b6c5c657b54a84a1e7a93a8ea642ab88b9e991a5a243a447cf95c0f4f0')[::-1] == h2b(st)

cur = h2b(st)
tx = ["b1be3b3cd6575f4d2136b5ab2b99160742af3a3dddabf39107717afe7ebf0130","3ee999b6c5c657b54a84a1e7a93a8ea642ab88b9e991a5a243a447cf95c0f4f0","ec8080063fafa8b2ece5625761b32da6a232da297898a234f397ba702d0bff96","3b8ed6d76762d14576bd38599bb54e2a939d0b5cc218b7a6fc4f646612993d77","5e7ddc63981e0dcc783a7c14bb349b923a1b8907c2eca294b0b6932e3274a401","76aac80fa0e7a621756824106b0b21191d320ae8839a2afab9a29a3d8128e50a","7ac832393fe2b8a9d0d026081cf8b5d5a0823a9bea347d382417ccf9e1d35185","5e9bb73f6a89e51d19c5cc1bc2ca8a6794549a78689ba2614645267c3308ea89","0836bbfa137f63b943ff2330761bb158d6306bd4a12d0e4ce1a7dd8b5e0e50ec","a814cf23c271844775cfcb0cd8f0dd9b198445c562fd9f0c6cd4de1173e91413","4e77e955c5e357e55b9a39bad7719276f3f37eb67e6d66f1a243635bef6a4dbc","df7a6511fc901847fd308cb3cfee8fe68d6fdc7047a83d3e415028d5a69b7b55","01d017bbf638eb4f978d25983ea0bc0d9dc8b464de27823b465e3d1da24c2ae9","34b590c401f8e64748cf65700feea04073639d1832be419f660453ee44277522","7a28dc1cf6abacb8e0a2117c6b1254d96122694f4d9d7eb289d44794530277f8","8522d68e4199eece85184ef31e1206dbf22f3f4fc2ec6b221119d5de9dc10e62","aa8dcdedd2ee9ecf321fc4a4c4511d617d6094d5c957b13ccecc2ebd06a5c95a","52beaa1713982299edbf13ec184c8b963577a89d9a9e6436c6604242c3357046","d161e07aa448fc32884708883dc0c36d2a12927ceb7b425f19784dcc9618ec60","097d8cf2abfbb77d938fbb1f29438f0c7861049e59d4df877fac18cc6638141f","d0ed16595625ee1009d5eb5521fe10787ce0e314e5ed2cb584f0b77c67f7fd84","70c7a2b82406e1cf5aafe7f5c7187230baf60a08a7019ebffa06d60237c8d28f","3fa2de8f7363fe4465765269e47d8853c124ed6aeaceaa186bc118fdd5f928a4","498680c3de12f09422200a7aea8ade371f820fe0f1373bb035c6a14f9893a7db"]
merkleroot = '14ddbde1d6f27c35cd3c91c7da928065001a1b09129ef67582ce475860362953'

merkle_leaf = list(map(lambda x: h2b(x)[::-1], tx))

def BuildMerkleRoot(tx):
    if len(tx) == 1:
        return tx[0]
    if len(tx) % 2 == 1:
        tx = tx + [tx[-1]]
    r = []
    for i in range(0, len(tx), 2):
        global cur
        if cur in (tx[i], tx[i+1]):
            p.sendlineafter('> ', (tx[i] + tx[i+1]).hex())
            p.sendlineafter('> ', 'n')
            p.sendlineafter('> ', h((tx[i] + tx[i+1])).hex())
            p.sendlineafter('> ', 'n')
            cur = h(h(tx[i] + tx[i+1]))
        next_hash = h(h(tx[i] + tx[i+1]))
        r.append(next_hash)
    return BuildMerkleRoot(r)

print(BuildMerkleRoot(merkle_leaf)[::-1].hex())
print(cur[::-1].hex())
print(merkleroot)

# block header
prev = {
    'hash': '000000000000002d35244e76ab8837c7845f66b978bac43c54df9dc88c27ef4d'
}
cur  = {
    'time': 1656241193,
    'version': 628629504,
    'merkle_root': merkleroot,
    'bits': 0x195c44cd,
    'nonce': 736380202,
}

header = p32(int(cur['version'])) + h2b(prev['hash'])[::-1] + h2b(cur['merkle_root'])[::-1] + p32(cur['time']) + p32(int(cur['bits'])) + p32(int(cur['nonce']))
assert len(header) == 80
p.sendlineafter('> ', header.hex())
p.sendlineafter('> ', 'n')
p.sendlineafter('> ', h(header).hex())
p.sendlineafter('> ', 'y')

p.interactive()

# WACon{Some_Vo1unteer_C0mputes_SHA256_F0r_u_And_Me^___^Did_you_use_th3m?}
