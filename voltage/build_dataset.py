from backgroud import BackgroundProgramBase, SpecCPUBackground, OpenSSLBackground, MultiBackground, DisturberBackground
from executable.rwvolt import RWVolt
from subprocess import Popen, PIPE, DEVNULL
import multiprocessing as mp
from typing import Optional, Union, Literal, List, Tuple, Dict
import json, os, glob
import numpy as np
import tqdm
from constants import *
from recorder import VoltRecorder

def find_config(name):
    name += ".json" if "." not in name else ""
    for path in glob.iglob(os.path.join(DIR_DATASETS_CONFIG, "**", name), recursive=True):
        return path

def all_configs():
    return glob.glob(os.path.join(DIR_DATASETS_CONFIG, "**", "*.json"))

class DatasetBuilder:
    _BACKGROUNDS: Dict[str, BackgroundProgramBase] = {
        "speccpu": SpecCPUBackground,
        "openssl": OpenSSLBackground,
    }
    _DATASET_DIR = DIR_DATASETS_BUILD
    _POS_LABEL = POS_LABEL
    _NEG_LABEL = NEG_LABEL
    _N_MAX_CORES = mp.cpu_count() - 2
    _SETTER_CORE = _N_MAX_CORES
    _READER_CORE = _SETTER_CORE + 1
    _LOG_DIR = DIR_LOG
    
    def _reset_volt(self):
        self.rwvolt_.offset_core_voltage(0, self.base_, self.fp_log_)
    
    def __init__(
        self,
        name: str = "default",
        size: int = 100000,
        n_cores: int = 1,
        n_reads: int = 1000000,
        interval: int = 0,
        backgrounds: Dict[str, Dict] = {},
        disturber: Optional[Dict[str, List[int]]] = None,
        on_finished: Literal["revert", "repeat", "termiate"] = "repeat",
        base: int = 400
    ):
        self.name_ = name
        self.size_ = size
        self.n_cores_ = n_cores
        self.n_reads_ = n_reads
        self.interval_ = interval
        self.label_ = self._POS_LABEL if disturber is not None else self._NEG_LABEL
        self.on_finished_ = on_finished
        assert 1 <= n_cores <= self._N_MAX_CORES, ValueError(f"Number of cores should be between 1 and {self._N_MAX_CORES}")
        
        self.cores_ = list(range(0, self.n_cores_))
        self.rwvolt_ = RWVolt()
        self.base_ = base
        
        # Backgrounds
        self.backgrouds_ = MultiBackground(
            *[
                self._BACKGROUNDS[k](
                    cores=self.cores_,
                    **kwargs,
                )
                for k, kwargs in backgrounds.items()
            ]
        )
        self.disturber_ = DisturberBackground(cores=[self._N_MAX_CORES], **disturber) if disturber else None
        
        # Reader
        self.recorder_ = VoltRecorder(self._READER_CORE)

        # File paths
        self.target_ = os.path.join(self._DATASET_DIR, self.label_, self.name_)
        self.log_path_ = os.path.join(self._LOG_DIR, self.name_)
        self.fp_log_ = None
        
        os.makedirs(os.path.join(self._DATASET_DIR, self.label_), exist_ok=True)
        os.makedirs(self._LOG_DIR, exist_ok=True)
        # Bind main programme on last core
        self.rwvolt_.bind_core(self._SETTER_CORE)
        
    
    @classmethod
    def from_config(cls, path: str):
        with open(path) as fp:
            return cls(**json.load(fp))
    
    def _check_exist(self):
        return os.path.exists(self.target_ + ".npy")
    
    def build(self, save = True, replace = False):
        # If exist and not replace, skip
        if not replace and self._check_exist():
            return np.load(self.target_ + ".npy"), self.label_
        
        data = np.zeros((self.size_, self.n_reads_), dtype=np.int16)
        
        self.fp_log_ = open(self.log_path_, "w")

        # Set base voltage
        self._reset_volt()
        
        # Start backgrounds
        self.backgrouds_.run()
        
        # Wait until all backgrounds are ready
        while not self.backgrouds_.ready(): ...
        
        for i in tqdm.tqdm(range(self.size_)):
            if self.disturber_:
                self.disturber_.run()
                while not self.disturber_.ready(): ...
            
            data[i] = self.recorder_.record_once(self.n_reads_, self.interval_, self.fp_log_)
            
            if self.backgrouds_.finished():
                # On finish
                if self.on_finished_ == "repeat":
                    # self.backgrouds_.stop()
                    for b in self.backgrouds_.backgrounds_:
                        if b.finished(): b.run()
                elif self.on_finished_ == "revert":
                    # self.backgrouds_.stop()
                    for b in self.backgrouds_.backgrounds_:
                        if b.finished(): b.run()
                    i -= 1
                elif self.on_finished_ == "terminate":
                    break
                
            if self.disturber_ is not None:
                while not self.disturber_.finished():...
            
        self.backgrouds_.stop()
        self._reset_volt()
        self.fp_log_.close
        
        if save: np.save(self.target_, data)
        return data, self.label_

def build_all(configs: List[str], save = True, replace = False):
    datasets = []
    labels = []
    for config in configs:
        cfg_pth = find_config(config)
        if cfg_pth is None:
            print(f"Config `{config}` not found, skipped...")
            continue
        print(f"Building config `{config}`...")
        data, label = DatasetBuilder.from_config(cfg_pth).build(save, replace)
        datasets.append(data)
        labels.append(np.ones(data.shape[0], dtype=np.bool_) * (label == "disturbed"))
    
    RWVolt().unbind()
    return np.concatenate(datasets, axis=0), np.concatenate(labels, axis=0)

def parse_args():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", type=str, default="template")
    parser.add_argument("-r", "--replace", action="store_true", default=False)
    parser.add_argument("-t", "--test", action="store_true", default=False)
    return parser.parse_args()

def main():
    args = parse_args()
    
    builder = DatasetBuilder.from_config(find_config(args.config))
    data = builder.build(replace=args.replace)
    
    if args.test:
        with open(".temp/test_dataset", "w") as fp:
            fp.write("\n".join([str(t) for t in data[0]]))
        p = Popen(["python3", f"{DIR_UTILS}/plot_voltage.py", ".temp/test_dataset", ".temp/temp.png"])
        p.wait()

if __name__ == "__main__":
    main()
    