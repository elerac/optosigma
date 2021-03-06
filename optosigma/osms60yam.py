import serial
from .gsc02 import GSC02


class OSMS60YAW(GSC02):
    is_sleep_until_stop = True

    degree_per_pulse = 0.0025  # [deg/pulse] (fixed)

    def __init__(self, 
                 port=None,
                 baudrate=9600,
                 bytesize=serial.EIGHTBITS,
                 parity=serial.PARITY_NONE,
                 stopbits=serial.STOPBITS_ONE,
                 timeout=None,
                 xonxoff=False,
                 rtscts=False,
                 write_timeout=None,
                 dsrdtr=False,
                 inter_byte_timeout=None,
                 exclusive=None,
                 axis = 1,
                 **kwargs):
        super().__init__(port=port, baudrate=baudrate, bytesize=bytesize, parity=parity, stopbits=stopbits, timeout=timeout, xonxoff=xonxoff, rtscts=rtscts, write_timeout=write_timeout, dsrdtr=dsrdtr, inter_byte_timeout=inter_byte_timeout, exclusive=exclusive, **kwargs)
        self.axis = axis  # 1 or 2

    def reset(self) -> bool:
        ret =  self.return_origin("-", axis=self.axis)
        if self.is_sleep_until_stop:
            self.sleep_until_stop()
        return ret

    def stop(self) -> bool:
        return self.decelerate_stop(axis=self.axis)

    @property
    def degree(self) -> float:
        """Get current angle [deg]"""
        position = getattr(self, f"position{self.axis}")
        degree = self.pos2deg(position)
        return degree
    
    @degree.setter
    def degree(self, target_degree: float):
        """Move stage to target angle [deg]"""
        target_position = self.deg2pos(target_degree)
        setattr(self, f"position{self.axis}", target_position)
        if self.is_sleep_until_stop:
            self.sleep_until_stop()

    def pos2deg(self, position: int) -> float:
        return (position % (360.0 / self.degree_per_pulse)) * self.degree_per_pulse

    def deg2pos(self, degree: float) -> int:
        return int(degree / self.degree_per_pulse)