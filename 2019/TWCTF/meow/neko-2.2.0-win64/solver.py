from PIL import Image, ImageChops
import os, pickle

#white = Image.new('RGB', [768, 768], 'white')
#white.save('white.png')
#os.system('neko meow.n white.png white_enc.png')
white_enc = Image.open('white_enc.png')

def inv_crd():
    res = [-1] * 768
    test = Image.new('RGB', [768, 768], 'white')
    for i in range(768):
        test.putpixel((i, i), (0, 0, 0))
    test.save('test.png')
    
    os.system('neko meow.n test.png test_enc.png')
    
    test_enc = Image.open('test_enc.png')
    for y in range(768):
        found = False
        for x in range(768):
            if test_enc.getpixel((x, y)) != white_enc.getpixel((x, y)):
                assert(not found)
                found = True
                res[x] = y

    return res

REP = 768*25
    
def inv_col(inverse_crd):
    res = [[-1]*256 for i in range(REP)]

    for rept in range(11):
        test = Image.new('RGB', [768, 768], 'white')
        for i in range(REP):
            for j in range(0, 25):
                idx = i + REP * j
                crd = (idx % 768, idx // 768)
                col = ((rept * 25 + j * 3) & 0xff, (rept * 25 + j * 3 + 1) & 0xff, (rept * 25 + j * 3 + 2) & 0xff)
                test.putpixel(crd, col)
            if i % 768 == 0:
                print('#{}-{} putpixel done'.format(rept, i))
        test.save('test.png'.format(i))
        
        os.system('neko meow.n test.png test_enc.png')
        
        test_enc = Image.open('test_enc.png')
        for i in range(REP):
            for j in range(0, 25):
                idx = i + REP * j
                crd = (inverse_crd.index(idx % 768), idx // 768)
                col = test_enc.getpixel(crd)
                for k in range(3):
                    assert(res[i][col[k]] == -1 or res[i][col[k]] == (rept * 25 + j * 3 + k) & 0xff)
                    res[i][col[k]] = (rept * 25 + j * 3 + k)&0xff
    
    return res
    
if __name__ == '__main__':
    res, inverse_crd, inverse_col = [], [-1] * 768, []
    
    if os.path.isfile('inverse_crd.pickle'):
        with open('inverse_crd.pickle', 'rb') as f:
            inverse_crd = pickle.load(f)
    else:
        inverse_crd = inv_crd()
        assert(-1 not in inverse_crd)
        
        with open('inverse_crd.pickle', 'wb') as f:
            pickle.dump(inverse_crd, f, pickle.HIGHEST_PROTOCOL)
            
    #print(inverse_crd)
    
    if os.path.isfile('inverse_col.pickle'):
        with open('inverse_col.pickle', 'rb') as f:
            inverse_col = pickle.load(f)
    else:
        inverse_col = inv_col(inverse_crd)
        assert(False not in [-1 not in inverse_col])
        
        with open('inverse_col.pickle', 'wb') as f:
            pickle.dump(inverse_col, f, pickle.HIGHEST_PROTOCOL)
    
    #print(inverse_col)

    flag_enc = Image.open('flag_enc.png')
    flag = Image.new('RGB', [768, 768], 'white')
     
    for y in range(flag_enc.size[1]):
        for x in range(flag_enc.size[0]):
            crd = (inverse_crd[x], y)
            idx = crd[0] + crd[1] * flag_enc.size[0]
            col_enc = flag_enc.getpixel((x, y))
            col = tuple(inverse_col[idx % REP][col_enc[i]] for i in range(3))
            flag.putpixel(crd, col)
    flag.save('flag.png')

# TWCTF{Ny4nNyanNy4n_M30wMe0wMeow}

