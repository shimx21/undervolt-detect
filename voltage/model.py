import keras
import tensorflow as tf
from keras.models import Sequential
from keras.layers import Conv1D, DepthwiseConv1D, AveragePooling1D, Dense, GlobalAveragePooling1D
import numpy as np

import tensorflow_model_optimization as tfmot

def get_model(X_train, quantize: bool = True):
    model = Sequential([
        Conv1D(16, 5, activation='relu', padding='same', input_shape=(X_train.shape[1],1)),
        DepthwiseConv1D(3, activation='relu'),
        AveragePooling1D(4),
        
        Conv1D(32, 3, activation='relu', padding='same'),
        GlobalAveragePooling1D(),
        
        Dense(1, activation='sigmoid')  # 无偏置项
    ])
    if not quantize: return model
    
    quant_model = tfmot.quantization.keras.quantize_model(model)

    converter = tf.lite.TFLiteConverter.from_keras_model(quant_model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = lambda: [[X_train[:1000]]]  # 校准数据
    return converter.convert()
    

def augment_ts(sequence):
    if np.random.rand() > 0.5:
        shift = np.random.randint(-3,3)
        sequence = np.roll(sequence, shift)
    
    # noise = np.random.normal(0, 0.01, size=sequence.shape)
    return sequence # + noise

    