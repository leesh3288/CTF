from Crypto.Util.number import long_to_bytes as l2b
import json

with open('sent.json', 'r', encoding='UTF-8') as f:
    dat = f.read()
    sent = json.loads(dat)

fl = b""
ag = b""

for packet in sent:
    if int(packet["_source"]["layers"]["frame"]["frame.number"]) in range(504, 683):
        fl += l2b(int(packet["_source"]["layers"]["data"]["data.data"][21:].replace(':', ''), 16))
    elif int(packet["_source"]["layers"]["frame"]["frame.number"]) in range(702, 933):
        ag += l2b(int(packet["_source"]["layers"]["data"]["data.data"][21:].replace(':', ''), 16))

with open('fl.rsf', 'wb') as f:
    f.write(fl)
with open('ag.rsf', 'wb') as f:
    f.write(ag)

print("fin")