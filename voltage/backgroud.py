from typing import Optional, Literal, Union, List, Tuple
import os
import subprocess, time, multiprocessing
from constants import DIR_EXECUTABLE

class BackgroundProgramBase:
    
    def _check_env(self) -> bool:
        raise NotImplementedError("Subclasses should implement this method.")
    
    def _check_and_set_cores(self, cores: Optional[List[None]] = None) -> int:
        self.n_total_cores_ = multiprocessing.cpu_count()
        cores = cores or list(range(self.n_total_cores_))
        
        assert self.n_total_cores_ > 0, "No CPU cores available"
        assert isinstance(cores, list), "Cores should be a list"
        assert all(isinstance(i, int) for i in cores), "Cores should be a list of integers"
        cores = list(set(cores))
        cores.sort()
        assert all(0 <= i < self.n_total_cores_ for i in cores), f"Cores id `{cores}` out of range"
        self.cores_ = cores
        
        # print(f"Total CPU cores: {self.n_total_cores_}")
        # print(f"Using CPU cores: {cores}")
    
    def _taskset_cmd(self) -> List[str]:
        return ["taskset", "-c", ','.join(map(str, self.cores_))]
    
    def _runner_cmd(self) -> List[str]:
        raise NotImplementedError("Subclasses should implement this method.")

    def _build_cmd(self) -> List[str]:
        return self._taskset_cmd() + self._runner_cmd()
    
    def __init__(
        self,
        method: Literal["all", "each"] = "all",
        cores: Optional[List[int]] = None,
        name: str = "default"
    ):
        self._check_env()
        self._check_and_set_cores(cores)
        self.method_ = method
        self.name_ = name
        
        self.subprocess_ = None
    
    def ready(self) -> bool:
        return True
    
    def run(
        self,
        # loop: Optional[int] = 1,
        # duration: Optional[int] = None,
    ):
        self.start_time_ = time.time()
        
        # Close all output
        # TODO: maybe add a log file
        self.subprocess_ = subprocess.Popen(
            self._build_cmd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    
    def stop(self):
        if self.subprocess_:
            self.subprocess_.terminate()
            self.subprocess_.wait()
    
    def finished(self) -> bool:
        return self.subprocess_ is None or self.subprocess_.poll() is not None
    
class SpecCPUBackground(BackgroundProgramBase):
    __DEFAULT_EVAL = "500.perlbench_r"
    __EXECUTABLE = "../spec2017/bin/runcpu"
    __INSTALLED_EVALS = [
        "500.perlbench_r",
        "502.gcc_r",
        "505.mcf_r",
        "520.omnetpp_r",
        "523.xalancbmk_r",
        "525.x264_r",
        "531.deepsjeng_r",
        "541.leela_r",
        "548.exchange2_r",
        "557.XZ_r",
        "intrate"
    ]
    def _check_env(self) -> bool:
        return "SPEC" in os.environ
    
    def __init__(
        self,
        method: Literal["all", "each"] = "all",
        cores: Optional[List[int]] = None,
        config: str = "gcc.cfg",
        targets: List[str] = [__DEFAULT_EVAL],
        name: str = "speccpu_default",
    ):
        super().__init__(
            method=method,
            cores=cores,
            name = name
        )
        self.config_ = config
        assert all(t in self.__INSTALLED_EVALS for t in targets), f"Invalid target: {targets}"
        self.targets_ = targets
        
        subprocess.run(
            self._runner_cmd("buildsetup"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def ready(self):
        # At least 5 seconds
        # TODO: More accurate etimation using pipe
        return time.time() - self.start_time_ > 5
    
    def _runner_cmd(self, action:str = "run") -> List[str]:
        return [
            self.__EXECUTABLE,
            f"--config={self.config_}",
            f"--action={action}",
            "--loose"
        ] + self.targets_

class OpenSSLBackground(BackgroundProgramBase):
    def _check_env(self) -> bool:
        try:
            # Check if OpenSSL is installed
            subprocess.run(
                ["openssl", "version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            # OpenSSL is not installed or not working
            print("OpenSSL is not installed or not working.")
            return False
    
    def __init__(
        self,
        method: Literal["all", "each"] = "all",
        cores: Optional[int] = None,
        name: str = "openssl_default",
    ):
        super().__init__(
            method=method,
            cores=cores,
            name=name
        )
    
    def ready(self):
        # At least 5 seconds
        return time.time() - self.start_time_ > 5
    
    def _runner_cmd(self) -> List[str]:
        # TODO: Add more options for OpenSSL
        return [
            "openssl",
            "speed",
            "-evp",
            "aes-128-cbc",
            "-multi",
            str(len(self.cores_)),
            "-time"
        ]

class DisturberBackground(BackgroundProgramBase):
    def _check_env(self) -> bool:
        # Check if the environment is set up for Disturber
        return True  # Placeholder for actual check
    
    def __init__(
        self,
        cores: Optional[List[int]] = None,
        set_method: str = "offset",
        # (k(ms), v(mV)) set voltage offset v mV after k ms, v=None for end
        periods: List[int] = [],
        values: List[int] = [], 
        name: str = "disturber_default",
        executable: str = f"{DIR_EXECUTABLE}/setter.py"
    ):
        super().__init__(
            method="all",
            cores=cores,
            name=name
        )
        self.periods_ = periods
        self.values_ = values
        self.exec_ = executable
        self.set_method_ = set_method
    
    def _runner_cmd(self) -> List[str]:
        return [
            "python3",
            self.exec_,
            "--method",
            self.set_method_,
            "--periods",
            *[str(_) for _ in self.periods_],
            "--values",
            *[str(_) for _ in self.values_],
        ]

class MultiBackground:
    def __init__(self, *backgrounds: BackgroundProgramBase):
        self.backgrounds_ = backgrounds
    
    def run(self):
        for bg in self.backgrounds_:
            bg.run()
    
    def stop(self):
        for bg in self.backgrounds_:
            bg.stop()
    
    def ready(self):
        return all(bg.ready() for bg in self.backgrounds_)
    
    def finished(self) -> bool:
        return any(bg.finished() for bg in self.backgrounds_)


if __name__ == "__main__":
    # Example usage
    print("Running example...")
    spec_cpu = SpecCPUBackground(method="all", cores=[0, 1], config="gcc.cfg", targets=["500.perlbench_r"])
    spec_cpu.run()
    time.sleep(5)
    spec_cpu.stop()
    print("Finished:", spec_cpu.finished())
    
    openssl = OpenSSLBackground(method="all", cores=[0, 1])
    openssl.run()
    time.sleep(5)
    openssl.stop()
    print("Finished:", openssl.finished())
    print("Example finished.")
    
    bg = DisturberBackground([0], periods=[0, 4000, 4000, 4000], values=[200, 320, 50, 200])
    bg.run()
    time.sleep(15)
    bg.stop()
    
