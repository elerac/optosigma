from .gsc02 import GSC02


class OSMS60YAW(GSC02):
    is_sleep_until_stop = True

    degree_per_pulse = 0.0025  # [deg/pulse] (fixed)

    axis = 1

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
        position = self.get_position(axis=self.axis)
        degree = self.pos2deg(position)
        return degree
    
    @degree.setter
    def degree(self, target_degree: float):
        """Move stage to target angle [deg]"""
        current_degree = self.degree
        target_degree %= 360
        relative_degree = (target_degree - current_degree) % 360
        relative_position = self.deg2pos(relative_degree)

        self.set_relative_pulse(relative_position, axis=self.axis)
        self.driving()
        if self.is_sleep_until_stop:
            self.sleep_until_stop()

    def pos2deg(self, position: int) -> float:
        return (position % (360.0 / self.degree_per_pulse)) * self.degree_per_pulse

    def deg2pos(self, degree: float) -> int:
        return int(degree / self.degree_per_pulse)