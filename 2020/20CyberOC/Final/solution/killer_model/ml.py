#!/usr/bin/env python3

import tensorflow as tf
import numpy as np
from mnist import MNIST
import random

# download your EMNIST dataset

ds_digits = MNIST('ds_digits')
digit_images, digit_labels = ds_digits.load_training()

src = {i: [] for i in range(10 + 26)}

for i, lbl in enumerate(digit_labels):
    src[lbl].append(np.array(digit_images[i]).reshape(-1, 28, 28, 1))

ds_letters = MNIST('ds_letters')
letter_images, letter_labels = ds_letters.load_training()
for i, lbl in enumerate(letter_labels):
    src[lbl + 9].append(np.array(letter_images[i]).reshape(-1, 28, 28, 1))

i2c = []
for i in range(10):
    i2c.append(chr(i + ord('0')))
for i in range(26):
    i2c.append(chr(i + ord('a')))

flag = ''
for i in range(19):
    model = tf.keras.models.load_model(f'models\\flag_{i}.h5', custom_objects={"GlorotUniform": tf.keras.initializers.glorot_uniform})
    activation = []
    for c in range(10 + 26):
        si = random.sample(range(len(src[c])), 100)
        ds = np.concatenate(list(src[c][x] for x in si), axis=0)
        predicted = model.predict(ds)
        activation.append((sum(x[0] for x in predicted), c))
    activation.sort()
    flag += i2c[activation[-1][1]]
    print(activation[-1][0])
    print(flag)

#print(labels)

#print(a)
#model.summary()
#print(model.predict(a))
