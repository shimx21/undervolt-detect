import tensorflow as tf
from keras.models import Sequential
from keras.layers import Conv1D, DepthwiseConv1D, AveragePooling1D, Dense, GlobalAveragePooling1D
import numpy as np


def get_model(X_train):
    model = Sequential([
        Conv1D(16, 5, activation='relu', padding='same', input_shape=(X_train.shape[1],1)),
        DepthwiseConv1D(3, activation='relu'),
        AveragePooling1D(4),
        
        Conv1D(32, 3, activation='relu', padding='same'),
        GlobalAveragePooling1D(),
        
        Dense(1, activation='sigmoid')
    ])
    return model
    