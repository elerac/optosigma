# OptoSigma Motorized Stages Control

This project provides wrappers to control [OptoSigma (Sigma-Koki) motorized stages](https://jp.optosigma.com/en_jp/motorized-stages.html) in Python. The wrapper is designed for 1) controllers and 2) stages.

(1) The controller type wrapper sends commands to the controller (*i.e.*, GSC-01 and GSC-02) through [pySerial](https://github.com/pyserial/pyserial). It supports all commands of the SHOT series and provides practical methods and attributes.

(2) The stage type wrapper inherits the controller type wrapper. Hence, you can send not only basic commands but also use stage-specific methods and attributes.

## Supported Controllers and Stages
| [GSC-01](https://jp.optosigma.com/en_jp/motorized-stages/controllers-drivers/single-axis-stage-controller/gsc-01.html) | [GSC-02](https://jp.optosigma.com/en_jp/motorized-stages/controllers-drivers/2-axis-stage-controller-half-step/gsc-02.html) | [OSMS-60YAW](https://jp.optosigma.com/en_jp/catalog/product/view/id/12617/s/osms-60yaw/category/456/) | [PWA-100](http://www.twin9.co.jp/product/holders-list/mirror-list-2-2/pwa-100/) | 
| :-: | :-: | :-: | :-: |
| ![](https://jp.optosigma.com/media/catalog/product/cache/abae91551e7847ba068353fb78d14f29/g/s/gsc-01_p_pqyav390g4670kee.jpg) | ![](https://jp.optosigma.com/media/catalog/product/cache/abae91551e7847ba068353fb78d14f29/g/s/gsc-02_p_1uaksjmt1bqcnadg.jpg) | ![](https://jp.optosigma.com/media/catalog/product/cache/abae91551e7847ba068353fb78d14f29/o/s/osms-60yaw_p_hg82pv9mibjyav8t.jpg) |  |
| Controller | Controller | Stage | Stage |
| [GSC-01.md](documents/GSC-01.md) | [GSC-02.md](documents/GSC-02.md) | [OSMS-60YAW.md](documents/OSMS-60YAW.md) | [PAW-100.md](documents/PWA-100.md) |
| [[Manual]](https://jp.optosigma.com/html/en_jp/software/motorize/manual_en/GSC-01_En.pdf) | [[Manual]](https://jp.optosigma.com/html/en_jp/software/motorize/manual_en/GSC-02.pdf) | | | 
| | | | [[Video]](https://youtu.be/dfmbfFGqxJw) |

## Requirement
* [pyserial](https://github.com/pyserial/pyserial)

## Short Introduction

### Basic Usage of GSC01 class
Open port at baudrate=9600, bytesize=8, parity=NONE, stopbits=1, timeout=forever. Other arguments follow [pySerial serial.Serial](https://pythonhosted.org/pyserial/pyserial_api.html).
```python
from optosigma import GSC01
port = "/dev/tty.usbserial-FTRWB1RN"  # depends on your environment
controller = GSC01(port)
```

Return to mechanical origin (H command) and wait.
```python
controller.return_origin()
controller.sleep_until_stop()
```

Move stage +1000 pulses (M and G command) and wait.
```python
controller.position += 1000
controller.sleep_until_stop()
```

Get stage status.
```python
print(controller.position)
# 1000
print(controller.is_ready)
# True
```

Stop stage (L command).
```python
controller.decelerate_stop()
```

### Other Classes
For more detail, check the following documents.
- [GSC-01.md](documents/GSC-01.md)
- [GSC-02.md](documents/GSC-02.md)
- [OSMS-60YAW.md](documents/OSMS-60YAW.md)
- [PAW-100.md](documents/PWA-100.md)