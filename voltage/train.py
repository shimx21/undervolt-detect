import numpy as np
from build_dataset import DatasetBuilder, DatasetGroup
from constants import *
from model import get_model
import datetime, os, json, pickle, random
import tensorflow as tf

import keras
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from utils.tools import set_random_seed

def parse_args():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-n", "--name", type=str, default=str(datetime.datetime.now().strftime("%Y%m%d%H%M%S")))
    parser.add_argument("-g", "--dataset_group", type=str, default="default")
    parser.add_argument("-r", "--seed", type=int, default=42)
    parser.add_argument("-R", "--retrain", action="store_true", default=False, help="Retrain model even if the one with same name exists.")
    
    # parser.add_argument("--test", action="store_true", default=False)
    
    # Train args
    parser.add_argument("-e", "--epochs", type=int, default=100)
    parser.add_argument("-b", "--batch_size", type=int, default=32)
    parser.add_argument("-p", "--patience", type=int, default=5)
    
    # Train setting
    parser.add_argument("-s", "--scale_method", type=str, choices=["robust", "standard"], default="robust")
    
    # Additional
    # parser.add_argument("--quantize_model", action="store_true", default=False)
    parser.add_argument("--threshold_opt", action="store_true", default=False, help="Threshold optimizaion")
    parser.add_argument("-t", "--target_prec", type=float, default=0.9995)
    
    return parser.parse_args()

def scale_input(X_train, X_test, y_train, method = "robust"):
    if method == "robust":
        from sklearn.preprocessing import RobustScaler
        scaler = RobustScaler()
    elif method == "standard":
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
    else:
        raise NotImplementedError(f"Scaling method {method} not implemented")
    X_train = scaler.fit_transform(X_train,y_train)
    X_test = scaler.transform(X_test)
    return X_train, X_test, scaler

def threshold_opt_prec(y_val, y_val_pred, target_prec):
    from sklearn.metrics import precision_recall_curve
    precisions, recalls, thresholds = precision_recall_curve(y_val, y_val_pred)

    viable_thresholds = thresholds[precisions[:-1] >= target_prec]
    if len(viable_thresholds) > 0:
        optimal_threshold = viable_thresholds[0]
    else:
        optimal_threshold = 0.5

    return optimal_threshold

def load_data(config_name, scaler_method):
    target_dir = os.path.join(DatasetGroup._TARGET_DIR, config_name)
    data, labels = DatasetGroup.load_from(target_dir)
    data = np.ascontiguousarray(data, np.float32)
    labels = labels.astype(np.int8)
    
    X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size=0.2, stratify=labels)
    if scaler_method:
        X_train, X_test, scaler = scale_input(X_train, X_test, y_train, scaler_method)
    else:
        scaler = None
    X_train = X_train[:,:,np.newaxis]
    X_test = X_test[:,:,np.newaxis]
    return X_train, X_test, y_train, y_test, scaler

def train_model(model, X_train, y_train, args):
    model.compile(optimizer='Nadam',
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
    
    history = model.fit(
        X_train, y_train,
        epochs=args.epochs,
        batch_size=args.batch_size,
        validation_split=0.2,
        class_weight={i : class_weights[i] for i in classes},
        
        callbacks=[keras.callbacks.EarlyStopping(
            monitor='val_precision',
            patience=args.patience,
            mode='max',
            min_delta=0.001
        )]
    )
    return model

def test_model(model, X_test, y_test, args):
    from sklearn.metrics import classification_report
    y_test_prob = model.predict(X_test)
    y_test_pred = (y_test_prob > args.threshold).astype(int)

    return classification_report(y_test, y_test_pred, digits=6)

def load_model(load_dir):
    model = keras.models.load_model(os.path.join(load_dir, "model.keras"))
    with open(os.path.join(load_dir, "config.json"), "r") as fp:
        args = json.load(fp)
    with open(os.path.join(load_dir, "scaler.pkl"), "rb") as fp:
        scaler = pickle.load(fp)
    return model, scaler, args

def save_model(model, scaler, args, save_dir):
    model.save(os.path.join(save_dir, "model.keras"))
    with open(os.path.join(save_dir, "config.json"), "w") as fp:
        json.dump(args.__dict__, fp, indent=4)
    with open(os.path.join(save_dir, "scaler.pkl"), "wb") as fp:
        pickle.dump(scaler, fp)

def main():
    args = parse_args()
    set_random_seed(args.seed)
    save_dir = os.path.join(DIR_MODELS, args.name)
    
    print("Loading data...")
    X_train, X_test, y_train, y_test, scaler = load_data(args.dataset_group, args.scale_method)
    
    print("Finding model...")
    _need_saving = True
    if os.path.exists(save_dir) and not args.retrain:
        import argparse
        model, scaler, args = load_model(save_dir)
        args = argparse.Namespace(**args)
        _need_saving = False
    else:
        os.makedirs(save_dir, exist_ok=True)
        print("Training model...")
        model = get_model(X_train)
        train_model(model, X_train, y_train, args)
        
        print("Calculating threshold...")
        args.threshold = threshold_opt_prec(y_train, model.predict(X_train), args.target_prec) if args.threshold_opt else 0.5
    
    print("Testing...")
    report = test_model(model, X_test, y_test, args)
    print(report)
    
    if _need_saving:
        print(f"Saving model to {save_dir}...")
        save_model(model, scaler, args, save_dir)

if __name__ == "__main__":
    main()