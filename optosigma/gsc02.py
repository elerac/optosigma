import time
from types import MethodType
from typing import Tuple, Union, Sequence, Any
import serial


_gsc02_opened_objects = dict()


class GSC02(serial.Serial):
    """Wrapper for GSC-02 controller"""

    def open(self):
        """Open port with current settings.
        This may throw a SerialException if the port cannot be opened.

        The difference with the original `serial.Serial` class is
        that it *only* executed when opening a *new* port.
        """
        if self.port not in _gsc02_opened_objects:
            super().open()
            if self.is_open:
                _gsc02_opened_objects[self.port] = self

    def close(self):
        """Close port"""
        super().close()

        if self.port in _gsc02_opened_objects:
            del _gsc02_opened_objects[self.port]

    def __getattribute__(self, name):
        if name in ["port", "_port"]:
            return super().__getattribute__(name)

        # If opened object does not exist,
        if self.port not in _gsc02_opened_objects:
            return super().__getattribute__(name)

        opened_object = _gsc02_opened_objects[self.port]

        # If this object is equal to opened object,
        if id(self) == id(opened_object):
            return super().__getattribute__(name)

        # If the attribute was added in sub-class,
        # (opened object hasn't been contained)
        if not hasattr(super(), name):
            return super().__getattribute__(name)

        # Check override
        this_attr = super().__getattribute__(name)
        opened_attr = getattr(opened_object, name)
        if isinstance(this_attr, MethodType):
            is_overridden = this_attr.__func__ != opened_attr.__func__
        else:
            is_overridden = this_attr != opened_attr

        # Rturn overridden attribute
        if is_overridden:
            return super().__getattribute__(name)

        return opened_object.__getattribute__(name)

    def raw_command(self, cmd: str) -> Union[bool, Any]:
        """Send command to controller

        Parameters
        ----------
        cmd : str
            Command

        Returns
        -------
        ret : bool or Any
            Whether the command is a success or not.
            If the command is status check commands (Q:, !:, ?:), the raw response value is returned.
        """
        self.write(cmd.encode())
        self.write(b"\r\n")
        
        if cmd[:2] in ["Q:", "!:", "?:"]:
            # status check commands (Q:, !:, ?:)
            return self.readline().decode()[:-2]  # -2: Remove terminator characters (CR + LF)        
        else:
            return self.is_last_command_success

    def _get_position(self, axis: Union[int, str]) -> int:
        if axis in [1, "1"]:
            return self.get_status1()[0]
        elif axis in [2, "2"]:
            return self.get_status1()[1]

    def _set_position(self, target_position: int, axis: Union[int, str]) -> bool:
        current_position = self._get_position(axis)
        relative_position = target_position - current_position

        ret1 = self.set_relative_pulse(relative_position, axis=axis)
        ret2 = self.driving()
        return all([ret1, ret2])

    @property
    def position1(self) -> int:
        """Current stage position of axis 1"""
        return self._get_position(axis=1)

    @position1.setter
    def position1(self, target_position):
        """Move stage to target position of axis 1"""
        self._set_position(target_position, axis=1)

    @property
    def position2(self) -> int:
        """Current stage position of axis 2"""
        return self._get_position(axis=2)

    @position2.setter
    def position2(self, target_position):
        """Move stage to target position of axis 2"""
        self._set_position(target_position, axis=2)

    @property
    def ack1(self) -> str:
        """ACK1

        X  Command error
        K  Command accepted normaly
        """
        return self.get_status1()[2]

    @property
    def ack2(self) -> str:
        """ACK2
        L  First axis stopped at LS
        M  Second axis stopped at LS
        W  First and second axes stopped at LS
        K  Normal stop
        """
        return self.get_status1()[3]

    @property
    def ack3(self) -> str:
        """ACK3

        B  Busy status
        R  Ready status
        """
        return self.get_status1()[4]

    @property
    def is_ready(self) -> bool:
        """Check whether stage is ready or not"""
        ack3 = self.ack3
        if ack3 == "R":
            return True
        elif ack3 == "B":
            return False

    @property
    def is_last_command_success(self) -> bool:
        """Check whether last command is success or not"""
        ack1 = self.ack1
        if ack1 == "K":
            return True
        elif ack1 == "X":
            return False

    def sleep_until_stop(self):
        """Sleep until stage stops"""
        while not self.is_ready:
            time.sleep(0.01)

    def return_origin(self, direction: Union[str, Sequence[str]], axis: Union[int, str]) -> bool:
        """H command: Return to mechanical origin

        This command is used to detect the mechanical origin for a stage and set that position as the origin.
        Once the mechanical origin has been detected, the value displayed will be 0.
        Each axis moves at the following constant conditions: Minimum speed (S): 500PPS, Maximum speed (F): 5000PPS, Acceleration/ Deceleration time (R): 200mS.
        Axes to home are depending on the DIP Switch settings.

        Parameters
        ----------
        direction : Union[str, Sequence[str]]
            "+": Moves the axis in the positive direction
            "-": Moves the axis in the negative direction
        axis : Union[int, str]
            Axis number. 1 or 2 or "W"

        Returns
        -------
        ret : bool
            Whether the command is a success or not.

        Examples
        --------
        >>> return_origin("+", axis=1)
        >>> return_origin("-", axis=1)
        >>> return_origin("+", axis=2)
        >>> return_origin("-", axis=2)
        >>> return_origin(("+", "+"), axis="W")
        >>> return_origin(("+", "-"), axis="W")
        >>> return_origin(("-", "+"), axis="W")
        >>> return_origin(("-", "-"), axis="W")
        """
        if axis in [1, 2, "1", "2"]:
            if direction in ["+", "-"]:
                n = int(axis)
                m = direction
                return self.raw_command(f"H:{n}{m}")
            else:
                msg = f'"{direction}" is not supported, choose direction from "+" or "-"'
                raise ValueError(msg)
        elif axis == "W":
            if len(direction) == 2:
                if all([d in ["+", "-"] for d in direction]):
                    n = axis
                    m1 = direction[0]
                    m2 = direction[1]
                    return self.raw_command(f"H:{n}{m1}{m2}")
                else:
                    msg = f'"{direction}" is not supported, direction contain "+" or "-"'
                    raise ValueError(msg)
            else:
                msg = f'"Length of `direction` must be 2 (i.e. len(direction) is 2)'
                raise ValueError(msg)
        else:
            msg = f'"{axis}" is not supported, choose axis from [1, 2, "W"]'
            raise ValueError(msg)

    def set_relative_pulse(self, pulse: Union[int, Sequence[int]], axis: Union[int, str]) -> bool:
        """M command: Set number of pulses for relative travel

        This command is to specify the axis of travel, direction, and the travel (number of pulses).
        This command must always be followed by a drive (G) command.
        Travel is by means of acceleration/deceleration driving.

        Parameters
        ----------
        pulse: Union[int, Sequence[int]]
             Moving pulse. Set a number from (+/- 16,777,214)
        axis : Union[int, str]
            Axis number. 1 or 2 or "W"

        Returns
        -------
        ret : bool
            Whether the command is a success or not.

        Examples
        --------
        >>> set_relative_pulse((500, -200), axis="W")  # Travel 500 pulses in the + direction on the first axis and 200 pulses in the - direction on the second axis
        >>> driving()
        """
        if axis in [1, 2, "1", "2"]:
            n = int(axis)
            m = "+" if pulse >= 0 else "-"
            x = str(abs(pulse))
            return self.raw_command(f"M:{n}{m}P{x}")
        elif axis == "W":
            if len(pulse) == 2:
                n = axis
                m1 = "+" if pulse[0] >= 0 else "-"
                x1 = str(abs(pulse[0]))
                m2 = "+" if pulse[1] >= 0 else "-"
                x2 = str(abs(pulse[1]))
                return self.raw_command(f"M:{n}{m1}P{x1}{m2}P{x2}")
            else:
                msg = f'"Length of `direction` must be 2 (i.e. len(direction) is 2)'
                raise ValueError(msg)
        else:
            msg = f'"{axis}" is not supported, choose axis from [1, 2, "W"]'
            raise ValueError(msg)

    def jog(self, direction: Union[str, Sequence[str]], axis: Union[int, str]) -> bool:
        """J command: JOG

        This command drives stages continuously (at a constant speed) at the starting speed (S).
        This command must always be followed by a drive (G) command.
        The stage will stop by an L command.

        Parameters
        ----------
        direction : Union[str, Sequence[str]]
            "+": Moves the axis in the positive direction
            "-": Moves the axis in the negative direction
        axis : Union[int, str]
            Axis number. 1 or 2 or "W"

        Returns
        -------
        ret : bool
            Whether the command is a success or not.

        Examples
        --------
        >>> jpg(("+", "-"), axis="W")  # Move in the - direction on the first axis and in the + direction on the second axis
        >>> driving()
        """
        if axis in [1, 2, "1", "2"]:
            if direction in ["+", "-"]:
                n = int(axis)
                m = direction
                return self.raw_command(f"J:{n}{m}")
            else:
                msg = f'"{direction}" is not supported, choose direction from "+" or "-"'
                raise ValueError(msg)
        elif axis == "W":
            if len(direction) == 2:
                if all([d in ["+", "-"] for d in direction]):
                    n = axis
                    m1 = direction[0]
                    m2 = direction[1]
                    return self.raw_command(f"J:{n}{m1}{m2}")
                else:
                    msg = f'"{direction}" is not supported, direction contain "+" or "-"'
                    raise ValueError(msg)
            else:
                msg = f'"Length of `direction` must be 2 (i.e. len(direction) is 2)'
                raise ValueError(msg)
        else:
            msg = f'"{axis}" is not supported, choose axis from [1, 2, "W"]'
            raise ValueError(msg)

    def driving(self) -> bool:
        """G command: Drive

        When a drive command is issued, the stage starts moving, moves the specified number of pulses, and then stops.
        The G command is used after M and J commands.

        Returns
        -------
        ret : bool
            Whether the command is a success or not.
        """
        return self.raw_command("G")

    def decelerate_stop(self, axis: Union[int, str]) -> bool:
        """L command: Decelerate and stop

        When this command is executed, the stage decelerates and stops.

        Stage does not stop even if“ L:1”,“ L:2” at the time“ H:”.
        Stop in“ L:W" or“ L:E".

        Parameters
        ----------
        axis : Union[int, str]
            Axis number. 1 or 2 or "W"

        Returns
        -------
        ret : bool
            Whether the command is a success or not.
        """
        return self.raw_command(f"L:{axis}")

    def immediate_stop(self) -> bool:
        """L: E command: Emergency stop

        This command stops all stages immediately, whatever the conditions.

        Returns
        -------
        ret : bool
            Whether the command is a success or not.
        """
        return self.raw_command("L:E")

    def set_logical_zero(self, axis: Union[int, str]) -> bool:
        """R command: Set electronic (logical) origin

        This command is used to set electronic (logical) origin to the current position of each axis.

        Parameters
        ----------
        axis : Union[int, str]
            Axis number. 1 or 2 or "W"

        Returns
        -------
        ret : bool
            Whether the command is a success or not.
        """
        return self.raw_command(f"R:{axis}")

    def set_speed(self, spd_range: int, spd_min: Sequence[int], spd_max: Sequence[int], acceleration_time: Sequence[int]) -> bool:
        """D command: Speed settings

        The minimum speed (S), maximum speed (F), and acceleration/deceleration time (R) are set according to the initialize settings when the power is turned on.
        This command allows you to change these initial settings.
        The initialize setting is (S): 500PPS, (F): 5000PPS, (R): 200mS.

        The maximum speed(F) setting should be equal or greater than the minimum speed.
        If the minimum speed is set to equals to the maximum or the acceleration/deceleration time is set to zero,
        stages will move at a constant speed without performing acceleration/deceleration logically.

        Parameters
        ----------
        spd_rande : int
            Speed range. 1: Low speed range, 2: High speed range.
        spd_min: Sequence[int]
            Minimum Speed. 1-200PPS (Low range), 50-20000PPS (High range)
        spd_max: Sequence[int]
            Maximum Speed. 1-200PPS (Low range), 50-20000PPS (High range)
        acceleration_time: Sequence[int]
            Acceleration/Deceleration time. 0-1000mS (for both High/Low range)

        Returns
        -------
        ret : bool
            Whether the command is a success or not.

        Examples
        --------
        >>> set_speed(2, (100, 100), (200, 1000), (1000, 200))
        True
        """
        r = spd_range
        spd11, spd12 = spd_min
        spd21, spd22 = spd_max
        spd31, spd32 = acceleration_time
        return self.raw_command(f"D:{r}S{spd11}F{spd21}R{spd31}S{spd12}F{spd22}R{spd32}")

    def energize_motor(self, energize: Union[bool, Sequence[bool]], axis: Union[int, str]) -> bool:
        """C command: Free/ hold motor (Excitation ON/OFF)

        This command is used to excite the motor or to turn excitation off, making it possible to move (rotate) stages manually.

        Parameters
        ----------
        energize : Union[bool, Sequence[bool]]
            True: hold motor
            False: free motor
        axis : Union[int, str]
            Axis number. 1 or 2 or "W"

        Returns
        -------
        ret : bool
            Whether the command is a success or not.

        Examples
        --------
        >>> energize_motor(False, axis=1)
        """
        if axis in [1, 2, "1", "2"]:
            n = int(axis)
            m = 1 if energize else 0
            return self.raw_command("C:{n}{m}")
        elif axis == "W":
            if len(energize) == 2:
                n = axis
                m1 = 1 if energize[0] else 0
                m2 = 1 if energize[0] else 0
                return self.raw_command(f"C:{n}{m1}{m2}")
            else:
                msg = f'"Length of `direction` must be 2 (i.e. len(direction) is 2)'
                raise ValueError(msg)
        else:
            msg = f'"{axis}" is not supported, choose axis from [1, 2, "W"]'
            raise ValueError(msg)

    def get_status1(self) -> Tuple[int, int, str, str, str]:
        """Q command: Status 1

         On receipt of this command, the controller returns the coordinates for each axis and the current state of each stage.

         Returns
         -------
         position1 : int
             current position of axis 1
         position2 : int
             current position of axis 2
         ack1 : str
             X  Command error
             K  Command accepted normaly
         ack2 : str
             L  First axis stopped at LS
             M  Second axis stopped at LS
             W  First and second axes stopped at LS
             K  Normal stop
        ack3 : str
             B  Busy status
             R  Ready status
        """
        status = self.raw_command("Q:").split(",")
        position1 = int(status[0].replace(" ", ""))
        position2 = int(status[1].replace(" ", ""))
        ack1 = status[2]
        ack2 = status[3]
        ack3 = status[4]
        return position1, position2, ack1, ack2, ack3

    def get_status2(self) -> str:
        """! command: Status2

        On receipt of this command, the controller returns the stage operating status.

        Returns
        -------
        ack3 : str
            B  Busy status
            R  Ready status
        """
        return self.raw_command("!:")

    def get_version(self) -> str:
        """? command: Request for internal information

        The command to request an internal ROM version from the controller.

        Returns
        -------
        version : str
            ROM version
        """
        return self.raw_command("?:V")
