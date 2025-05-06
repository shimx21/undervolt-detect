from backgroud import BackgroundProgramBase, SpecCPUBackground, OpenSSLBackground, MultiBackground, DisturberBackground
from executable.rwvolt import RWVolt
from subprocess import Popen, PIPE
import multiprocessing as mp
from typing import Optional, Union, Literal, List, Tuple, Dict
import json, os, glob
import numpy as np
import tqdm
from constants import DIR_EXECUTABLE, DIR_UTILS, DIR_LOG, DIR_DATASETS, DIR_CONFIG

def find_config(name):
    name += ".json" if "." not in name else ""
    path = ""
    for i in glob.iglob(os.path.join(DIR_CONFIG, "**", name), recursive=True):
        path = i
    return path

def all_configs():
    return glob.glob(os.path.join(DIR_CONFIG, "**", "*.json"))

class DatasetBuilder:
    _BACKGROUNDS: Dict[str, BackgroundProgramBase] = {
        "speccpu": SpecCPUBackground,
        "openssl": OpenSSLBackground,
    }
    _DATASET_DIR = DIR_DATASETS
    _POS_LABEL = "disturbed"
    _NEG_LABEL = "normal"
    _N_MAX_CORES = mp.cpu_count() - 2
    _SETTER_CORE = _N_MAX_CORES
    _READER_CORE = _SETTER_CORE + 1
    _LOG_DIR = DIR_LOG
    
    def __init__(
        self,
        name: str = "default",
        size: int = 100000,
        n_cores: int = 1,
        n_reads: int = 1000000,
        interval: int = 0,
        backgrounds: Dict[str, Dict] = {},
        disturber: Optional[Dict[str, List[int]]] = None
    ):
        self.name_ = name
        self.size_ = size
        self.n_cores_ = n_cores
        self.n_reads_ = n_reads
        self.interval_ = interval
        self.label_ = self._POS_LABEL if disturber is None else self._NEG_LABEL
        assert 1 <= n_cores <= self._N_MAX_CORES, ValueError(f"Number of cores should be between 1 and {self._N_MAX_CORES}")
        
        self.cores_ = list(range(0, self.n_cores_))
        self.rwvolt_ = RWVolt()
        
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
        self.reader_cmd_ = [
            "taskset",
            "-c",
            str(self._READER_CORE),
            "python3",
            f"{DIR_EXECUTABLE}/reader.py",
            "--n_reads",
            str(self.n_reads_),
            "--interval",
            str(self.interval_)
        ]
        
        # File paths
        self.target_ = os.path.join(self._DATASET_DIR, self.label_, self.name_)
        self.log_path_ = os.path.join(self._LOG_DIR, self.name_)
        
        os.makedirs(os.path.join(self._DATASET_DIR, self.label_), exist_ok=True)
        os.makedirs(self._LOG_DIR, exist_ok=True)
        # Bind main programme on last core
        self.rwvolt_.bind_core(self._SETTER_CORE)
        
    
    @classmethod
    def from_config(cls, path: str):
        with open(path) as fp:
            return cls(**json.load(fp))
    
    def _check_exist(self):
        return os.path.exists(self.target_ + ".pkl")
    
    def build(self, save = True, replace = False):
        if not replace and self._check_exist(): return np.load(self.target_)
        
        data = np.zeros((self.size_, self.n_reads_), dtype=np.int16)
        fp_log = open(self.log_path_, "w")
        
        # Start backgrounds
        self.backgrouds_.run()
        
        # Wait until all backgrounds are ready
        while not self.backgrouds_.ready(): ...
        
        for i in tqdm.tqdm(range(self.size_)):
            if self.disturber_:
                self.disturber_.run()
                while not self.disturber_.ready(): ...
            
            proc = Popen(
                self.reader_cmd_,
                stdout=PIPE,
                stderr=fp_log
            )
            
            cnt = 0
            while proc.poll() is None:
                line = proc.stdout.readline()
                if line:
                    data[i][cnt] = int(line)
                    cnt += 1
            
            if self.backgrouds_.finished(): break
            while not self.disturber_.finished():...
            
        self.backgrouds_.stop()
        fp_log.close()
        
        if save: np.save(self.target_, data)
        return data

def build_all(configs: List[str], save = True, replace = False):
    for config in configs:
        DatasetBuilder.from_config(config).build(save, replace)

def parse_args():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", type=str, default="default")
    parser.add_argument("-t", "--test", action="store_true", default=False)
    return parser.parse_args()

def main():
    args = parse_args()
    
    builder = DatasetBuilder.from_config(find_config(args.config))
    data = builder.build()
    
    if args.test:
        with open(".temp/test_dataset", "w") as fp:
            fp.write("\n".join([str(t) for t in data[0]]))
        p = Popen(["python3", f"{DIR_UTILS}/plot_voltage.py", ".temp/test_dataset", ".temp/temp.png"])
        p.wait()

if __name__ == "__main__":
    main()
    