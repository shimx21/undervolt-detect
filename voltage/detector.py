from train import load_model
from rwvolt import RWVolt
from recorder import VoltRecorder
import multiprocessing as mp
import sys

class VoltDetector:
    _N_MAX_CORES = mp.cpu_count() - 2
    _DEALER_CORE = _N_MAX_CORES
    _READER_CORE = _DEALER_CORE + 1
    def __init__(self, model_dir: str, proc_core: int = _DEALER_CORE, reader_core: int = _READER_CORE):
        self.recorder_ = VoltRecorder(proc_core, reader_core)
        model, scaler, args = load_model(model_dir)
        self.model_ = model
        self.scaler_ = scaler
        self.args_ = args
        self.n_reads_ = model.input_shape[1]
    
    def _dealer(self, data):
        result = self.model_.predict(
            self.scaler_.transform(data.reshape(1,-1)),
            verbose=2
        )
        if result > 0.5:
            print("Alarm!!!!")
            raise OSError("Being attacked!")
    
    def start(self):
        self.recorder_.record_deal(self.n_reads_, 0, self._dealer, sys.stderr)
        


def parse_args():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-m", "--model", type=str, default="models/standard")
    return parser.parse_args()

def main():
    args = parse_args()
    detector = VoltDetector(args.model)
    detector.start()
    
if __name__ == "__main__":
    main()
    