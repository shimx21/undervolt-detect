import pandas as pd
import matplotlib.pyplot as plt
import sys


def plot_voltage(data, title, ax: plt.Axes = plt, fontsize=15):
    scaled_data = data / 8192
    
    plt.rcParams.update({'font.size': fontsize})
    ax.tick_params(labelsize=fontsize)
    
    ax.plot(scaled_data, label='Core Voltage Sequence', color='blue')
    ax.set_xlabel('Sequnece Index', fontsize=fontsize)
    ax.set_ylabel('Voltage (V)', fontsize=fontsize)
    ax.set_title(title, fontdict={"fontsize": fontsize})
    ax.legend()
    ax.grid()
