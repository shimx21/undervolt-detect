import subprocess
import time

if __name__ == "__main__":
    time_limit = 10  # seconds
    cnt = 0
    start = time.time()
    while time.time() - start < time_limit:
        subprocess.run(
            [
                "sudo",
                "rdmsr",
                "--all",
                "--bitfield",
                "47:32",
                "0x198"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        cnt += 1
    print(f"Total iterations: {cnt}")
    print(f"Time taken: {time.time() - start:.2f} seconds")
    print(f"Iterations per second: {cnt / (time.time() - start):.2f}")