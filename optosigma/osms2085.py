import serial
from .gsc02 import GSC02


class OSMS2085(GSC02):
    is_sleep_until_stop = True

    millimeter_per_pulse = 0.001  # [mm/pulse] (fixed)

    def __init__(
        self,
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
        axis=1,
        **kwargs,
    ):
        super().__init__(
            port=port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            timeout=timeout,
            xonxoff=xonxoff,
            rtscts=rtscts,
            write_timeout=write_timeout,
            dsrdtr=dsrdtr,
            inter_byte_timeout=inter_byte_timeout,
            exclusive=exclusive,
            **kwargs,
        )
        self.axis = axis  # 1 or 2

    def reset(self, direction="-") -> bool:
        ret = self.return_origin(direction, axis=self.axis)
        if self.is_sleep_until_stop:
            self.sleep_until_stop()
        return ret

    def stop(self) -> bool:
        return self.decelerate_stop(axis=self.axis)

    @property
    def millimeter(self) -> float:
        """Get current position [millimeter]"""
        position = getattr(self, f"position{self.axis}")
        return self.pos2mm(position)

    @millimeter.setter
    def millimeter(self, target_mm: float):
        """Move stage to target position [millimeter]"""
        target_position = self.mm2pos(target_mm)
        setattr(self, f"position{self.axis}", target_position)
        if self.is_sleep_until_stop:
            self.sleep_until_stop()

    def pos2mm(self, position: int) -> float:
        return position * self.millimeter_per_pulse

    def mm2pos(self, mm: float) -> int:
        return int(mm / self.millimeter_per_pulse)
