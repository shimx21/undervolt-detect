from train import load_model
from rwvolt import RWVolt
from recorder import VoltRecorder
import multiprocessing as mp
import sys, keras
import numpy as np
from utils.plot_voltage import plot_voltage
import matplotlib.pyplot as plt

class VoltDetector:
    _N_MAX_CORES = mp.cpu_count() - 2
    _DEALER_CORE = _N_MAX_CORES
    _READER_CORE = _DEALER_CORE + 1
    def __init__(self, model_dir: str, threshold = 0.5, n_windows = 10, tol = 2, proc_core: int = _DEALER_CORE, reader_core: int = _READER_CORE, test = False):
        """Initialize the VoltDetector with a model directory, threshold, fold, and tolerance.
        Args:
            model_dir (str): Directory containing the model files.
            threshold (float): Threshold for volt detection model output.
            n_windows (int): Number of sliding windows for data predicting, the comming slide will replace the first slide for next predict.
            tol (int): Tolerance truth for the alarm, in order to avoid error.
            proc_core (int): Core ID for data processing.
            reader_core (int): Core ID for reading data.
        """
        self.recorder_ = VoltRecorder(proc_core, reader_core)
        model, scaler, args = load_model(model_dir)
        self.model_: keras.models.Model = model
        self.scaler_ = scaler
        self.args_ = args
        self.n_reads_ = model.input_shape[1]
        self.threshold_ = threshold
        
        self.n_windows_ = n_windows
        assert self.n_reads_ % n_windows == 0, ValueError(f"Number of reads {self.n_reads_} should be divisible by fold {n_windows}.")
        self.tol_ = tol
        
        self.window_size_ = (self.n_reads_ + self.n_windows_ - 1) // self.n_windows_
        
        self.buffer_ = None
        self.record_ = None
        self.is_test_ = test
    
    def _dealer(self, data):
        if self.buffer_.shape[1] < self.n_reads_:
            self.buffer_ = np.hstack((self.buffer_, data.reshape(1,-1)))
            if self.buffer_.shape[1] > self.n_reads_:
                self.buffer_ = self.buffer_[:,-self.n_reads_:]
            return
        self.cnt_ += 1
        self.buffer_ = np.hstack((self.buffer_[:,self.window_size_:], data.reshape(1,-1)))
        
        result = self.model_.predict(
            self.scaler_.transform(self.buffer_),
            verbose=0
        )[0][0]
        
        if self.is_test_:
            import os
            os.makedirs(".log/temp", exist_ok=True)
            with open(".log/temp/result.txt", "a") as f:
                f.write(f"Test predict {self.cnt_: 4} {result}\n")
            fig, ax = plt.subplots(figsize=(10, 5))
            plot_voltage(self.buffer_[0], f"volt_detected_{self.cnt_}", ax)
            fig.savefig(f".log/temp/volt_detected_{self.cnt_}.png")
            plt.close()
        
        # slide
        self.record_ = np.roll(self.record_, -1)
        self.record_[-1] = int(result > self.threshold_)
        
        if self.record_.sum() > self.tol_:
            print("Alarm!!!!")
            raise OSError("Being attacked!")
    
    def start(self):
        self.buffer_ = np.zeros((1, 0),dtype=np.int16)
        self.record_ = np.zeros((self.n_windows_,), dtype=np.int8)
        self.cnt_ = 0
        self.recorder_.record_deal(self.window_size_, 0, self._dealer, sys.stderr)


def parse_args():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-m", "--model", type=str, default="models/standard")
    parser.add_argument("-t", "--threshold", type=float, default=0.7, help="Threshold for the volt detection model output.")
    parser.add_argument("-n", "--n_windows", type=int, default=10, help="Number of sliding windows for data predicting.")
    parser.add_argument("-a", "--tol", type=int, default=8, help="Tolerance for the alarm, in order to avoid error.")
    return parser.parse_args()

def main():
    args = parse_args()
    detector = VoltDetector(args.model, args.threshold, args.n_windows, args.tol)
    detector.start()
    
if __name__ == "__main__":
    main()
    