from PIL import Image, ImageChops
from multiprocessing import Pool
import os
import math

def divisorGenerator(n):
    large_divisors = []
    for i in range(1, int(math.sqrt(n) + 1)):
        if n % i == 0:
            yield i
            if i*i != n:
                large_divisors.append(n // i)
    for divisor in reversed(large_divisors):
        yield divisor

"""
flag_enc = Image.open('flag_enc.png')
test = Image.new('RGB', [100, 6000], 'white')
for y in range(flag_enc.size[1]):
    for x in range(flag_enc.size[0]):
        idx = x + y * flag_enc.size[0]
        test_crd = (idx % 100, idx // 100)
        test.putpixel(test_crd, flag_enc.getpixel((x, y)))
test.save('flag_enc_100.png')
"""

white_enc = Image.open('white_enc.png')

reverser = [-1]*768

def rev(i):
    div = i + 768 * 25
    crd = (div % 768, div // 768)
    test = Image.new('RGB', [768, 768], 'white')
    test.putpixel(crd, (0, 0, 0))
    test.save('test{}.png'.format(i))
    
    os.system('neko meow.n test{}.png test{}_enc.png'.format(i, i))
    
    test_enc = Image.open('test{}_enc.png'.format(i))
    diff = ImageChops.difference(white_enc, test_enc)
    diffbox = diff.getbbox()
    print(diffbox)
    assert(diffbox[2] - diffbox[0] == diffbox[3] - diffbox[1] == 1)
    pix_zero = test_enc.getpixel(diffbox[0:2])
    
    test = Image.new('RGB', [768, 768], 'white')
    test.putpixel(crd, (1, 1, 1))
    test.save('test{}.png'.format(i))
    
    os.system('neko meow.n test{}.png test{}_enc.png'.format(i, i))
    
    test_enc = Image.open('test{}_enc.png'.format(i))
    pix_one = test_enc.getpixel(diffbox[0:2])
    print(pix_zero, pix_one)
    delta = tuple(pix_one[j] - pix_zero[j] for j in range(3))
    
    os.remove('test{}.png'.format(i))
    os.remove('test{}_enc.png'.format(i))
    return (diffbox[0], i, delta)

if __name__ == '__main__':
    res, revmap = [], [-1] * 768
    #with Pool(1) as p:
    #    res = p.map(rev, (i for i in range(768)))
    for i in range(768):
        revpair = rev(i)
    #for revpair in res:
        revmap[revpair[0]] = revpair[1]
    assert(-1 not in revmap)

    print(reverser)