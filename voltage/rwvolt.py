from ctypes import CDLL, c_int, POINTER
from typing import TextIO
from sys import stdout, stderr
from constants import *

class RWVolt:
    _LIB = None
    
    @classmethod
    def build(cls, path = PATH_LIB):
        cls._LIB = CDLL(path)
        
        # cls._LIB.bind_core.argtypes = [c_int]
        # cls._LIB.bind_core.restype = None
        
        cls._LIB.unbind.argtypes = []
        cls._LIB.unbind.restype = None
        
        cls._LIB.read_core_voltage.argtypes = [c_int, c_int, c_int, c_int, c_int]
        cls._LIB.read_core_voltage.restype = c_int
        
        cls._LIB.offset_core_voltage.argtypes = [c_int, c_int, c_int]
        cls._LIB.offset_core_voltage.restype = c_int
        
        cls._LIB.set_core_voltage.argtypes = [c_int, c_int, c_int]
        cls._LIB.set_core_voltage.restype = c_int

    @classmethod
    def read_core_voltage(
        cls, 
        core_id: int,
        read_num: int,
        interval: int = 0,
        fpout: TextIO = stdout,
        fplog: TextIO = stderr
    ) -> int:
        return cls._LIB.read_core_voltage(
            core_id,
            read_num,
            interval,
            fpout.fileno(),
            fplog.fileno()
        )
    
    # @classmethod
    # def bind_core(cls, core_id) -> None:
    #     cls._LIB.bind_core(core_id)
    
    @classmethod
    def unbind(cls) -> None:
        cls._LIB.unbind()

    @classmethod
    def offset_core_voltage(cls, core_id: int, offset: int, fplog: TextIO = stderr) -> int:
        return cls._LIB.offset_core_voltage(core_id, offset, fplog.fileno())
    
    
    @classmethod
    def set_core_voltage(cls, core_id: int, target: int, fplog: TextIO = stderr) -> int:
        return cls._LIB.set_core_voltage(core_id, target, fplog.fileno())

# Default
RWVolt.build()

if __name__ == "__main__":
    import sys
    target = int(sys.argv[1])
    # Offset core voltage
    result = RWVolt.offset_core_voltage(0, target)
    print(f"Offset Core Voltage Result: {result}")
    