# dymoprint

[![GitHub Actions (Tests)](https://github.com/computerlyrik/dymoprint/workflows/Tests/badge.svg)](https://github.com/computerlyrik/dymoprint)
[![PyPI version](https://img.shields.io/pypi/v/dymoprint.svg)](https://pypi.org/project/dymoprint/)

Linux Software to print with LabelManager PnP from Dymo

* First version from Sebastian Bronner: <https://sbronner.com/dymoprint.html>
* Cloned to Github and formerly maintained by @computerlyrik: <https://github.com/computerlyrik/dymoprint>
* Currently maintained by @maresb

## Features

* Works on python 3.7 and up
* Supports text printing
* Supports qr code printing
* Supports barcode printing
* Supports image printing
* Supports combined barcode / qrcode and text printing

## Installation

It is recommended to install dymoprint with [pipx](https://pypa.github.io/pipx/) so that it runs in an isolated virtual environment:

```bash
pipx install dymoprint
```

In case pipx is not already installed, it can be installed on Ubuntu/Debian with

```bash
sudo apt-get install pipx
```

or on Arch with

```bash
sudo pacman -S python-pipx
```


To install for development, fork and clone this repository, and from this directory, and run (ideally within a venv):

```bash
pip install --editable .
```

## Configuration

### For ubuntu based distributions

Use **udev** and **modeswitch** configurations to work with the LabelManager PNP.
**modeswitch** changes the mode (and USB Id) from mass storage device to printer device.

```bash
sudo cp 91-dymo-labelmanager-pnp.rules /etc/udev/rules.d/
sudo cp dymo-labelmanager-pnp.conf /etc/usb_modeswitch.d/
```

and restart services with:

```bash
sudo systemctl restart udev.service
```

Finally, physically disconnect and reconnect the LabelManager PnP.

([more info](http://www.draisberghof.de/usb_modeswitch/bb/viewtopic.php?t=947))

### For arch based distributions

(should also work for manjaro, but not tested yet)
use **udev** and **modeswitch** configurations to work with the LabelManager PNP.
**modeswitch** changes the mode (and USB Id) from mass storage device to printer device.

Install **usb_modeswitch** at first:

```bash
sudo pacman -S usb_modeswitch
```

if the **/etc/usb_modeswitch.d/** folder was not created at installation do:

```bash
sudo mkdir /etc/usb_modeswitch.d/
````

now copy the udev and usb_modswitch configs:

```bash
sudo cp 91-dymo-labelmanager-pnp.rules /etc/udev/rules.d/
sudo cp dymo-labelmanager-pnp.conf /etc/usb_modeswitch.d/
```

and restart services with:

```bash
sudo udevadm control --reload
```

you might need to change the permissions of the hid device (dymoprint will tell if it is the case):

```bash
sudo chown your_user:users /dev/hidraw0
```

Finally, physically disconnect and reconnect the LabelManager PnP.

([more info](http://www.draisberghof.de/usb_modeswitch/bb/viewtopic.php?t=947))

## Font management

Fonts are managed via [dymoprint.ini](dymoprint.ini). This should be placed in your
config folder (normally `~/.config`). An example file is provided here.

You may choose any TTF Font you like

You may edit the file to point to your favorite font.

For my Arch-Linux System, fonts are located at e.g.

```bash
/usr/share/fonts/TTF/DejaVuSerif.ttf
```

It is also possible to Download a font from
<http://font.ubuntu.com/> and use it.

## Modes

### Print text

```dymoprint MyText```

Multilines will be generated on whitespace

```dymoprint MyLine MySecondLine # Will print two Lines```

If you want whitespaces just enclose in " "

```dymoprint "prints a single line"```

### Print QRCodes and Barcodes

```dymoprint --help```

### Print Codes and Text

Just add a text after your qr or barcode text

```dymoprint -qr "QR Content" "Cleartext printed"```

### Picture printing

Any picture with JPEG standard may be printed. Beware it will be downsized to tape.

```dymoprint -p mypic.jpg ""```

Take care of the trailing "" - you may enter text here which gets printed in front of the image

## Development

Besides the travis-ci one should run the following command on a feature implemention or change to ensure the same outcome on a real device:

```bash
dymoprint Tst && \
dymoprint -qr Tst && \
dymoprint -c code128 Tst && \
dymoprint -qr qrencoded "qr_txt" && \
dymoprint -c code128 Test "bc_txt"
```

### ToDo

* (?)support multiple ProductIDs (1001, 1002) -> use usb-modeswitch?
* put everything in classes that would need to be used by a GUI
* ~~for more options use command line parser framework~~
* ~~allow selection of font with command line options~~
* allow font size specification with command line option (points, pixels?)
* ~~provide an option to show a preview of what the label will look like~~
* ~~read and write a .dymoprint file containing user preferences~~
* ~~print barcodes~~
* ~~print graphics~~
* ~~plot frame around label~~
* vertical print
