[![Build Status](https://travis-ci.org/maresb/dymoprint.svg?branch=master)](https://travis-ci.org/maresb/dymoprint)

dymoprint
=========

Linux Software to print with LabelManager PnP from Dymo


* First version from Sebastian Bronner: https://sbronner.com/dymoprint.html
* Cloned by computerlyrik to: https://github.com/computerlyrik/dymoprint
* Forked by Ben Mares on 2020-10-05 to: https://github.com/maresb/dymoprint
* [Pull request](https://github.com/computerlyrik/dymoprint/pull/35) sent to computerlyrik on 2020-10-05 with update and offering PyPI ownership.
* After no response, assumed that computerlyrik's fork is abandoned, continuing development from fork on 2021-03-22.

## Features

* Works on python 2.7 and 3.5 to 3.8
* Supports text printing
* Supports qr code printing
* Supports barcode printing
* Supports image printing
* Supports combined barcode / qrcode and text printing

## Installation & Configuration
### Dependent packages

From this directory,

```bash
pip install .
```

or for development,

```bash
pip install --editable .
```

Add the `--user` flag to install in userspace.

#### For ubuntu based distributions:
(should also work for debian, but not tested yet)
use **udev** and **modeswitch** configurations to work with the LabelManager PNP.
**modeswitch** changes the mode (and USB Id) from mass storage device to printer device.

    sudo cp 91-dymo-labelmanager-pnp.rules /etc/udev/rules.d/
    sudo cp dymo-labelmanager-pnp.conf /etc/usb_modeswitch.d/    
    
and restart services with:
  
    sudo systemctl restart udev.service

Finally, physically disconnect and reconnect the LabelManager PnP.

([more info](http://www.draisberghof.de/usb_modeswitch/bb/viewtopic.php?t=947))


#### For arch based distributions:
(should also work for manjaro, but not tested yet)
use **udev** and **modeswitch** configurations to work with the LabelManager PNP.
**modeswitch** changes the mode (and USB Id) from mass storage device to printer device.

Install **usb_modeswitch** at first:

    sudo pacman -S usb_modeswitch

if the **/etc/usb_modeswitch.d/** folder was not created at installation do:

    sudo mkdir /etc/usb_modeswitch.d/

now copy the udev and usb_modswitch configs:

    sudo cp 91-dymo-labelmanager-pnp.rules /etc/udev/rules.d/
    sudo cp dymo-labelmanager-pnp.conf /etc/usb_modeswitch.d/    
    
and restart services with:
  
    sudo udevadm control --reload

you might need to change the permissions of the hid device (dymoprint will tell if it is the case):

    sudo chown your_user:users /dev/hidraw0 

Finally, physically disconnect and reconnect the LabelManager PnP.

([more info](http://www.draisberghof.de/usb_modeswitch/bb/viewtopic.php?t=947))


### Font management

Fonts are managed via **dymoprint.ini**. This should be placed in your
config folder (normally `~/.config`). An example file is provided here.

You may choose any TTF Font you like

You may edit the file to point to your favorite font.

For my Arch-Linux System, fonts are located at e.g.

	/usr/share/fonts/TTF/DejaVuSerif.ttf

It is also possible to Download a font from
http://font.ubuntu.com/ and use it.

## Modes
### Print text
```./dymoprint MyText```

Multilines will be generated on whitespace

```./dymoprint MyLine MySecondLine # Will print two Lines```

If you want whitespaces just enclose in " "

```./dymoprint "prints a single line"```

### Print QRCodes and Barcodes
```./dymoprint --help```

### Print Codes and Text
just add a text after your qr or barcode text

```./dymoprint -qr "QR Content" "Cleartext printed"```

### Picture printing
Any picture with JPEG standard may be printed. Beware it will be downsized to tape.

```./dymoprint -p mypic.jpg ""```

Take care of the trailing "" - you may enter text here which gets printed in front of the image

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
- ~~print graphics~~
- ~~plot frame around label~~
- vertical print
