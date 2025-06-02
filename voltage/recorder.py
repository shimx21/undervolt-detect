from rwvolt import RWVolt
from constants import DIR_EXECUTABLE
from subprocess import Popen, PIPE
import numpy as np
from io import TextIOWrapper, StringIO
import multiprocessing as mp
from multiprocessing.connection import Connection
import os
from threading import Timer
from typing import Callable, Any

class VoltRecorder:
    def __init__(self, proc_core, reader_core):
        self.proc_core_ = proc_core
        self.reader_core_ = reader_core
        
    def _read_timeout(self):
        raise TimeoutError("Read Pipe timeout!")
    
    def _check_flog(self, flog):
        sign = flog is None
        if sign: flog = open("/dev/null", "w")
        return flog, sign
    
    def _build_pipe(self):
        rp, wp = os.pipe()
        reader = os.fdopen(rp, "r")
        writer = os.fdopen(wp, "w")
        return reader, writer
    
    def _read_pipe(self, fp: TextIOWrapper, n_reads: int, dtype=np.int16, timeout = 10):
        data = np.zeros(n_reads, dtype=dtype)
        cnt = 0
        # Unstable
        while cnt < n_reads:
            line = fp.readline()
            data[cnt] = int(line)
            cnt += 1
        return data
    
    def record_once(self, n_reads, interval, flog = None):
        os.sched_setaffinity(0, {self.proc_core_})
        reader, writer = self._build_pipe()
        # Check flog
        flog, sign = self._check_flog(flog)
        
        proc = mp.Process(
            target=RWVolt.read_core_voltage,
            args=(0, n_reads, interval, writer, flog)
        )
        proc.start()
        os.sched_setaffinity(proc.pid, {self.reader_core_})
        
        data = self._read_pipe(reader, n_reads)
        proc.join()
        reader.close()
        writer.close()
        
        if sign: flog.close()

        return data

    def record_deal(self, n_reads = 10_000, interval = 0, dealer:Callable[[np.ndarray],Any] = lambda:None, flog: StringIO = None):
        os.sched_setaffinity(0, {self.proc_core_})
        reader, writer = self._build_pipe()
        # Check flog
        flog, sign = self._check_flog(flog)
        
        proc = mp.Process(
            target=RWVolt.read_core_voltage,
            # Infinite read
            args=(0, -1, interval, writer, flog)
        )
        proc.start()
        os.sched_setaffinity(proc.pid, {self.reader_core_})
        
        try:
            while True:
                data = self._read_pipe(reader, n_reads)
                dealer(data)
        except Exception as e:
            import traceback; traceback.print_exc(file=flog);
        finally:
            proc.kill()
        
    # def stop(self):
    #     return
    