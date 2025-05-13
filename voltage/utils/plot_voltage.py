import pandas as pd
import matplotlib.pyplot as plt
import sys

def plot_voltage(data, save_pth):
    scaled_data = data / 8192

    plt.figure(figsize=(10, 6))
    plt.plot(scaled_data, label='Voltage (V)', color='blue')
    plt.xlabel('Data Point Index')
    plt.ylabel('Voltage (V)')
    plt.title('Voltage Waveform')
    plt.legend()
    plt.grid()
    plt.tight_layout()
    plt.savefig(save_pth)
    plt.close()
