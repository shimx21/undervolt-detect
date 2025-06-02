import multiprocessing as mp
import sys, os, time, random
from detector import VoltDetector
from setter import seq_setter
from rwvolt import RWVolt
from enum import Enum, auto
from utils.plot_voltage import plot_voltage

class TestResult(Enum):
    TP = 0
    FP = 1
    FN = 2
    TN = 3
    UNDEFINED = auto()

def detector_process_entry(model, threshold, n_windows, tol, test):
    detector = VoltDetector(model, threshold, n_windows, tol, test=test)
    detector.start()

# False Positive in 10 minutes
def test_false_positive(detector_args, test_time = 10):
    proc = mp.Process(target=detector_process_entry, args=detector_args)
    proc.start()
    
    st = time.time()
    proc.join(timeout=test_time)
    
    if proc.is_alive():
        proc.kill()
        proc.join()
        return TestResult.TN
    else:
        return TestResult.FP

def test_true_positive(detector_args, random_start = 10, retry_gap = 2, max_attempts = 5):
    """Test if the detector can detect a voltage change."""
    from backgroud import SpecCPUBackground, DisturberBackground
    proc = mp.Process(target=detector_process_entry, args=detector_args)
    background = SpecCPUBackground(cores=[0])
    background.run()
    while not background.ready(): time.sleep(0.1)
    
    # dstb = mp.Process(target=seq_setter, args=(RWVolt.offset_core_voltage, [0], [0,190,10,10],[400,520,370,400]))
    dstb = DisturberBackground(cores=[1], periods=[0, 190, 10, 10], values=[400, 520, 370, 400])
    wt = random.randint(1, random_start)
    
    proc.start()
    st = time.time()
    proc.join(timeout=wt)
    
    if not proc.is_alive(): return TestResult.FP, 0
    i = 0
    while proc.is_alive():
        i += 1
        print(f"Attempt {i}...")
        
        dstb.run()
        while not dstb.finished(): ...
        time.sleep(0.5)
        
        if background.finished():
            print("Background finished, retrying...")
            background.run()
            while not background.ready(): time.sleep(0.1)
        if i >= max_attempts:
            print("Max attempts reached, stopping...")
            proc.kill()
            background.stop()
            return TestResult.FN, i
            
        time.sleep(retry_gap)
    
    return (TestResult.TP if i == 1 else TestResult.FN), i
    
def parse_args():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("-N", "--n_rounds", type=int, default=100, help="Number of rounds for the test.")
    parser.add_argument("-m", "--model", type=str, default="models/standard")
    parser.add_argument("-t", "--threshold", type=float, default=0.5, help="Threshold for the volt detection model output.")
    parser.add_argument("-n", "--n_windows", type=int, default=10, help="Number of sliding windows for data predicting.")
    parser.add_argument("-a", "--tol", type=int, default=8, help="Tolerance for the alarm, in order to avoid error.")
    parser.add_argument("-s", "--tests", type=int, nargs="+", default=[0,1])
    
    parser.add_argument("-l", "--log", action="store_true", default=False)
    
    return parser.parse_args()

def false_positive_rate(detector_args, n_rounds=100, test_time=10):
    """Calculate the false positive rate."""
    cnt_false_positive = 0
    try:
        for i in range(n_rounds):
            print("-"*40 + f"Test {i}" + "-"*40)
            res = test_false_positive(detector_args, test_time)
            print(f"Test {i} finished: {res.name}")
            cnt_false_positive += res is TestResult.FP
    except KeyboardInterrupt as e:
        ...
    finally:
        fpr = cnt_false_positive / i
        print(f"False positive rate: {fpr:.2%}")
        return {"false_positive_rate": fpr}

def true_positive_rate(detector_args, n_rounds=100, random_start=10, retry_gap=2, max_attempts=5):
    cnt_false_positive = 0
    cnt_false_negative = 0
    cnt_retry = []
    try:
        for i in range(n_rounds):
            print("-"*40 + f"Test {i}" + "-"*40)
            res, times = test_true_positive(detector_args, random_start, retry_gap, max_attempts)
            print(f"Test {i} finished: {res}")
            cnt_false_negative += res is TestResult.FN
            cnt_false_positive += res is TestResult.FP
            cnt_retry.append(times)
    
    except KeyboardInterrupt as e:
        ...
    finally:
        print(f"False negative rate: {cnt_false_negative / len(cnt_retry):.2%}")
        print(f"False positive rate: {cnt_false_positive / len(cnt_retry):.2%}")
        print(f"Average retry times: {sum(cnt_retry) / len(cnt_retry):.2f}")
        return {
            "false_negative_rate": cnt_false_negative / len(cnt_retry),
            "false_positive_rate": cnt_false_positive / len(cnt_retry),
            "average_retry_times": sum(cnt_retry) / len(cnt_retry)
        }
    
TestList = [
    false_positive_rate,
    true_positive_rate
]

def main():
    random.seed(42)
    args = parse_args()
    
    detector_args = [args.model, args.threshold, args.n_windows, args.tol, args.log]
    N = args.n_rounds
    
    results = {}
    for test in args.tests:
        if test < 0 or test >= len(TestList):
            print(f"Test {test} not found.")
            continue
        print(f"Running test {test}...")
        result = TestList[test](detector_args, n_rounds=N)
        results.update(result)
    
    import json
    print(json.dumps(results, indent=4))
    import json
    with open(f".log/{args.model}.json", "w") as fp:
        json.dump(results, fp, indent=True)
    
# Positive in 10 minutes
if __name__ == "__main__":
    main()