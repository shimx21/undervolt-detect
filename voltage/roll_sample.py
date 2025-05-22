import numpy as np
from build_dataset import DatasetBuilder, DatasetGroup
from constants import *
from utils.plot_voltage import plot_voltage

USED_CONFIGS = [
    "normal_spec",
    "normal_openssl",
    "normal_rest",
    "normal_multi",
    "normal_mix",
    "disturbed_t1_spec",
    # "template"
]

if __name__ == "__main__":
    data, labels = DatasetGroup.load_from("datasets/group/default")
    n_sets = len(USED_CONFIGS)
    n_single = data.shape[0] // n_sets
    
    while not input():
        index = np.random.randint(data.shape[0])
        sample = data[index]
        plot_voltage(sample, ".log/displayed.png")
        print(f"Set: {USED_CONFIGS[index//n_single]}")
        