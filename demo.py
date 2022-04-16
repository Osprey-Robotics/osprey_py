# Osprey Robotics Demo for Proof of Life
# TODO: Global state for threads, join threads when key no longer pressed?

import binascii
import usb1
import time
import threading
import curses

all_motors = []

# Constants
SER_FRONT_LEFT_1 = "205A336B4E55"
SER_BACK_LEFT_2 = "2061376C4243"
SER_BACK_RIGHT_3 = "206D33614D43"
SER_FRONT_RIGHT_4 = "206B336B4E55"
# TODO: Use dictionary instead. cdccccbe and cdcccc3e would be mapped to keys of -40 and 40 respectively
NEGATIVE_40 = binascii.a2b_hex("000000008400058208000000cdccccbe0000000032a34b88")
POSITIVE_40 = binascii.a2b_hex("000000008400058208000000cdcccc3e000000000af69afb")

def bulkWrite(dev, data, endpoint=0x02, timeout=None):
    dev.bulkWrite(endpoint, data, timeout=(1000 if timeout is None else timeout))

def forward(serial, dev):
    # TODO: Replace static file with one message and timestamp-packed last bytes, they shouldn't be much different
    comm=open("commtestcan").read().splitlines()
    if serial == SER_FRONT_LEFT_1: # Front left, 1
        bulkWrite(dev, POSITIVE_40)
    elif serial == SER_BACK_LEFT_2: # Back left, 2
        bulkWrite(dev, POSITIVE_40)
    elif serial == SER_BACK_RIGHT_3: # Back right, 3
        bulkWrite(dev, NEGATIVE_40)
    elif serial == SER_FRONT_RIGHT_4: # Front right, 4
        bulkWrite(dev, NEGATIVE_40)
    else:
        raise Exception("Unknown serial detected: %s" % serial)
    while True:
        try:
            for line in comm:
                bulkWrite(0x02, binascii.a2b_hex(line))
                time.sleep(.05)
        except Exception:
            return

def run_motor(dev):
    dev[1].claimInterface(0)
    dev[1].resetDevice()
    forward(dev[0], dev[1])

def open_dev(usbcontext=None):
    if usbcontext is None:
        usbcontext = usb1.USBContext()

    for udev in usbcontext.getDeviceList(skip_on_error=True):
        vid = udev.getVendorID()
        pid = udev.getProductID()
        device = udev.getDeviceAddress()
        serial = udev.getSerialNumber()
        if ((vid, pid) == (0x0483, 0xA30E)):
            all_motors.append((serial, udev.open()))
    #if len(all_motors) < 2:
    #    raise Exception("Insufficient motors detected")

def main(win):
    win.nodelay(True)
    key=""
    win.clear()
    win.addstr("Osprey Robotics Demo\n")
    usbcontext = usb1.USBContext()
    open_dev(usbcontext)
    win.addstr("%i motors detected\n" % len(all_motors))
    win.addstr("Ready, press any key to continue\n")
    while True:
        try:
            win.getkey()
            break
        except Exception as e:
            # No input
            pass
    #print(all_motors)
    for motor in all_motors:
        t= threading.Thread(target=run_motor, args=(motor,))
        t.start()
    while True:
        try:
           key = win.getkey()
           win.clear()
           win.addstr("Detected key:")
           win.addstr(repr(str(key)))
           if key == "q":
              break
        except Exception as e:
           # No input
           pass

curses.wrapper(main)
