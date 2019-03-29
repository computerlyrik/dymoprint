[![Build Status](https://travis-ci.org/computerlyrik/dymoprint.svg?branch=master)](https://travis-ci.org/computerlyrik/dymoprint)

dymoprint
=========

Linux Software to print with LabelManager PnP from Dymo


cloned for development from https://sbronner.com/dymoprint.html


## Installation & Configuration
### Dependent packages

```
pip install -r requirements.txt
```
or in userspace
```
pip install --user -r requirements.txt
```

#### For ubuntu based distributions:
(should also work for debian, but not tested yet)
use **udev** and **modeswitch** configurations to work with the LabelManager PNP.
**modeswitch** changes the mode (and USB Id) from mass storage device to printer device.

    sudo cp 91-dymo-labelmanager-pnp.rules /etc/udev/rules.d/
    sudo cp dymo-labelmanager-pnp.conf /etc/usb_modeswitch.d/    
    
and restart services with:
  
    sudo systemctl restart udev.service

([more info](http://www.draisberghof.de/usb_modeswitch/bb/viewtopic.php?t=947))


### Font management

Fonts are managed via **dymoprint.ini**

You may choose any TTF Font you like

You may edit the file to point to your favorite font.

For my Arch-Linux System, fonts are located at e.g.

	/usr/share/fonts/TTF/DejaVuSerif.ttf

It is also possible to Download a font from
http://font.ubuntu.com/ and use it.

## Development 
Besides the travis-ci one should run the following command on a feature implemention or change to ensure the same outcome on a real device:
```
./dymoprint Tst && \
./dymoprint -qr Tst && \
./dymoprint -c code128 Tst && \
./dymoprint -qr qrencoded "qr_txt" && \
./dymoprint -c code128 Test "bc_txt"
```


### ToDo
- (?)support multiple ProductIDs (1001, 1002) -> use usb-modeswitch?
- put everything in classes that would need to be used by a GUI
- ~~for more options use command line parser framework~~
- ~~allow selection of font with command line options~~
- allow font size specification with command line option (points, pixels?)
- ~~provide an option to show a preview of what the label will look like~~
- ~~read and write a .dymoprint file containing user preferences~~
- ~~print barcodes~~
- print graphics
- ~~plot frame around label~~
- vertical print
