import pandas as pd
import matplotlib.pyplot as plt
import sys

assert sys.argv.__len__() == 3
# 读取 CSV 文件，数据在第一列，文件名为 data.csv
file_name = sys.argv[1]

# 读取数据，CSV 文件只有一列数据
try:
    data = pd.read_csv(file_name, header=None)
except FileNotFoundError:
    raise FileNotFoundError(f"文件 '{file_name}' 未找到，请检查文件路径。")

# 获取数据并进行处理
data_points = data[0][20000:180000]  # 使用第0列的数据
scaled_data = data_points / 8192  # 每个数据点除以 8192

# 绘制折线图
plt.figure(figsize=(10, 6))
plt.plot(scaled_data, label='Voltage (V)', color='blue')
plt.xlabel('Data Point Index')
plt.ylabel('Voltage (V)')
plt.title('Voltage Waveform')
plt.legend()
plt.grid()
plt.tight_layout()
plt.savefig(sys.argv[2])
