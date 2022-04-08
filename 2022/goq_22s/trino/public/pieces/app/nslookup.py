from socket import gethostname, getaddrinfo, AF_INET

def nslookup(host=None):
    if host is None:
        host = gethostname()
    return list(set(ai[4][0] for ai in getaddrinfo(host, None) if ai[0] == AF_INET))
