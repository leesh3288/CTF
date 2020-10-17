import pwn


SBOX_SIZE = 0x100

elf = pwn.ELF('./generated.bin.bak')
sbox_data = elf.read(elf.symbols['sbox'], 4 * SBOX_SIZE)
sbox = [pwn.u32(sbox_data[4*i:4*i+4]) for i in range(SBOX_SIZE)]

inv_sbox = [None] * SBOX_SIZE

for i, sb in enumerate(sbox):
    inv_sbox[sb] = i

with open('./generated.bin.bak', 'rb') as f:
    data = f.read()[0x5000:]

for d in range(19):
    encoded_len = pwn.u32(data[:4])
    encoded = data[4:encoded_len+4]
    data = data[encoded_len+4:]
    print(hex(encoded_len))

    encoded = bytes(map(lambda x: inv_sbox[x], encoded))

    encoded = [pwn.u32(encoded[4*i:4*i+4]) for i in range(encoded_len // 4)]

    encoded = encoded[2:] + encoded[:2]

    # Rotate right: 0b1001 --> 0b1100
    ror = lambda val, r_bits, max_bits: \
        ((val & (2**max_bits-1)) >> r_bits%max_bits) | \
        (val << (max_bits-(r_bits%max_bits)) & (2**max_bits-1))


    def step2(i, x):
        if i & 1:
            return ror(x, 25, 32)
        else:
            return ror(x, 10, 32)


    encoded = list(map(step2, range(encoded_len // 4), encoded))
    encoded = encoded[-3:] + encoded[:-3]

    x = 0x19990929
    for i in range(encoded_len // 4):
        encoded[i], x = encoded[i] ^ x, encoded[i]

    with open('./flag_{}.h5'.format(d), 'wb') as f:
        for i in range(encoded_len // 4):
            f.write(pwn.p32(encoded[i]))
