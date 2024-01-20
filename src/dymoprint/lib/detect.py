import platform
from typing import NamedTuple, NoReturn

import usb

from dymoprint.lib.utils import die

from .constants import (
    DEV_VENDOR,
    HID_INTERFACE_CLASS,
    PRINTER_INTERFACE_CLASS,
    SUPPORTED_PRODUCTS,
    UNCONFIRMED_MESSAGE,
)

GITHUB_LINK = "<https://github.com/computerlyrik/dymoprint/pull/56>"


class DetectedDevice(NamedTuple):
    id: int
    """See dymoprint.constants.SUPPORTED_PRODUCTS for a list of known IDs."""
    dev: usb.core.Device
    intf: usb.core.Interface
    devout: usb.core.Endpoint
    devin: usb.core.Endpoint


def device_info(dev: usb.core.Device) -> str:
    try:
        _ = dev.manufacturer
    except ValueError:
        instruct_on_access_denied(dev)
    res = ""
    res += f"{dev!r}\n"
    res += f"  manufacturer: {dev.manufacturer}\n"
    res += f"  product: {dev.product}\n"
    res += f"  serial: {dev.serial_number}\n"
    configs = dev.configurations()
    if configs:
        res += "  configurations:\n"
        for cfg in configs:
            res += f"  - {cfg!r}\n"
            intfs = cfg.interfaces()
            if intfs:
                res += "    interfaces:\n"
                for intf in intfs:
                    res += f"    - {intf!r}\n"
    return res


class DeviceDetectionError(RuntimeError):
    pass


def detect_device() -> DetectedDevice:
    dymo_devs = list(usb.core.find(idVendor=DEV_VENDOR, find_all=True))
    if len(dymo_devs) == 0:
        print(f"No Dymo devices found (expected vendor {hex(DEV_VENDOR)})")
        for dev in usb.core.find(find_all=True):
            print(
                f"- Vendor ID: {hex(dev.idVendor):6}  "
                f"Product ID: {hex(dev.idProduct)}"
            )
        raise DeviceDetectionError("No Dymo devices found.")
    if len(dymo_devs) > 1:
        print("Found multiple Dymo devices:")
        for dev in dymo_devs:
            print(device_info(dev))
        print("Using first device.")
        dev = dymo_devs[0]
    else:
        dev = dymo_devs[0]
        print(f"Found one Dymo device: {device_info(dev)}")
    dev = dymo_devs[0]
    if dev.idProduct in SUPPORTED_PRODUCTS:
        print(f"Recognized device as {SUPPORTED_PRODUCTS[dev.idProduct]}")
    else:
        print(f"Unrecognized device: {hex(dev.idProduct)}. {UNCONFIRMED_MESSAGE}")

    try:
        dev.get_active_configuration()
        print("Active device configuration already found.")
    except usb.core.USBError:
        try:
            dev.set_configuration()
            print("Device configuration set.")
        except usb.core.USBError as e:
            if e.errno == 13:
                raise RuntimeError("Access denied") from e
            if e.errno == 16:
                print("Device is busy, but this is okay.")
            else:
                raise

    intf = usb.util.find_descriptor(
        dev.get_active_configuration(), bInterfaceClass=PRINTER_INTERFACE_CLASS
    )
    if intf is not None:
        print(f"Opened printer interface: {intf!r}")
    else:
        intf = usb.util.find_descriptor(
            dev.get_active_configuration(), bInterfaceClass=HID_INTERFACE_CLASS
        )
        if intf is not None:
            print(f"Opened HID interface: {intf!r}")
        else:
            die("Could not open a valid interface.")
    assert isinstance(intf, usb.core.Interface)

    try:
        if dev.is_kernel_driver_active(intf.bInterfaceNumber):
            print(f"Detaching kernel driver from interface {intf.bInterfaceNumber}")
            dev.detach_kernel_driver(intf.bInterfaceNumber)
    except NotImplementedError:
        print(f"Kernel driver detaching not necessary on " f"{platform.system()}.")
    devout = usb.util.find_descriptor(
        intf,
        custom_match=(
            lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
            == usb.util.ENDPOINT_OUT
        ),
    )
    devin = usb.util.find_descriptor(
        intf,
        custom_match=(
            lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
            == usb.util.ENDPOINT_IN
        ),
    )

    if not devout or not devin:
        die("The device endpoints not be found.")
    return DetectedDevice(
        id=dev.idProduct, dev=dev, intf=intf, devout=devout, devin=devin
    )


def instruct_on_access_denied(dev: usb.core.Device) -> NoReturn:
    system = platform.system()
    if system == "Linux":
        instruct_on_access_denied_linux(dev)
    elif system == "Windows":
        raise RuntimeError(
            "Couldn't access the device. Please make sure that the "
            "device driver is set to WinUSB. This can be accomplished "
            "with Zadig <https://zadig.akeo.ie/>."
        )
    elif system == "Darwin":
        raise RuntimeError(
            f"Could not access {dev}. Thanks for bravely trying this on a Mac. You "
            f"are in uncharted territory. It would be appreciated if you share the "
            f"results of your experimentation at {GITHUB_LINK}."
        )
    else:
        raise RuntimeError(f"Unknown platform {system}")


def instruct_on_access_denied_linux(dev: usb.core.Device) -> NoReturn:
    # try:
    #     os_release = platform.freedesktop_os_release()
    # except OSError:
    #     os_release = {}
    # dists_with_empties = [os_release.get("ID", "")] + os_release.get(
    #     "ID_LIKE", ""
    # ).split(" ")
    # dists = [dist for dist in dists_with_empties if dist]
    # if "arch" in dists:
    #     restart_udev_command = "sudo udevadm control --reload"
    # elif "ubuntu" in dists or "debian" in dists:
    #     restart_udev_command = "sudo systemctl restart udev.service"
    # # detect whether we are in arch linux or ubuntu linux
    # if Path("/etc/arch-release").exists():
    #     restart_udev_command = "sudo udevadm control --reload"
    # elif Path("/etc/lsb-release").exists():
    #     restart_udev_command = "sudo systemctl restart udev.service"
    # else:
    #     restart_udev_command = None

    lines = []
    lines.append(
        "You do not have sufficient access to the "
        "device. You probably want to add the a udev rule in "
        "/etc/udev/rules.d with the following command:"
    )
    lines.append("")
    udev_rule = ", ".join(
        [
            'ACTION=="add"',
            'SUBSYSTEMS=="usb"',
            f'ATTRS{{idVendor}}=="{dev.idVendor:04x}"',
            f'ATTRS{{idProduct}}=="{dev.idProduct:04x}"',
            'MODE="0666"',
        ]
    )
    lines.append(
        f"  echo '{udev_rule}' "
        f"| sudo tee /etc/udev/rules.d/91-dymo-{dev.idProduct:x}.rules"
    )
    lines.append("")
    lines.append("Next refresh udev with:")
    lines.append("")
    lines.append("  sudo udevadm control --reload-rules")
    lines.append('  sudo udevadm trigger --attr-match=idVendor="0922"')
    lines.append("")
    lines.append(
        "Finally, turn your device off and back "
        "on again to activate the new permissions."
    )
    lines.append("")
    lines.append(
        f"If this still does not resolve the problem, you might need to reboot. "
        f"In case rebooting is necessary, please report this at {GITHUB_LINK}. "
        f"We are still trying to figure out a simple procedure which works "
        f"for everyone. In case you still cannot connect, "
        f"or if you have any information or ideas, please post them at "
        f"that link."
    )
    raise RuntimeError("\n\n" + "\n".join(lines) + "\n")
