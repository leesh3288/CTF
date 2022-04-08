from io import BytesIO
import pickle

class Unpickler(pickle.Unpickler):
    def find_class(self, module, name):
        assert module == 'picklable'
        return getattr(__import__('picklable'), name)

def loads(s):
    return Unpickler(BytesIO(s)).load()

dumps = pickle.dumps
