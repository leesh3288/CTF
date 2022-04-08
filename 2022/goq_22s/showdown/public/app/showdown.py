#!/usr/bin/env python3

from flask import Flask, render_template, request, Response
from cmark_gfm import md2html, leak

app = Flask(__name__)

@app.route("/")
def route_get():
    return render_template("index.html")

@app.route("/render", methods=["POST"])
def route_render():
    return Response(md2html(request.stream), mimetype='text/html')

@app.route("/reload", methods=["POST"])
def route_reload():
    exit(0)

LEAK_CTR_FILE = '/tmp/leakctr'

def get_leak_ctr():
    with open(LEAK_CTR_FILE, 'r') as f:
        return int(f.read())

def set_leak_ctr(ctr):
    with open(LEAK_CTR_FILE, 'w') as f:
        f.write(str(ctr))

# To speed things up, you can prove that you have address leak
# After 5 correct "Proof of Leak", server will toss you the leak
@app.route("/chal/proof_of_leak", methods=["POST"])
def route_chal_pol():
    if int(request.data) == leak():
        set_leak_ctr(get_leak_ctr() + 1)
    else:
        set_leak_ctr(0)
    exit(0)

@app.route("/chal/leak")
def route_chal_leak():
    if get_leak_ctr() >= 5:
        return hex(leak())
    else:
        return "Nope!"

if __name__ == '__main__':
    app.run('0.0.0.0', 56925, threaded=False)
