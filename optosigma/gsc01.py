import time
from typing import Tuple, Union
import serial


class GSC01(serial.Serial):
    """Wrapper for GSC-01 controller"""

    def raw_command(self, cmd: str) -> Union[bool, str]:
        """Send command to controller

        Parameters
        ----------
        cmd : str
            Command
            
        Returns
        -------
        ret : bool or str
            Whether the command is a success or not.
            If the response value is neither "OK" nor "NG", the raw response value is returned.
        """
        self.write(cmd.encode())
        self.write(b"\r\n")
        return_msg = self.readline().decode()[:-2]  # -2: Remove terminator characters (CR + LF)
        return (      True if return_msg == "OK"
                else False if return_msg == "NG" 
                else return_msg)

    @property
    def position(self) -> int:
        """Current stage position"""
        return self.get_status1()[0]

    @position.setter
    def position(self, target_position: int):
        """Move stage to target position"""
        current_position = self.position
        relative_position = target_position - current_position
        self.set_relative_pulse(relative_position)
        self.driving()

    @property
    def ack1(self) -> str:
        """ACK1

        X  Command error
        K  Command accepted normaly
        """
        return self.get_status1()[1]

    @property
    def ack2(self) -> str:
        """ACK2
        
        L  LS stop
        K  Normal stop
        """
        return self.get_status1()[2]

    @property
    def ack3(self) -> str:
        """ACK3
        
        B  Busy status
        R  Ready status
        """
        return self.get_status2()

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

    def sleep_until_stop(self) -> None:
        """Sleep until stage stops"""
        while not self.is_ready:
            time.sleep(0.01)

    def return_origin(self) -> bool:
        """H command: Return to Mechanical Origin

        This command is used to detect the mechanical origin for a stage and set that position as the origin. 
        The moving speed S: 500pps, F: 5000pps, R: 200mS. 
        Running a stop command during the homing operation suspends thes operation.  
        Limit sensor’s detection unplanned in the sequence during the homing operation suspends the operation.
        Any commands except the stop command or checking command are not acceptable during the homing operation. 
        Deceleration is not available if the limit sensor is activated.
        For driving in the normal rotation, the limit sensors are assigned as follows.
             1) LS0  CCW(+)
             2) LS1  CW(-)
        For driving in the reverse rotation, the limit sensors are assigned as follows.
             1) LS0  CCW(-)
             2) LS1  CW(+)
        If motor-free, an error is generated to inhibit the homing operation.

        Returns
        -------
        ret : bool
            Whether the command is a success or not.
        """
        return self.raw_command("H:1")
        
    def set_relative_pulse(self, pulse: int) -> bool:
        """M command: Set number of pulses for relative travel

        The command to set the moving distance and direction of the stage. 
        This device runs this command and then runs the driving command to drive the actual stage. 
        The stage accelerates/ decelerates as set in the speed setting command. 
        If this command is repeated without running the driving command, 
        the last run this command or the ‘Command to set number of pulses for absolute travel’ is effective.
        If the return to mechanical Origin Command, JOG Command or Stop Command is run, the values set in this command are canceled. 
        A command error is generated if a coordinate after the move exceeds the specified limit (+/- 16,777,215).
        While motor-free, running this command causes a command error.

        Parameters
        ----------
        pulse : int
            Moving pulse. Set a number from (+/- 16,777,215)

        Returns
        -------
        ret : bool
            Whether the command is a success or not.

        Examples
        --------
        >>> set_relative_pulse(1000)  # Sets 1000pulse move in the positive direction.
        True
        >>> set_relative_pulse(-5000)  # Sets 5000pulse move in the negative direction.
        True
        """
        n = 1
        m = "+" if pulse >= 0 else "-"
        x = str(abs(pulse))
        return self.raw_command(f"M:{n}{m}P{x}")

    def set_absolute_pulse(self, pulse: int) -> bool:
        """A command: Set number of pulses for absolute travel

        The command to set the moving distance and direction of the stage. 
        This device runs this command and then runs the driving command to drive the actual stage.
        The stage accelerates/decelerates as set in the speed setting command.
        If this command is repeated without running the driving command, 
        the last run this command or the ‘Command to set number of pulses for Relative travel’ is effective. 
        If the return to mechanical Origin Command, JOG Command or Stop Command is run, the values set in this command are canceled. 
        A command error is generated if a coordinate after the move exceeds the specified limit (+/- 16,777,215).
        While motor-free, running this command causes a command error.
        
        Parameters
        ----------
        pulse : int
            Moving pulse. Set a number from (+/- 16,777,215)
        
        Returns
        -------
        ret : bool
            Whether the command is a success or not.

        Examples
        --------
        >>> set_absolute_pulse(1000)  # Set a move to coordinate 1000
        True
        >>> set_absolute_pulse(-5000)  # Set a move to coordinate -5000
        True
        """
        n = 1
        m = "+" if pulse >= 0 else "-"
        x = str(abs(pulse))
        return self.raw_command(f"A:{n}{m}P{x}")

    def jog(self, direction: str) -> bool:
        """J command: JOG Command

        Set jog operation for the stage. 
        This device runs this command and then runs the driving command to drive the actual stage.
        The stage moves at a preset jog speed without acceleration/deceleration. 
        The jog speed is set in the ‘JOG Speed Set’ command. 
        When stop this, stop by L command. (When there is not L command, move to Limit sensor and stop in Limit sensor).
        Running a different moving command (M command, etc) without running the driving command cancels this command. 
        While motor-free, running this command causes a command error.

        Parameters
        ----------
        direction : str
             "+": Moves the axis in the positive direction, 
             "-": Moves the axis in the negative direction

        Returns
        -------
        ret : bool
            Whether the command is a success or not.

        Examples
        --------
        >>> jog("+")  # Set jog operation in the positive direction.
        True
        """
        if direction in ["+", "-"]:
            n = 1
            m = direction
            return self.raw_command(f"J:{n}{m}")
        else:
            msg = f'"{direction}" is not supported, choose direction from "+" or "-"'
            raise ValueError(msg)

    def driving(self) -> bool:
        """G command: Driving command

        The command to perform the driving operation of the stage.
        The stage is driven according to the ‘M command’ / ‘A command’ and ‘J command’ run immediately before. 
        On detecting a limit, the stage being driven stops immediately without acceleration/deceleration.
        Running this command without running a moving command (M command/ A command or J command) generates a command error.
        While motor-free, running this command causes a command error.
        
        Returns
        -------
        ret : bool
            Whether the command is a success or not.

        Examples
        --------
        >>> set_relative_pulse(10000)
        >>> driving()  # Moves 1000pulse in the positive direction.
        True
        """
        return self.raw_command("G:")

    def decelerate_stop(self) -> bool:
        """L command: Decelerate and stop

        When this command is executed, the stage decelerates and stops.

        Returns
        -------
        ret : bool
            Whether the command is a success or not.
        """
        return self.raw_command("L:1")

    def immediate_stop(self) -> bool:
        """L:E command: Immediate stop

        Stops the driving of the stage without deceleration.
        Unlike emergency stop signal input, this command does not motor-free.

        Returns
        -------
        ret : bool
            Whether the command is a success or not.
        """
        return self.raw_command("L:E")

    def set_logical_zero(self) -> bool:
        """R command: Electronic (Logical) Zero set command

        Set the current coordinate to the electronic (logical) zero. 
        After running this command, the current position is set to ZERO.

        Returns
        -------
        ret : bool
            Whether the command is a success or not.
        """
        return self.raw_command("R:1")

    def set_speed(self, spd_min: int, spd_max: int, acceleration_time: int) -> bool:
        """D command: Speed setting

        Sets the minimum/maximum speeds and acceleration/deceleration time for moving the stage. 
        The minimum speed is the driving speed S, the speed when the stage starts. 
        The maximum speed is the driving speed F that specifies the maximum speed of the stage. 
        The unit of the speeds is [PPS].

        Acceleration/deceleration time specifies the acceleration time from the driving speed S to F, 
        and the deceleration time from F to S. The unit of time is mS.

        The initial values are as follows:
          Minimum speed S                     500[PPS]
          Maximum speed F                     50000[PPS]
          Acceleration/ Deceleration Time     200[mS]
        (* If setting Configuration Program, obey the value.)

        Be sure to set the maximum speed F higher than the minimum speed S.
        Set the speed in 100[PPS]. Values less than 100[PPS] are rounded down.

        Parameters
        ----------
        spd_min: int
            Minimum Speed. Set a number from 100-20000. [PPS]
        spd_max: int 
            Maximum Speed. Set a number from 100-20000. [PPS]
        acceleration_time : int
            Acceleration/Deceleration time. Set a number from 0-1000. [mS]

        Returns
        -------
        ret : bool
            Whether the command is a success or not.

        Examples
        --------
        >>> set_speed(500, 50000, 200)  # Set the minimum speed to 500[PPS], the maximum speed to 5000[PPS], and the acceleration/deceleration time to 200[mS].
        True
        """
        n = 1
        spd1 = spd_min
        spd2 = spd_max
        spd3 = acceleration_time
        return self.raw_command(f"D:{n}S{spd1}F{spd2}R{spd3}")

    def energize_motor(self, energize: bool) -> bool:
        """C command: Motor Free/ Hold Command

        Deenergize (OFF)/ energize (ON) the motor.

        Parameters
        ----------
        energize : bool
            True: hold motor
            False: free motor

        Returns
        -------
        ret : bool
            Whether the command is a success or not.

        Examples
        --------
        >>> energize_motor(False)  # Free motor
        True
        """
        n = 1
        m = 1 if energize else 0
        return self.raw_command(f"C:{n}{m}")

    def get_status1(self) -> Tuple[int, str, str, str]:
        """ Q command: Status1

        On receipt of this command, the controller returns the coordinate and the current state.

        Returns
        -------
        position : int
            current position
        ack1 : str
            X  Command error or 
            K  Command accepted normaly
        ack2 : str
            L  LS stop
            K  Normal stop
        ack3 : str
            B  Busy status
            R  Ready status
        """
        status = self.raw_command("Q:").split(",")
        position = int(status[0].replace(" ", ""))
        ack1 = status[1]
        ack2 = status[2]
        ack3 = status[3]
        return position, ack1, ack2, ack3

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

    def get_version(self, firmware_type: str="ROM") -> str:
        """? command: Internal Information

        Returns the version number of firmware in this controller.

        Parameters
        ----------
        firmware_type: str
            Firmware type. "ROM" or "revision".

        Returns
        -------
        version : str
            ROM Version or Revision number
        """
        if firmware_type.lower() == "rom":
            return self.raw_command("?:V")
        elif firmware_type.lower() == "revision":
            return self.raw_command("?:-")
        else:
            msg = f'"{firmware_type}" is not supported, choose firmware type from "ROM" or "Revision"'
            raise ValueError(msg)

    def io_output(self, a: int) -> bool:
        """O command: I/O Output

        Sets the status of the I/O interface output ports. 
        The status of a port is set to a number from 0-15.
        
        Parameters
        ----------
        a : int
            0-15 
        
        Returns
        -------
        ret : bool
            Whether the command is a success or not.

        Examples
        --------
        >>> io_output(1)  # Sets the I/O interface output port DO0 to ‘ON’.
        True
        """
        return self.raw_command(f"O:{a}")

    def io_input(self) -> int:
        """I command: I/O Input

        Returns the current status of the I/O input ports. 
        The status of a port is returned in a number from 0-15.

        Returns
        -------
        a : int 
            0-15 

        Examples
        --------
        >>> io_input()
        2  # Only DI1 is ‘ON’.
        """
        return int(self.raw_command("I:"))