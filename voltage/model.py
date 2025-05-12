import keras
from keras import layers, models
import numpy as np


def get_model(n_reads):
    return models.Sequential([
        # 输入形状 (m, 1)
        layers.Conv1D(filters=32, kernel_size=5, activation='relu', 
            input_shape=(n_reads, 1), padding='same'),
        layers.MaxPooling1D(pool_size=2),
        
        layers.Conv1D(filters=64, kernel_size=3, activation='relu', padding='same'),
        layers.MaxPooling1D(pool_size=2),
        
        layers.GlobalAveragePooling1D(),  # 替代Flatten，更适应时序数据
        
        layers.Dense(32, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(1, activation='sigmoid')
    ])

def augment_ts(sequence):
    if np.random.rand() > 0.5:
        shift = np.random.randint(-3,3)
        sequence = np.roll(sequence, shift)
    
    # noise = np.random.normal(0, 0.01, size=sequence.shape)
    return sequence # + noise

    