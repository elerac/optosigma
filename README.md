# OptoSigma Motorized Stages Control

This project provides wrappers to control [OptoSigma (Sigma-Koki) motorized stages](https://jp.optosigma.com/en_jp/motorized-stages.html) in Python. The wrapper is designed for 1) controllers and 2) stages.

(1) The controller type wrapper sends commands to the controller (*i.e.*, GSC-01 and GSC-02) through [pySerial](https://github.com/pyserial/pyserial). It supports all commands of the SHOT series and provides practical methods and attributes.

(2) The stage type wrapper inherits the controller type wrapper. Hence, you can send not only basic commands but also use stage-specific methods and attributes.

## Supported Controllers and Stages
| [GSC-01](https://jp.optosigma.com/en_jp/motorized-stages/controllers-drivers/single-axis-stage-controller/gsc-01.html) | [GSC-02](https://jp.optosigma.com/en_jp/motorized-stages/controllers-drivers/2-axis-stage-controller-half-step/gsc-02.html) | [OSMS-60YAW](https://jp.optosigma.com/en_jp/catalog/product/view/id/12617/s/osms-60yaw/category/456/) | [PWA-100](http://www.twin9.co.jp/product/holders-list/mirror-list-2-2/pwa-100/) | 
| :-: | :-: | :-: | :-: |
| ![](https://jp.optosigma.com/media/catalog/product/cache/abae91551e7847ba068353fb78d14f29/g/s/gsc-01_p_pqyav390g4670kee.jpg) | ![](https://jp.optosigma.com/media/catalog/product/cache/abae91551e7847ba068353fb78d14f29/g/s/gsc-02_p_1uaksjmt1bqcnadg.jpg) | ![](https://jp.optosigma.com/media/catalog/product/cache/abae91551e7847ba068353fb78d14f29/o/s/osms-60yaw_p_hg82pv9mibjyav8t.jpg) |  |
| Controller | Controller | Stage | Stage |
| [[README]](documents/GSC-01.md) | [[README]](documents/GSC-02.md) | [[README]](documents/OSMS-60YAW.md) | [[README]](documents/PWA-100.md) |
| [[Manual]](https://jp.optosigma.com/html/en_jp/software/motorize/manual_en/GSC-01_En.pdf) | [[Manual]](https://jp.optosigma.com/html/en_jp/software/motorize/manual_en/GSC-02.pdf) | | | 
| | | | [[Video]](https://youtu.be/dfmbfFGqxJw) |


## Installation
```sh
pip install git+https://github.com/elerac/optosigma
```
Note: [pySerial](https://github.com/pyserial/pyserial) will also be installed if you don't have it.

## Basic Usage of GSC01 Class
Here is simple example of `GSC01` class.
```python
from optosigma import GSC01

port = "/dev/tty.usbserial-FTRWB1RN"  # depends on your environment
controller = GSC01(port)

# Return to mechanical origin 
controller.return_origin()
controller.sleep_until_stop()

# Move stage +1000 pulses
controller.position += 1000
controller.sleep_until_stop()

# Get stage status
print(controller.position)  # 1000
print(controller.is_ready)  # True
```
You can set arbitrary serial settings such as baud rate, data bits, parity bits, stop bits, and timeout. For more details about serial settings, you also see [documents of pySerial's `serial.Serial` class](https://pyserial.readthedocs.io/en/latest/pyserial_api.html).
```python
controller = GSC01(port, 9600, timeout=1)
```

## Extend to Your Stage
You can extend the controller class into a class for your stage by inheriting.
Here is an example code for OSMS-60YAW rotation stage with GSC-02 controller.
```python
from optosigma import GSC02


class OSMS60YAW(GSC02):
    def __init__(self, port = None, axis = 1):
        super().__init__(port)
        self.axis = axis  # 1 or 2
        self.degree_per_pulse = 0.0025  # [deg/pulse] (fixed)

    @property
    def degree(self):
        position = getattr(self, f"position{self.axis}")
        degree = self.pos2deg(position)
        return degree
    
    @degree.setter
    def degree(self, target_degree):
        target_position = self.deg2pos(target_degree)
        setattr(self, f"position{self.axis}", target_position)
        self.sleep_until_stop()

    def pos2deg(self, position):
        return (position % (360.0 / self.degree_per_pulse)) * self.degree_per_pulse

    def deg2pos(self, degree):
        return int(degree / self.degree_per_pulse)

stage = OSMS60YAW("/dev/tty.usbserial-FTRWB1RN", axis=1)
stage.degree = 60
stage.degree += 30
print(stage.degree)  # 90
```
The above sub-class `OSMS60YAW` contains a property `degree`. This property internally converts the position and angle of the rotation stage. Therefore, we can handle the stage angle intuitively.

