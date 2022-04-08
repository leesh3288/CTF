# Trino: {Albireo, Pieces, Rendezvous, Mirai}

GoN Open Qual 2022 Spring

Category:
- Albireo: **Web**
- Pieces: **Misc**, Pwn, Web
- Rendezvous: **Pwn**
- Mirai: **Pwn**

Author: Xion

Estimated Difficulty: 2.5~4.5 / 5


## Description

### Trino: Albireo

`Stage 1`

Look upon the brilliant stars of the night sky.  
Admire the pale gold and indigo blue of the double star `Albireo`.

### Trino: Pieces

`Stage 2`

Stitch the `Pieces` together for the Big Picture.

### Trino: Rendezvous

`Stage 3 - 1`

`Rendezvous` back to Zero with this one weird trick!

### Trino: Mirai

`Stage 3 - 2`

No more years-old dead PoCs, take a step into `Mirai`.

## Summary

### Trino: Albireo

- SSRF to Memcached via [HTTPS session id poisoning + DNS Rebinding Attack](https://i.blackhat.com/USA-20/Wednesday/us-20-Maddux-When-TLS-Hacks-You.pdf)
- Similar to [hxp CTF 2020 security scanner](https://ctftime.org/writeup/25661)

**Flag: `GoN{B34ut1ful_y37_po!s0nou5_st4r5_60und_t0_e4ch_07h3r}`**

### Trino: Pieces

- RCE on Python app server via Memcached SSRF (from `Trino: Albireo`) + Pyjailed Flask-Session unpickle
- Similar to [Real World CTF 2018 Quals Bookhub](https://ctftime.org/writeup/10558) / [Samsung CTF 2018 Quals Webcached](https://blog.tonkatsu.info/ctf/2018/07/01/sctf-2018-quals.html#webcached) + [Balsn CTF 2019 pyshv2](https://ctftime.org/writeup/16723)

**Flag: `GoN{St4k1ng_th3_p!ckl3s_4_l4t3r4l_m0v3men7}`**

### Trino: Rendezvous

- RCE on Redis 6.2.4 32bit via [CVE-2021-32761](http://cve.mitre.org/cgi-bin/cvename.cgi?name=2021-32761) requiring incorrect mitigation (blocking `CONFIG SET`) bypass
- Players can possibly use other applicable CVEs, but the use of "privileged" commands (`DEBUG`, `OBJECT`, etc.) are intentionally blocked

**Flag: `GoN{R3ndezv0u5_0n_bi7f1eld5_feat._CVE-2021-32761}`**

### Trino: Mirai

- RCE on Redis latest (6.2.5 by the time of chal creation, applicable for all Redis 6.x.x) default config via 0-day
- Quick inspection into some fishy commands (`DEBUG`) show that the command easily allows RCE via `mallctl`
- Note: After Pull [#9202](https://github.com/redis/redis/pull/9202) `set-disable-deny-scripts` was available, which allows RCE in a non-interactive (no-output) model by setting the flag and sending a single exploitation script in Lua (until Pull [#9920](https://github.com/redis/redis/pull/9920) disabled `DEBUG` by default)

**Flag: `GoN{M!r41_R3d1s_4nd_RCE_3xpl01ts}`**
