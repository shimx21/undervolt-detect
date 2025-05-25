import multiprocessing as mp
import sys, os, time, random
from detector import VoltDetector
from setter import seq_setter
from rwvolt import RWVolt
from enum import Enum, auto

class TestResult(Enum):
    TP = 0
    FP = 1
    FN = 2
    TN = 3
    UNDEFINED = auto()

# False Positive in 10 minutes
def test_false_positive(detector, test_time = 10):
    proc = mp.Process(target=detector.start)
    proc.start()
    proc.join(timeout=test_time)
    if proc.is_alive():
        proc.kill()
        proc.join()
        return TestResult.TN
    else:
        return TestResult.FP

def test_true_positive(detector, random_start = 10, retry_gap = 2):
    """Test if the detector can detect a voltage change."""
    proc = mp.Process(target=detector.start)
    dstb = mp.Process(target=seq_setter, args=(RWVolt.offset_core_voltage, [0], [0,190,10,10],[400,520,370,400]))
    wt = random.randint(1, random_start)
    
    proc.start()
    proc.join(timeout=wt)
    
    if not proc.is_alive(): return TestResult.FP, 0
    i = 0
    while proc.is_alive():
        i += 1
        print(f"Attempt {i}...")
        dstb.run()
        time.sleep(retry_gap)
    
    return (TestResult.TP if i == 1 else TestResult.FN), i
    

def main():
    random.seed(42)
    model, tol = sys.argv[1], sys.argv[2]
    detector = VoltDetector(model, tol)
    N = 100
    
    print("Test 1: False Positive")
    cnt_false_positive = 0
    for i in range(N):
        print("-"*40 + f"Test {i}" + "-"*40)
        res = test_false_positive(detector)
        print(f"Test {i} finished: {res.name}")
        cnt_false_positive += res is TestResult.FP
    print(f"False positive rate: {cnt_false_positive / N:.2%}")
    
    print("Test 2: False Negative")
    cnt_false_positive = 0
    cnt_false_negative = 0
    cnt_retry = []
    for i in range(N):
        print("-"*40 + f"Test {i}" + "-"*40)
        res, times = test_true_positive(detector)
        print(f"Test {i} finished: {res}")
        cnt_false_negative += res is TestResult.FN
        cnt_false_positive += res is TestResult.FP
        cnt_retry.append(times)
    print(f"False negative rate: {cnt_false_negative / N:.2%}")
    print(f"False positive rate: {cnt_false_positive / N:.2%}")
    print(f"Average retry times: {sum(cnt_retry) / len(cnt_retry):.2f}")
    
    
# Positive in 10 minutes
if __name__ == "__main__":
    main()