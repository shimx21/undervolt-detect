import tensorflow as tf
from keras.models import Sequential
from keras.layers import Conv1D, DepthwiseConv1D, AveragePooling1D, Dense, GlobalAveragePooling1D
import numpy as np


def get_model(X_train, id: int = 0):
    if id == 0:
        model = Sequential([
            Conv1D(16, 5, activation='relu', input_shape=(X_train.shape[1],1)),
            DepthwiseConv1D(3, activation='relu'),
            AveragePooling1D(4),
            
            Conv1D(32, 3, activation='relu'),
            GlobalAveragePooling1D(),
            
            Dense(1, activation='sigmoid')
        ])
    elif id == 1:
        model = Sequential([
            Conv1D(16, 15, activation='relu', input_shape=(X_train.shape[1],1)),
            DepthwiseConv1D(3, activation='relu'),
            AveragePooling1D(4),
            
            Conv1D(32, 3, activation='relu'),
            GlobalAveragePooling1D(),
            
            Dense(1, activation='sigmoid')
        ])
    elif id == 2:
        model = Sequential([
            Conv1D(16, 1024, 2, activation='relu', input_shape=(X_train.shape[1],1)),
            DepthwiseConv1D(3, activation='relu'),
            AveragePooling1D(4),
            Conv1D(32, 3, activation='relu'),
            GlobalAveragePooling1D(),
            Dense(1, activation='sigmoid')
        ])
        
    elif id == 3:
        model = Sequential([
            Conv1D(16, 512, 256, activation='relu', input_shape=(X_train.shape[1],1)),
            DepthwiseConv1D(3, activation='relu'),
            AveragePooling1D(4),
            Conv1D(32, 3, activation='relu'),
            GlobalAveragePooling1D(),
            Dense(1, activation='sigmoid')
        ])
    elif id == 4:
        model = Sequential([
            Conv1D(16, 1024, 512, activation='relu', input_shape=(X_train.shape[1],1)),
            DepthwiseConv1D(3, activation='relu'),
            AveragePooling1D(4),
            Conv1D(32, 3, activation='relu'),
            GlobalAveragePooling1D(),
            Dense(1, activation='sigmoid')
        ])
    
    elif id == 5:
        model = Sequential([
            Conv1D(16, 2048, 1024, activation='relu', input_shape=(X_train.shape[1],1)),
            DepthwiseConv1D(3, activation='relu'),
            AveragePooling1D(4),
            Conv1D(32, 3, activation='relu'),
            GlobalAveragePooling1D(),
            Dense(1, activation='sigmoid')
        ])
    
    elif id == 6:
        model = Sequential([
            Conv1D(16, 50, activation='relu', input_shape=(X_train.shape[1],1)),
            DepthwiseConv1D(3, activation='relu'),
            AveragePooling1D(4),
            Conv1D(32, 3, activation='relu'),
            GlobalAveragePooling1D(),
            Dense(1, activation='sigmoid')
        ])
    else:
        raise ValueError(f"Model ID {id} is not implemented.")
    print(model.count_params())
    return model
