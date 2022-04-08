import serializer
import redis, memcache
import re
import socket
import random, string
from flask.sessions import SessionInterface as FlaskSessionInterface
from flask_session import RedisSessionInterface, MemcachedSessionInterface
from random import sample
from nslookup import nslookup

TIMEOUT = 0.5

url_format = re.compile(r'^(\w+)://([^:]+)(:\d+)?$')

def recv(s, length):
    data = b''
    while len(data) < length:
        recv = s.recv(length - len(data))
        if not recv:
            raise EOFError('truncated recv')
        data += recv
    return data

def redis_healthcheck(s):
    s.send(b'PING\r\n')
    return recv(s, 7) == b'+PONG\r\n'

def memcached_healthcheck(s):
    s.send(b'mn\r\n')
    return recv(s, 4) == b'MN\r\n'

def redis_vercheck(s):
    s.send(b'INFO SERVER\r\n')
    
    resp_info = b''
    while not resp_info.endswith(b'\r\n'):
        resp_info += recv(s, 1)
    assert resp_info.startswith(b'$')
    resp_len = int(resp_info[1:-2])
    
    infos = recv(s, resp_len).decode('ascii').split('\r\n')

    info_dict = {}
    for info in infos:
        if info.lstrip().startswith('#'):
            continue
        sp = info.split(':')
        if len(sp) < 2:
            continue
        info_dict[sp[0]] = ':'.join(sp[1:])

    return f'{info_dict["redis_version"]} {info_dict["arch_bits"]}bit'

def memcached_vercheck(s):
    s.send(b'stats\r\n')
    
    resp = b''
    while not resp.endswith(b'END\r\n'):
        resp += recv(s, 1)

    stats = resp.decode('ascii').split('\r\n')[:-2]

    stat_dict = {}
    for stat in stats:
        sp = stat.split(' ')
        assert len(sp) >= 3 and sp[0] == 'STAT'
        stat_dict[sp[1]] = ' '.join(sp[2:])
    
    return f'{stat_dict["version"]} {stat_dict["pointer_size"]}bit'

class TrinoService:
    def __init__(self, default_port, SessionInterface, Connect, HealthcheckFn, VercheckFn):
        self.default_port = default_port
        self.SessionInterface = SessionInterface
        self.Connect = Connect
        self.HealthcheckFn = HealthcheckFn
        self.VercheckFn = VercheckFn

def InterfaceOverlay(cls, k):
    class SessionInterface(cls):
        serializer = serializer
        def _generate_sid(self):
            return ''.join(random.choices(string.ascii_letters + string.digits, k=k))
    return SessionInterface

SESSION_ID_LEN = 12

SVCS = {
    'redis': TrinoService(
        6379,
        InterfaceOverlay(RedisSessionInterface, SESSION_ID_LEN),
        lambda h, p: redis.Redis(h, p, socket_timeout=TIMEOUT),
        redis_healthcheck,
        redis_vercheck,
    ),
    'memcached': TrinoService(
        11211,
        InterfaceOverlay(MemcachedSessionInterface, SESSION_ID_LEN),
        lambda h, p: memcache.Client([f'{h}:{p}'], socket_timeout=TIMEOUT, unpickler=serializer.Unpickler),
        memcached_healthcheck,
        memcached_vercheck,
    ),
}

class TrinoAgent:
    def __init__(self, interface, prot, host, port, url):
        self.interface = interface
        self.prot = prot
        self.host = host
        self.port = port
        self.url = url
        self.alive = True

# Merges multiple session interfaces into one
class TrinoSession(FlaskSessionInterface):
    def __init__(self, app, kvs):
        self.__ver = None
        self.__ip = None
        self.agents = []
        
        permanent = app.config.get('SESSION_PERMANENT', True)
        use_signer = app.config.get('SESSION_USE_SIGNER', True)
        key_prefix = app.config.get('SESSION_KEY_PREFIX', 's:')

        for kv in kvs:
            parsed = url_format.match(kv)
            if not parsed:
                raise RuntimeError(f'Invalid Key-Value Store URL: {kv}')
            prot, host, port = parsed.group(1, 2, 3)
            if prot not in SVCS:
                raise RuntimeError(f'Unsupported Key-Value Store Type: {prot}')

            svc = SVCS[prot]
            
            port = svc.default_port if port is None else int(port[1:])

            self.agents.append(TrinoAgent(
                svc.SessionInterface(
                    svc.Connect(host, port), key_prefix,
                    use_signer, permanent
                ),
                prot, host, port, kv
            ))
        
        # Query & cache static infos
        self.vercheck()
        self.ipcheck()
        
        app.session_interface = self
    
    # Load from any random alive Key-Value Storages
    def open_session(self, app, request):
        # randomly shuffle agents
        agents_shuffled = sample(self.agents, len(self.agents))
        # ...but try alive ones first!
        agents_ordered = sorted(agents_shuffled, key=lambda x: not x.alive)
        for agent in agents_ordered:
            try:
                return agent.interface.open_session(app, request)
            except:
                agent.alive = False
        raise RuntimeError(f'open_session: Trino Key-Value Server DOWN!')

    # Save to all alive Key-Value Storages (at least one must succeed)
    def save_session(self, app, session, response):
        alive = False
        for agent in sample(self.agents, len(self.agents)):
            try:
                agent.interface.save_session(app, session, response)
                alive = True
            except:
                agent.alive = False
        if not alive:
            raise RuntimeError(f'save_session: Trino Key-Value Server DOWN!')

    def fn_runner(self, fn_retriever, result_fn):
        results = []

        for agent in self.agents:
            prot, host, port = agent.prot, agent.host, agent.port
            result = None
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(TIMEOUT)
                s.connect((host, port))
                result = fn_retriever(SVCS[prot])(s)
            except:
                pass
            finally:
                try:  # close the socket if the handlers have not done it themselves
                    s.close()
                    del s
                except:
                    pass
                
                result_fn(agent, result)
                results.append(result)
        
        return results
    
    def as_dict(self, key_retriever, agent_infos):
        assert len(self.agents) == len(agent_infos)
        return {key_retriever(self.agents[i]): agent_infos[i] for i in range(len(self.agents))}

    # Simple healthcheck via ping-pong
    def healthcheck(self):
        def set_alive(agent, result):
            agent.alive = bool(result)
        results = self.fn_runner(lambda svc: svc.HealthcheckFn, set_alive)
        return self.as_dict(lambda agent: agent.url, list(map(bool, results)))
    
    # Simple version retriever
    def vercheck(self):
        if self.__ver is not None:
            return self.__ver
        results = self.fn_runner(lambda svc: svc.VercheckFn, lambda _, __: None)
        self.__ver = self.as_dict(lambda agent: agent.url, results)
        return self.__ver

    # Simple hostname resolver
    def ipcheck(self):
        if self.__ip is not None:
            return self.__ip
        results = [nslookup(agent.host) for agent in self.agents]
        self.__ip = self.as_dict(lambda agent: agent.host, results)
        return self.__ip
    
    # Flag an agent as dead to test failover
    def failover(self, url):
        for agent in self.agents:
            if agent.url == url:
                agent.alive = False
                return True
        return False
