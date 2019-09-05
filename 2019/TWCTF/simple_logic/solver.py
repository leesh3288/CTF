BITS = 128

enc_flag = 0x43713622de24d04b9c05395bb753d437
pair = [(0x29abc13947b5373b86a1dc1d423807a,0xb36b6b62a7e685bd1158744662c5d04a),
        (0xeeb83b72d3336a80a853bf9c61d6f254,0x614d86b5b6653cdc8f33368c41e99254),
        (0x7a0e5ffc7208f978b81475201fbeb3a0, 0x292a7ff7f12b4e21db00e593246be5a0),
        (0xc464714f5cdce458f32608f8b5e2002e, 0x64f930da37d494c634fa22a609342ffe),
        (0xf944aaccf6779a65e8ba74795da3c41d, 0xaa3825e62d053fb0eb8e7e2621dabfe7),
        (0x552682756304d662fa18e624b09b2ac5, 0xf2ffdf4beb933681844c70190ecf60bf),
        ]
        
def enc(p, k):
    c = p
    mask = (1 << BITS) - 1
    for _ in range(765):
        c = (c + k) & mask
        c = c ^ k
    return c

def dec(p, k):
    c = p
    mask = (1 << BITS) - 1
    for _ in range(765):
        c = c ^ k
        c = (c - k) & mask
    return c

built = 0
for pos in range(BITS // 8):
    pos_mask = (1 << (8 * (pos + 1) + 1)) - 1
    hit = [0]*512
    for trial in pair:
        for i in range(512):
            try_built = built + (i << (8 * pos))
            if enc(trial[0] & pos_mask, try_built) & pos_mask == trial[1] & pos_mask:
                hit[i] += 1
    for h in enumerate(hit):
        if h[1] == 6:
            built += ((h[0] & 0xff) << (8 * pos))
            break
    print("{:032x}".format(built))

print("TWCTF{%x}"%dec(enc_flag, built))

# TWCTF{ade4850ad48b8d21fa7dae86b842466d}

