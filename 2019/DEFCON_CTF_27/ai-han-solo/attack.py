#!/usr/bin/env python3

import hashlib, glob, os, random, re, requests, sys, requests, shutil, itertools
import tensorflow as tf
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from PIL import Image


host = sys.argv[1]
port = sys.argv[2]
base_url = "http://{}:{}".format(host, port)

image_path = "/home/xion/Desktop/GoN/DEFCON_2019/real/ai-han-solo/emnist-png/emnist-balanced"

# EXPLOIT parameters
COMPILE_OPTIONS = { 'loss': 'categorical_crossentropy', 'optimizer': 'adam', 'metrics': ['accuracy'] }
possible_chars = "0123456789ABCDEF"
trials = 4
multi = 3

file_list = {}
for c in possible_chars:
    image_dir = os.path.join(image_path, c)
    file_list[c] = glob.glob(image_dir + "/*.png")

def create_image(hex_str):
    full_img = Image.new('1', (448, 28), color='black')

    for cnt, val in enumerate(hex_str):
        random_file = file_list[val][random.randint(0, len(file_list)-1)]
        img = Image.open(random_file)
        full_img.paste(img, (cnt*28,0))

    img_array = image.img_to_array(full_img)
    img_array = np.expand_dims(img_array, axis=0)

    return img_array


model_filename = 'navigation_parameters_{}.h5'.format(host)

model_file = requests.get('{}/navigation_parameters.h5'.format(base_url), stream=True)
with open(model_filename, 'wb') as f:
    model_file.raw.decode_content = True
    shutil.copyfileobj(model_file.raw, f)

model = load_model(model_filename)
model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

def eeval2(strs, op):
    # imgs = np.stack(np.expand_dims(imageio.imread(i) / 255, 2) for i in paths)
    dat = np.concatenate([create_image(s) for s in strs])
    return zip(map(list, model.predict(dat, steps = None)), strs)

neuron_number = 16

def replace_n_char(flag, n, char):
    return flag[:n] + char + flag[n+1:]

count = 0
while True:
    count += 1
    print("Trial #{}".format(count))
    current_flag = ""
    for i in range(len(current_flag),16, multi):
        strlst = []
        for j in itertools.product(possible_chars, repeat=min(multi, 16-len(current_flag))):
            _j = ''.join(j)
            strlst += [current_flag + _j] * trials
        score = eeval2(strlst, neuron_number)
        current_flag = max(score)[1]
        print(current_flag)

    print(current_flag)
    next_flag = hashlib.sha256(b"000-" + current_flag.encode('latin1')).hexdigest().upper()[:16]
    if (np.argmax(model.predict(create_image(current_flag))) == 16):
        if (np.argmax(model.predict(create_image(next_flag))) == 17):
            print(">> {}".format(next_flag))
            break

data = {"location": current_flag }
response = requests.post("{}/capture".format(base_url), data=data)
print(response.text.split('<p>')[-1].split('\n')[0].strip())

exit(0)