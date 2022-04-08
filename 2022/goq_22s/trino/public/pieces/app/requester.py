from io import BytesIO
import pycurl
import whatwg_url

# Returns (header, body, errstr)
def perform(url):
    with BytesIO() as header_buf, BytesIO() as body_buf:
        c = load_opts(pycurl.Curl())
        
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.WRITEHEADER, header_buf)
        c.setopt(pycurl.WRITEDATA, body_buf)
        
        try:
            c.perform()
        except pycurl.error as e:
            return None, None, repr(e)
        finally:
            c.close()
        
        return (header_buf.getvalue(), body_buf.getvalue(), None)

def normalize_url(url):
    try:
        parsed = whatwg_url.urlparse(url)
    except whatwg_url.UrlParserError:
        return None
    return parsed.geturl()

def load_opts(c):
    c.setopt(pycurl.PROTOCOLS, pycurl.PROTO_HTTP | pycurl.PROTO_HTTPS)
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(pycurl.MAXREDIRS, 5)
    c.setopt(pycurl.TIMEOUT, 5)

    # Let the upper-level DNS resolver take care of caching,
    #  this Curl instance is ephemeral anyways.
    c.setopt(pycurl.DNS_CACHE_TIMEOUT, 0)

    # You can test your https server with self-signed certs, how neat!
    c.setopt(pycurl.SSL_VERIFYPEER, 0)
    c.setopt(pycurl.SSL_VERIFYHOST, 0)

    return c
