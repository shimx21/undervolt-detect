from rwvolt import RWVolt
import argparse, time, sys

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cores", nargs="+", type=list, default=[0])
    parser.add_argument("-m", "--method", type=str, default="offset")
    parser.add_argument("-p", "--periods", type=int, nargs="+", required=True)
    parser.add_argument("-v", "--values", type=int, nargs="+", required=True)
    return parser.parse_args()

def seq_setter(func, cores, periods, values, output = sys.stderr):
    st = time.time()
    print(periods, values)
    for p, v in zip(periods, values):
        while 1000*(time.time() - st) < p: ...
        for core in cores: func(core, v, output)
        st = time.time()

def main():
    rwvolt = RWVolt()
    args = parse_args()
    config = args.__dict__
    method = config.pop("method")
    func = rwvolt.set_core_voltage if method == "set" else rwvolt.offset_core_voltage
    seq_setter(func, **config)

# subprocess only
main()
