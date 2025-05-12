import numpy as np
from build_dataset import build_all
from torch.nn import Conv1d
from constants import *
from model import get_model, augment_ts
import keras
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight


USED_CONFIGS = [
    "normal_spec",
    "normal_openssl",
    "normal_rest",
    "normal_multi",
    "normal_mix",
    "disturbed_t1_spec"
]

def parse_args():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-r", "--seed", type=int, default=42)
    parser.add_argument("-t", "--test", action="store_true", default=False)
    return parser.parse_args()

def main():
    # Load data
    data, labels = build_all(USED_CONFIGS)
    data = data[:,:,np.newaxis]
    print(labels.dtype)
    labels = labels.astype(np.int8)
    seq_len = data.shape[1]
    
    X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size=0.2, stratify=labels, random_state=42)
    # train_datagen = keras.preprocessing.sequence.TimeseriesGenerator(
    #     X_train, y_train,
    #     length=seq_len,
    #     batch_size=32,
    #     preprocessing_function=augment_ts
    # )
    # test_datagen = keras.preprocessing.sequence.TimeseriesGenerator(
    #     X_test, y_test,
    #     length=seq_len,
    #     batch_size=32,
    #     preprocessing_function=augment_ts
    # )

    model = get_model(data.shape[1])

    model.compile(optimizer='adam',
                loss='binary_crossentropy',
                metrics=['accuracy', 
                keras.metrics.Precision(),
                keras.metrics.Recall()])
    
    classes = np.unique(y_train)
    class_weights = compute_class_weight(
        'balanced',
        classes=classes,
        y=y_train
    )
    
    model.fit(
        X_train, y_train,
        epochs=100,
        batch_size=32,
        validation_split=0.2,
        class_weight={i : class_weights[i] for i in classes},
        callbacks=[keras.callbacks.EarlyStopping(
            monitor='val_recall',
            patience=10,
            mode='max',
            restore_best_weights=True
        )]
    )
    
    y_pred_proba = model.predict(X_test)
    y_pred = (y_pred_proba > 0.5).astype(int)

    from sklearn.metrics import classification_report
    print(classification_report(y_test, y_pred))
    
    model.save("model/.temp.h5")

if __name__ == "__main__":
    main()