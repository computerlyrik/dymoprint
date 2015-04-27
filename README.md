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

