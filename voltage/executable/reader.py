from rwvolt import RWVolt
import argparse, time, sys

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--core", type=int, default=0)
    parser.add_argument("-n", "--n_reads", type=int)
    parser.add_argument("-i", "--interval", type=int)
    return parser.parse_args()

def main():
    args = parse_args()
    RWVolt.read_core_voltage(args.core, args.n_reads, args.interval)

# subprocess only
main()
