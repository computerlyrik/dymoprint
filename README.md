dymoprint
=========

Linux Software to print with LabelManager PnP from Dymo


cloned for development from http://sbronner.com/dymoprint/

Changes:

- Using PIL library instead of pillow (python 2.7)
- explicit use of python2
- my udevrule is SUBSYSTEM=="hidraw", ACTION=="add", ATTRS{idVendor}=="0922", ATTRS{idProduct}=="1001", MODE="0660", GROUP="lpadmin"


### For ubuntu based distributions:
(should also work for debian, but not tested yet)
use **udev** and **modeswitch** configurations to work with the LabelManager PNP.
**modeswitch** changes the mode (and USB Id) from mass storage device to printer device

'''sh
$ sudo cp 91-dymo-labelmanager-pnp.rules /etc/udev/rules.d/
$ sudo cp dymo-labelmanager-pnp.conf /etc/usb_modeswitch.d/
'''
and restart services with
'''sh
$ sudo reload udev
'''

([more info](http://www.draisberghof.de/usb_modeswitch/bb/viewtopic.php?t=947))

