import numpy as np
from keras.preprocessing import image
from keras.applications import inception_v3
from keras import backend as K
from networks.lenet import LeNet
from matplotlib import pyplot as plt
from app import predictimg

def reverse_color_process(imgs):

    mean = [125.307, 122.95, 113.865]
    std  = [62.9932, 62.0887, 66.7048]
    for img in imgs:
        for i in range(3):
            img[:,:,i] = img[:,:,i] * std[i] + mean[i]

    return imgs

for i in range(7, 8):
    model = LeNet()

    # Grab a reference to the first and last layer of the neural net
    model_input_layer = model._model.layers[0].input
    model_output_layer = model._model.layers[-1].output

    object_type_to_fake = 3

    # Load the image to hack
    img = plt.imread(f"static/{i}.jpg")

    print(img)
    #process
    print(img.shape)

    processed = model.color_process(img)

    print(type(processed))

    max_change_above = processed + 0.0325
    max_change_below = processed - 0.0325

    hacked_image = np.copy(processed)

    print(processed)
    learning_rate = 0.1
    cost_function = model_output_layer[0, object_type_to_fake]

    # We'll ask Keras to calculate the gradient based on the input image and the currently predicted class
    # In this case, referring to "model_input_layer" will give us back image we are hacking.
    gradient_function = K.gradients(cost_function, model_input_layer)[0]

    # Create a Keras function that we can call to calculate the current cost and gradient
    grab_cost_and_gradients_from_model = K.function([model_input_layer, K.learning_phase()], [cost_function, gradient_function])

    cost = 0.0

    while cost < 0.98:
    # Check how close the image is to our target class and grab the gradients we
    # can use to push it one more step in that direction.
    # Note: It's really important to pass in '0' for the Keras learning mode here!
    # Keras layers behave differently in prediction vs. train modes!
        cost, gradients = grab_cost_and_gradients_from_model([hacked_image, 0])

    # Move the hacked image one step further towards fooling the model
        hacked_image += gradients * learning_rate

    # Ensure that the image doesn't ever change too much to either look funny or to become an invalid image
        hacked_image = np.clip(hacked_image, max_change_below, max_change_above)

        print("Model's predicted likelihood : {:.8}%".format(cost * 100))

    hacked_image = reverse_color_process(hacked_image)
    print(hacked_image)
    print(hacked_image.shape)
    print(hacked_image[0].shape)
    plt.imsave(f"hack/{i}.jpg", hacked_image[0].astype('uint8'))
    print(predictimg(f"hack/{i}.jpg",LeNet()))