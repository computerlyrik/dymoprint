dymoprint
=========

Linux Software to print with LabelManager PnP from Dymo


cloned for development from http://sbronner.com/dymoprint/

Changes:

- Using PIL library instead of pillow (python 2.7)
- explicit use of python2
- my udevrule is SUBSYSTEM=="hidraw", ACTION=="add", ATTRS{idVendor}=="0922", ATTRS{idProduct}=="1001", MODE="0660", GROUP="lpadmin"

