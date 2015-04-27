dymoprint
=========

Linux Software to print with LabelManager PnP from Dymo


cloned for development from http://sbronner.com/dymoprint/

Changes:

- *some..*


### For ubuntu based distributions:
(should also work for debian, but not tested yet)
use **udev** and **modeswitch** configurations to work with the LabelManager PNP.
**modeswitch** changes the mode (and USB Id) from mass storage device to printer device

    sudo cp 91-dymo-labelmanager-pnp.rules /etc/udev/rules.d/
    sudo cp dymo-labelmanager-pnp.conf /etc/usb_modeswitch.d/

and restart services with
    sudo reload udev

([more info](http://www.draisberghof.de/usb_modeswitch/bb/viewtopic.php?t=947))

# DYMO LabelManager PNP
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0922", ATTRS{idProduct}=="1001", \
RUN+="/usr/sbin/usb_modeswitch -c /etc/usb_modeswitch.d/dymo-labelmanager-pnp.conf"
SUBSYSTEMS=="usb", ATTRS{idVendor}=="0922", ATTRS{idProduct}=="1002", MODE="0660", GROUP="plugdev"
#
#SUBSYSTEM=="hidraw", ACTION=="add", ATTRS{idVendor}=="0922", ATTRS{idProduct}=="1001", GROUP="plugdev"
