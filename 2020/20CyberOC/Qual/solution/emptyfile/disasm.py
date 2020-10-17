from collections import Iterable

with open('code.txt', 'r') as f:
    code = f.read()

class Op():
    def __init__(self, inst, ip, oplen, val=None):
        self.inst = inst
        self.ip = ip
        self.oplen = oplen
        self.val = val
        self.dce = False  # dead code elimination
        self.pseudo_op = False
    
    def __str__(self):
        s = "{:04x}: {}".format(self.ip, self.inst)
        if self.val is not None:
            if isinstance(self.val, list):
                s += " " + " ".join(("{:x}".format(v) if isinstance(v, int) else v) for v in self.val)
            else:
                s += " " + ("{:x}".format(self.val) if isinstance(self.val, int) else self.val)
        if self.pseudo_op:
            s += " (pseudo-op)"
        return s

def c2v(code, st):
    cur = 0
    val = 0
    while st + cur < len(code):
        if code[st + cur] == '\t':
            val = val * 2 + 1
        elif code[st + cur] == ' ':
            val = val * 2
        else:
            break
        cur += 1
    return val, st + cur + 1

def hyperop(ip):
    dis = []
    while ip + 1 < len(code):
        op = code[ip:ip+2][::-1]
        st_ip = ip
        ip += 2
        if op == '\n\n':
            dis.append(Op('pop', st_ip, ip - st_ip))
        elif op == ' \t':
            dis.append(Op('sub', st_ip, ip - st_ip))
        elif op == ' \n':
            val, ip = c2v(code, ip)
            dis.append(Op('popjz', st_ip, ip - st_ip, val))
        elif op == '  ':
            dis.append(Op('add', st_ip, ip - st_ip))
        elif op == '\n ':
            dis.append(Op('dup', st_ip, ip - st_ip))
        elif op == '\t\n':
            val, ip = c2v(code, ip)
            dis.append(Op('push', st_ip, ip - st_ip, val))
        elif op == '\t ':
            dis.append(Op('put', st_ip, ip - st_ip))
        elif op == '\n\t':
            dis.append(Op('swap', st_ip, ip - st_ip))
        elif op == '\t\t':
            dis.append(Op('get', st_ip, ip - st_ip))

    # DCE
    for i in range(1, len(dis)):
        last, curr = dis[i - 1], dis[i]
        if last.dce or curr.dce:
            continue
        if last.inst == 'push' and last.val != 0 and curr.inst == 'popjz':
            last.dce = curr.dce = True
        elif last.inst == 'push' and curr.inst == 'pop':
            last.dce = curr.dce = True

    # pseudo-op-ify (2)
    for i in range(1, len(dis)):
        a, b = dis[i-1], dis[i]
        if any(x.dce or x.pseudo_op for x in (a, b)):
            continue
        elif a.inst == 'push' and b.inst == 'get':
            a.inst = 'PUSHIDX'
            a.val = '[{:x}]'.format(a.val)
            a.pseudo_op = True
            b.dce = True

    # pseudo-op-ify (3)
    for i in range(2, len(dis)):
        a, b, c = dis[i-2], dis[i-1], dis[i]
        if any(x.dce or x.pseudo_op for x in (a, b, c)):
            continue
        if a.inst == 'push' and b.inst == 'push' and c.inst == 'put':
            a.inst = 'WRITE'
            a.val = ['[{:x}]'.format(b.val), a.val]
            a.pseudo_op = True
            b.dce = c.dce = True

    # pseudo-op-ify (4)
    for i in range(3, len(dis)):
        ds = dis[i-3:i+1]
        if any(x.dce or x.pseudo_op for x in ds):
            continue
        if [d.inst for d in ds] == ['push', 'swap', 'popjz', 'pop']:
            ds[0].inst = 'popjz'
            ds[0].val = ds[2].val
            ds[0].pseudo_op = True
            ds[1].dce = ds[2].dce = ds[3].dce = True

    # filter out non-DCE instr
    dis = [d for d in dis if not d.dce]

    # pseudo-op-ify (2)
    for i in range(1, len(dis)):
        ds = dis[i-1:i+1]
        if [d.inst for d in ds] == ['push', 'popjz']:
            if ds[0].val == 0:
                ds[0].inst = 'JMP'
                ds[0].val = ds[1].val
                ds[0].pseudo_op = True
                ds[1].dce = True
            else:
                ds[0].dce = ds[1].dce = True

    dis = [d for d in dis if not d.dce]

    # pseudo-op-ify (5)
    for i in range(4, len(dis)):
        ds = dis[i-4:i+1]
        if [d.inst for d in ds] == ['push', 'PUSHIDX', 'sub', 'push', 'put']:
            ds[0].inst = 'WRITE_SUB'
            ds[0].val = ['[{:x}]'.format(ds[3].val), ds[1].val, ds[0].val]
            ds[0].pseudo_op = True
            ds[1].dce = ds[2].dce = ds[3].dce = ds[4].dce = True

    dis = [d for d in dis if not d.dce]

    # pseudo-op-ify (9)
    for i in range(8, len(dis)):
        ds = dis[i-8:i+1]
        if [d.inst for d in ds] == ['PUSHIDX', 'push', 'add', 'dup', 'get', 'popjz', 'push', 'swap', 'put']:
            ds[0].inst = 'ASSERT_NZ_WRITE_Z'
            ds[0].val = '[{:x} + {}]'.format(ds[1].val, ds[0].val)
            ds[0].pseudo_op = True
            assert(ds[5].val > 0x1000000)
            for j in range(1, 9):
                ds[j].dce = True

    dis = [d for d in dis if not d.dce]

    # pseudo-op-ify (4)
    for i in range(3, len(dis)):
        ds = dis[i-3:i+1]
        if [d.inst for d in ds] == ['push', 'PUSHIDX', 'sub', 'popjz']:
            ds[0].inst = 'ASSERT_N1'
            ds[0].val = ds[1].val
            ds[0].pseudo_op = True
            assert(ds[3].val > 0x1000000)
            for j in range(1, 4):
                ds[j].dce = True

    dis = [d for d in dis if not d.dce]

    # pseudo-op-ify (6 + 5n + 1)
    for i in range(5, len(dis)):
        ds = dis[i-5:i+1]
        if [d.inst for d in ds] == ['PUSHIDX', 'PUSHIDX', 'swap', 'sub', 'dup', 'popjz']:
            mult = ds[1].val
            assert(ds[5].val > 0x1000000)
            cur = 0
            for j in range(1, 6):
                ds[j].dce = True
            while dis[i+1+cur*5].inst != 'pop':
                for j in range(5):
                    assert(dis[i+1+cur*5 + j].inst == ds[j+1].inst and dis[i+1+cur*5 + j].val == ds[j+1].val)
                    dis[i+1+cur*5 + j].dce = True
                cur += 1
            dis[i+1+cur*5].dce = True
            assert(cur + 1 == 12)
            ds[0].inst = 'NEQ_MULT_1_TO_12'
            ds[0].val = [ds[0].val, ds[1].val]
            ds[0].pseudo_op = True

    dis = [d for d in dis if not d.dce]

    return dis