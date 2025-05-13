import keras
from keras.models import Sequential
from keras.layers import Conv1D, MaxPooling1D, GlobalMaxPooling1D, Dense, Dropout
import numpy as np


def get_model(m):
    return Sequential([
        Conv1D(64, 7, activation='relu', input_shape=(m, 1)),
        MaxPooling1D(4),  # 快速压缩时间维度
        
        Conv1D(128, 5, activation='relu', padding='same'),
        MaxPooling1D(2),
        
        Conv1D(256, 3, activation='relu', padding='same'),
        GlobalMaxPooling1D(),  # 替代GlobalAverage
        
        Dense(128, activation='relu'),
        Dropout(0.5),
        Dense(1, activation='sigmoid')
    ])

def augment_ts(sequence):
    if np.random.rand() > 0.5:
        shift = np.random.randint(-3,3)
        sequence = np.roll(sequence, shift)
    
    # noise = np.random.normal(0, 0.01, size=sequence.shape)
    return sequence # + noise

    