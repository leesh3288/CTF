#!/usr/bin/env python3
#-*- coding: utf-8 -*-
from flask import Flask, request, session
from trino import TrinoSession
from config import Config
from picklable import ReqCache
from base64 import b64decode
from datetime import datetime, timedelta
from pycurl import version as curl_version
from nslookup import nslookup

FLAG_ALBIREO = open('../flag_albireo', 'rt').read()

app = Flask(__name__)

app.config.from_mapping(Config)
trino = TrinoSession(app, [
    'memcached://albireo:65401',
    'redis://rendezvous:65402',
    'redis://mirai:65403'
])

@app.route("/")
def route_root():
    return {'success': True}

@app.route("/info")
def route_info():
    return {
        'success': True,
        'version': {
            'curl': curl_version, 'trino': trino.vercheck()
        },
        'network': {
            'pieces': nslookup(), 'trino': trino.ipcheck()
        }
    }

last_HC = (datetime.fromtimestamp(0), None)
@app.route("/healthcheck")
def route_healthcheck():
    global last_HC
    cached = True
    if datetime.now() - last_HC[0] >= timedelta(minutes=1):
        cached = False
        last_HC = (datetime.now(), trino.healthcheck())
    return {'success': True, 'cached': cached, 'health': last_HC[1]}

@app.route("/failover", methods=['POST'])
def route_failover():
    j = request.json
    if j is None or 'url' not in j or not isinstance(j['url'], str):
        return {'success': False, 'error': 'Invalid request. (Failover agent URL not found)'}
    if not trino.failover(j['url']):
        return {'success': False, 'error': 'Nonexistent agent URL.'}
    return {'success': True}

@app.route("/query", methods=['POST'])
def route_query():
    j = request.json
    if j is None or 'url' not in j or not isinstance(j['url'], str):
        return {'success': False, 'error': 'Invalid request. (Query URL not found)'}
    if 'cache' not in session:
        session['cache'] = ReqCache()
    return session['cache'].query(j['url'])

@app.route("/clear")
def route_clear():
    if 'cache' in session:
        cnt = len(session['cache'].history)
        session['cache'].clear()
        return {'success': True, 'cleared_length': cnt}
    return {'success': False, 'error': 'ReqCache not initialized.'}

@app.route("/count")
def route_flush():
    if 'cache' in session:
        cnt = len(session['cache'].history)
        return {'success': True, 'history_length': cnt}
    return {'success': False, 'error': 'ReqCache not initialized.'}

@app.route("/history/<int:hid>")
def route_history(hid):
    if 'cache' not in session:
        return {'success': False, 'error': 'ReqCache not initialized.'}
    elif hid not in range(0, len(session['cache'].history)):
        return {'success': False, 'error': 'History index out of range.'}
    return {'success': True, 'history': session['cache'].history[hid]}

@app.route("/flag")
def route_flag():
    if session.get('flag', None) == 'albireo':
        return {'success': True, 'FLAG_ALBIREO': FLAG_ALBIREO}
    return {'success': False, 'error': 'You haven\'t solved the mystery of Albireo...'}

if __name__ == "__main__":
    app.run("0.0.0.0", 15961, debug=False, threaded=True)
