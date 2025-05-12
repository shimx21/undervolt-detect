from executable.rwvolt import RWVolt
from constants import DIR_EXECUTABLE
from subprocess import Popen, PIPE
import numpy as np
from io import BytesIO, StringIO

class VoltRecorder:
    def __init__(self, core):
        self.bind_core_ = core
    
    def _reader_cmd(self, n_reads, interval):
        return [
            "taskset",
            "-c",
            str(self.bind_core_),
            "python3",
            f"{DIR_EXECUTABLE}/reader.py",
            "--n_reads",
            str(n_reads),
            "--interval",
            str(interval)
        ]
    
    def record_once(self, n_reads, interval, flog = None):
        data = np.zeros(n_reads, dtype=np.int16)
        proc = Popen(
            self._reader_cmd(n_reads, interval),
            stdout=PIPE,
            stderr=flog
        )
        
        cnt = 0
        while proc.poll() is None:
            lines = proc.stdout.readlines()
            for line in lines:
                data[cnt] = int(line)
                cnt += 1
        # Remain data
        lines = proc.stdout.readlines()
        for line in lines:
            data[cnt] = int(line)
            cnt += 1
        assert cnt == n_reads
        proc.wait()

        return data
    
    # def record_batch(self, batch_size = 10_000, interval = 0, fout: BytesIO = None, flog: StringIO = None):
    #     data = np.zeros(batch_size, dtype=np.int16)
    #     proc = Popen(
    #         self._reader_cmd(batch_size, interval),
    #         stdout=PIPE,
    #         stderr=flog
    #     )
    #     cnt = 0
        
    #     while proc.poll() is None and cnt < batch_size:
    #         lines = proc.stdout.readlines()
    #         for line in lines:
    #             data[cnt] = int(line)
    #             cnt += 1
        
    #     return data
    
    # def stop(self):
    #     return
    