from backgroud import BackgroundProgramBase, SpecCPUBackground, OpenSSLBackground, MultiBackground, DisturberBackground
from rwvolt import RWVolt
from subprocess import Popen, PIPE, DEVNULL
import multiprocessing as mp
from typing import Optional, Union, Literal, List, Tuple, Dict
import json, os, glob
import numpy as np
import tqdm, traceback
from constants import *
from recorder import VoltRecorder
from utils.augment import AugmentBase
from collections import OrderedDict

def find_config(name, dir: str = DIR_DATASETS_CONFIG):
    name += ".json" if "." not in name else ""
    for path in glob.iglob(os.path.join(dir, "**", name), recursive=True):
        return path

class DatasetBuilder:
    _BACKGROUNDS: Dict[str, BackgroundProgramBase] = {
        "speccpu": SpecCPUBackground,
        "openssl": OpenSSLBackground,
    }
    _DATASET_DIR = DIR_DATASETS_BUILD
    _POS_LABEL = POS_LABEL
    _NEG_LABEL = NEG_LABEL
    _N_MAX_CORES = mp.cpu_count() - 3
    _SETTER_CORE = _N_MAX_CORES
    _READER_CORE = _SETTER_CORE + 1
    _RECODER_CORE = _READER_CORE + 1
    _LOG_DIR = DIR_LOG
    
    def _reset_volt(self):
        RWVolt.offset_core_voltage(0, self.base_, self.fp_log_)
    
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
        self.disturber_ = DisturberBackground(cores=[self._SETTER_CORE], **disturber) if disturber else None
        
        # Reader
        self.recorder_ = VoltRecorder(self._RECODER_CORE, self._READER_CORE)

        # File paths
        self.target_ = os.path.join(self._DATASET_DIR, self.label_, self.name_)
        self.log_path_ = os.path.join(self._LOG_DIR, self.name_)
        self.fp_log_ = None
        
        os.makedirs(os.path.join(self._DATASET_DIR, self.label_), exist_ok=True)
        os.makedirs(self._LOG_DIR, exist_ok=True)
        # Bind main programme on last core
        os.sched_setaffinity(0, {self._SETTER_CORE})
        
    
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
        try:
            finished = False
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
            finished = True
        except Exception as e:
            self.fp_log_.write(traceback.format_exc())
        finally:
            self.backgrouds_.stop()
            if self.disturber_: self.disturber_.stop()
        self._reset_volt()
        self.fp_log_.close()
        
        if save and finished: np.save(self.target_, data)
        return data, self.label_

    @classmethod
    def build_all(cls, configs: List[str], save = True, replace = False):
        datasets = []
        labels = []
        for config in configs:
            cfg_pth = find_config(config)
            if cfg_pth is None:
                print(f"Config `{config}` not found, skipped...")
                continue
            print(f"Building config `{config}`...")
            data, label = cls.from_config(cfg_pth).build(save, replace)
            datasets.append(data)
            labels.append(np.ones(data.shape[0], dtype=np.bool_) * (label == cls._POS_LABEL))
        
        RWVolt.unbind()
        return np.concatenate(datasets, axis=0), np.concatenate(labels, axis=0)

class DatasetGroup:
    _TARGET_DIR = os.path.join(DIR_DATASETS_BUILD, "group")
    _NAME_DATA = "data"
    _NAME_LABELS = "labels"
    def __init__(
        self,
        name: str,
        configs: List[str],
        augment: Optional[AugmentBase]
    ):
        self.name_ = name
        self.configs_ = configs
        self.augment_ = augment
        self.target_dir_ = os.path.join(self._TARGET_DIR, name)
        os.makedirs(self.target_dir_, exist_ok=True)
        self.target_data_ = os.path.join(self.target_dir_, self._NAME_DATA)
        self.target_labels_ = os.path.join(self.target_dir_, self._NAME_LABELS)
    
    def build(self, save = True, replace = False):
        X, y = DatasetBuilder.build_all(self.configs_, save, replace)
        X, y = self.augment_.apply(X, y)
        if save:
            np.save(self.target_data_  , X)
            np.save(self.target_labels_, y)
        return X, y
    
    @classmethod
    def from_config(cls, path: str):
        with open(path) as fp:
            config: OrderedDict = json.load(fp, object_pairs_hook=OrderedDict)
        aug_config = config.pop("augment", None)
        augment = aug_config and AugmentBase.from_config(aug_config)
        return cls(**config, augment=augment)
    
    @classmethod
    def load_from(cls, dir):
        data_pth = os.path.join(dir, cls._NAME_DATA + ".npy")
        label_pth = os.path.join(dir, cls._NAME_LABELS + ".npy")
        return np.load(data_pth), np.load(label_pth)

def parse_args():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-s", "--seed", type=int, default=42)
    parser.add_argument("-c", "--config", type=str, default="template")
    parser.add_argument("-g", "--group", action="store_true", default=False)
    parser.add_argument("-r", "--replace", action="store_true", default=False)
    parser.add_argument("-t", "--test", action="store_true", default=False)
    return parser.parse_args()

def main():
    args = parse_args()
    
    if args.group:
        builder = DatasetGroup.from_config(find_config(args.config, DIR_DATASETS_GROUP))
    else:
        builder = DatasetBuilder.from_config(find_config(args.config))
    data, label = builder.build(replace=args.replace)
    
    if args.test:
        print("Save figure...")
        sample = data[0]
        from utils.plot_voltage import plot_voltage
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(10, 6))
        plot_voltage(sample, "sample", ax=ax)
        fig.savefig(".log/build_sample.png")
    
    # command line
    while 1:
        cmd = input(">>> ")
        try:
            exec(cmd)
        except EOFError:
            return
        except Exception as e:
            traceback.print_exc()

if __name__ == "__main__":
    main()
    