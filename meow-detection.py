import numpy as np
import librosa as lr
import matplotlib.pyplot as plt
from pathlib import Path
import warnings
from PIL import Image
import os

import tensorflow as tf
print("Num GPUs Available: ", len(tf.config.list_physical_devices('GPU')))
print(tf.config.list_physical_devices('GPU'))
input()

def audio_to_image(path, height=192, width=192):
    signal, sr = lr.load(path, res_type='kaiser_fast')
    hl = signal.shape[0]//(width*1.1)
    spec = lr.feature.melspectrogram(signal, n_mels=height, hop_length=int(hl))
    img = lr.power_to_db(spec)**2
    start = (img.shape[1] - width) // 2
    return img[:, start:start+width]

meow_images = []

for i in range(1,200):
    filename = 'data/cat_'+str(i)+'.wav'
    if Path('./'+filename).exists():
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            img = audio_to_image(filename)
            meow_images.append(img)
            
            #plt.imshow(img)
            #plt.savefig('training/cat_'+str(i)+'.png')

# Importing the Keras libraries and packages
from keras.models import Sequential
from keras.layers import Convolution2D
from keras.layers import MaxPooling2D
from keras.layers import Flatten
from keras.layers import Dense

# image size: 432x288
height = 432
width = 288

#Initialising the CNN
classifier = Sequential()
# Step 1 - Convolution
classifier.add(Convolution2D(32, 3, 3, input_shape = (height,width, 3), activation = 'relu'))
# Step 2 - Pooling
classifier.add(MaxPooling2D(pool_size = (2, 2)))
# Adding a second convolutional layer
classifier.add(Convolution2D(32, 3, 3, activation = 'relu'))
classifier.add(MaxPooling2D(pool_size = (2, 2)))
# Step 3 - Flattening
classifier.add(Flatten())
# Step 4 - Full connection
classifier.add(Dense(128, activation = 'relu'))
classifier.add(Dense(1, activation = 'sigmoid'))
# Compiling the CNN
classifier.compile(optimizer = 'adam', loss = 'binary_crossentropy', metrics = ['accuracy'])

from keras.preprocessing.image import ImageDataGenerator

# Data Augmentation
train_datagen = ImageDataGenerator(rescale = 1./255,
                                   shear_range = 0.2,
                                   zoom_range = 0.2,
                                   horizontal_flip = True)
test_datagen = ImageDataGenerator(rescale = 1./255)
training_set = train_datagen.flow_from_directory(r"./images/training/",
                                                 target_size = (height,width),
                                                 batch_size = 4, #32
                                                 class_mode = 'binary')
test_set = test_datagen.flow_from_directory(r"./images/test/",
                                            target_size = (height,width),
                                            batch_size = 4, #32
                                            class_mode = 'binary')

from tensorflow import keras

# train model
def train_model():
    epochs = 10

    callbacks = [
        # save model
        keras.callbacks.ModelCheckpoint("save_at_{epoch}.h5"),
    ]
    classifier.compile(
        optimizer=keras.optimizers.Adam(1e-3),
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )
    classifier.fit(
        training_set, epochs=epochs, callbacks=callbacks, validation_data=test_set,
    )

# load model
def load_model()

# run inference on new data
def run_inference_on_new_data(path, model):
    img = keras.preprocessing.image.load_img(
        "PetImages/Cat/6779.jpg", target_size=image_size
    )
    img_array = keras.preprocessing.image.img_to_array(img)
    img_array = tf.expand_dims(img_array, 0)  # Create batch axis

    predictions = model.predict(img_array)
    score = predictions[0]
    print(
        "This image is %.2f percent cat and %.2f percent dog."
        % (100 * (1 - score), 100 * score)
    )