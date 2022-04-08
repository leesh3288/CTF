import requester
from base64 import b64encode

HISTORY_ROTATE_LEN = 10

class ReqCache:
    def __init__(self):
        self.history = []
    
    def query(self, url):
        normalized_url = requester.normalize_url(url)
        history_elem = {'original_url': url, 'normalized_url': normalized_url}
        
        if normalized_url is None:
            history_elem['result'] = {'success': False, 'error': 'Failed to normalize url.'}
        else:
            header, body, errstr = requester.perform(normalized_url)
            if errstr is not None:
                history_elem['result'] = {'success': False, 'error': errstr}
            else:
                history_elem['result'] = {'success': True, 'response': {'header': b64encode(header).decode('ascii'), 'body': b64encode(body).decode('ascii')}}
        
        self.history.append(history_elem)
        self.history = self.history[-HISTORY_ROTATE_LEN:]  # rotate history
        
        return history_elem['result']
