from .gsc02 import GSC02
from .osms2085 import OSMS2085


class OSMS2085XYZ:
    def __init__(self, port, x_axis=1, y_axis=2) -> None:
        self.stage = GSC02(port)
        self.x = OSMS2085(port, axis=x_axis)
        self.y = OSMS2085(port, axis=y_axis)

    def reset(self, direction=("-", "-")) -> bool:
        ret = self.stage.return_origin(direction, axis="W")
        if self.x.is_sleep_until_stop or self.y.is_sleep_until_stop:
            self.stage.sleep_until_stop()
        return ret
