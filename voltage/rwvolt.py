from ctypes import CDLL, c_int, POINTER
from typing import TextIO
from sys import stdout, stderr

class RWVolt:
    def __init__(
        self,
        lib_path: str = 'rwvolt/librwvolt.so'
    ):
        # Load the shared library
        self.lib = CDLL(lib_path)
        self.lib.read_core_voltage.argtypes = [c_int, c_int, c_int, c_int, c_int]
        self.lib.read_core_voltage.restype = c_int
        
        self.lib.offset_core_voltage.argtypes = [c_int, c_int, c_int]
        self.lib.offset_core_voltage.restype = c_int
        
        self.lib.set_core_voltage.argtypes = [c_int, c_int, c_int]
        self.lib.set_core_voltage.restype = c_int

    def read_core_voltage(
        self, 
        core_id: int,
        read_num: int,
        interval: int = 0,
        fpout: TextIO = stdout,
        fplog: TextIO = stderr
    ) -> int:
        return self.lib.read_core_voltage(
            core_id,
            read_num,
            interval,
            fpout.fileno(),
            fplog.fileno()
        )

    def offset_core_voltage(self, core_id: int, offset: int, fplog: TextIO = stderr) -> int:
        return self.lib.offset_core_voltage(core_id, offset, fplog.fileno())
    
    
    def set_core_voltage(self, core_id: int, target: int, fplog: TextIO = stderr) -> int:
        return self.lib.set_core_voltage(core_id, target, fplog.fileno())
    
if __name__ == "__main__":
    import sys
    rwvolt = RWVolt()
    target = int(sys.argv[1])
    # Offset core voltage
    result = rwvolt.offset_core_voltage(0, target)
    print(f"Offset Core Voltage Result: {result}")