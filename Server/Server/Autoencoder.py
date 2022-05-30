"""This module builds a sensible model that can be used by the AnoPCB server."""

import tensorflow as tf
from tensorflow.keras import layers as ls
import numpy as np
import os

# the models name and the save-path
model_name = "autoencoder_template_x_28_y_4"
path = os.getcwd()
path = os.path.join(path, f"{model_name}.h5")


def build_model():
    # Input shape: (slice width, slice height, number of signals)
    inp = tf.keras.Input((28, 4, 8))
    noise = ls.GaussianNoise(0.1)

    # Encoder parts
    pool = ls.MaxPool2D()
    conv1 = ls.Conv2D(8, (3, 3), padding="same", activation="relu", use_bias=False)
    norm1 = ls.BatchNormalization()
    conv2 = ls.Conv2D(16, (3, 3), padding="same", activation="relu", use_bias=False)
    norm2 = ls.BatchNormalization()
    conv3 = ls.Conv2D(32, (3, 3), padding="same", activation="relu", use_bias=False)
    norm3 = ls.BatchNormalization()
    flatten = ls.Flatten()

    # Bottleneck
    latent = ls.Dense(32, activation="relu")

    # Decoder parts
    sample = ls.UpSampling2D()
    dense = ls.Dense(224, activation="relu")
    reshape = ls.Reshape((7, 1, 32))
    deconv1 = ls.Conv2DTranspose(
        32, (3, 3), padding="same", activation="relu", use_bias=False
    )
    norm4 = ls.BatchNormalization()
    deconv2 = ls.Conv2DTranspose(
        16, (3, 3), padding="same", activation="relu", use_bias=False
    )
    norm5 = ls.BatchNormalization()
    deconv3 = ls.Conv2DTranspose(
        8, (3, 3), padding="same", activation="sigmoid", use_bias=False
    )
    norm6 = ls.BatchNormalization()

    # Dropout to be applied throughout the network
    dropout = ls.Dropout(0.1)

    # Putting it all together
    x = noise(inp)
    x = conv1(x)
    x = norm1(x)
    x = dropout(x)
    x = pool(x)
    x = conv2(x)
    x = norm2(x)
    x = dropout(x)
    x = pool(x)
    x = conv3(x)
    x = norm3(x)
    x = dropout(x)
    x = flatten(x)
    latent = latent(x)
    x = dense(latent)
    x = reshape(x)
    x = deconv1(x)
    x = norm4(x)
    x = dropout(x)
    x = sample(x)
    x = deconv2(x)
    x = norm5(x)
    x = dropout(x)
    x = sample(x)
    x = deconv3(x)
    reconstructed = x

    # MSE computed for each slice
    mse = tf.math.reduce_mean((inp - reconstructed) ** 2, axis=[1, 2, 3])
    counts = tf.math.reduce_sum(inp, axis=[1, 2, 3])
    # MSE normalized by the amount of non-zero pixels in the input slice
    rect_mse = mse / (counts + 1)

    # Creating the model
    # Error metric is a combination between rect_mse and mse, the factor of 20 is somewhat arbitrary
    model = tf.keras.Model(
        inputs=[inp], outputs=[reconstructed, latent, rect_mse * 20 + mse]
    )
    return model


pcb_autoenc = build_model()
# Loss only to be applied to the first output
pcb_autoenc.compile(
    optimizer="adam",
    loss=[
        "binary_crossentropy",
        None,
        None,
    ],
    loss_weights=[1.0, 0.0, 0.0],
)

# saving the model, server requies h5-format
pcb_autoenc.save(path, include_optimizer=True, save_format="h5")
