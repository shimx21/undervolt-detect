import numpy as np
from build_dataset import DatasetBuilder, DatasetGroup
from constants import *
from utils.plot_voltage import plot_voltage
import matplotlib.pyplot as plt

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
    data, labels = DatasetGroup.load_from("datasets/build/group/transform")
    n_sets = len(USED_CONFIGS)
    n_single = data.shape[0] // n_sets
    
    fig, axs = plt.subplots((n_sets+1)//2, 2, figsize=(16, (n_sets+1)//2*6))
    for i in range(n_sets):
        index = np.random.randint(n_single)
        sample = data[i * n_single + index]
        plot_voltage(sample, USED_CONFIGS[i], ax=axs[i//2, i%2])
    
    fig.tight_layout()
    fig.savefig(".log/sample.png")
    
    while not input():
        index = np.random.randint(data.shape[0])
        sample = data[index]
        plt.close('all')
        fig, ax = plt.subplots(figsize=(10, 6))
        plot_voltage(sample, "random sample", ax=ax)
        plt.savefig(f".log/sample_{index}.png")
        print(f"Set: {USED_CONFIGS[index//n_single]}, Label: {labels[index]}")
        