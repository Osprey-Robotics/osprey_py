# Osprey Robotics Demo for Proof of Life

import binascii
import usb1
import time
import threading
import curses

# Constants
STOP = 0
FORWARD = 1
LEFT = 1
RIGHT = 1
BACKWARD = 1
SER_FRONT_LEFT_1 = "205A336B4E55"
SER_BACK_LEFT_2 = "2061376C4243"
SER_BACK_RIGHT_3 = "206D33614D43"
SER_FRONT_RIGHT_4 = "206B336B4E55"
# TODO: Use dictionary instead. cdccccbe and cdcccc3e would be mapped to keys of -40 and 40 respectively
NEGATIVE_40 = binascii.a2b_hex("000000008400058208000000cdccccbe0000000032a34b88")
POSITIVE_40 = binascii.a2b_hex("000000008400058208000000cdcccc3e000000000af69afb")

COMM_FORWARD = ["00000000802c058208000000100000000000000095e92111", "00000000802c0582080000001000000000000000a6102211", "00000000802c0582080000001000000000000000b6372211", "00000000802c0582080000001000000000000000c75e2211", "00000000802c0582080000001000000000000000d8852211"]

CURRENT_ACTION = 0
all_motors = []

def move_forward(serial, dev):
    global CURRENT_ACTION, FORWARD
    dev.claimInterface(0)
    # TODO: Replace static file with one message and timestamp-packed last bytes, they shouldn't be much different
    if serial == SER_FRONT_LEFT_1: # Front left, 1
        dev.bulkWrite(0x02, POSITIVE_40, timeout=1000)
    elif serial == SER_BACK_LEFT_2: # Back left, 2
        dev.bulkWrite(0x02, POSITIVE_40, timeout=1000)
    elif serial == SER_BACK_RIGHT_3: # Back right, 3
        dev.bulkWrite(0x02, NEGATIVE_40, timeout=1000)
    elif serial == SER_FRONT_RIGHT_4: # Front right, 4
        dev.bulkWrite(0x02, NEGATIVE_40, timeout=1000)
    else:
        raise Exception("Unknown serial detected: %s" % serial)
    try:
        for line in COMM_FORWARD:
            dev.bulkWrite(0x02, binascii.a2b_hex(line))
            time.sleep(.1)
    except Exception as e:
        #print("Error: %s" % str(e))
        return

def move_backward(serial, dev):
    global CURRENT_ACTION, BACKWARD
    dev.claimInterface(0)
    # TODO: Replace static file with one message and timestamp-packed last bytes, they shouldn't be much different
    if serial == SER_FRONT_LEFT_1: # Front left, 1
        dev.bulkWrite(0x02, NEGATIVE_40, timeout=1000)
    elif serial == SER_BACK_LEFT_2: # Back left, 2
        dev.bulkWrite(0x02, NEGATIVE_40, timeout=1000)
    elif serial == SER_BACK_RIGHT_3: # Back right, 3
        dev.bulkWrite(0x02, POSITIVE_40, timeout=1000)
    elif serial == SER_FRONT_RIGHT_4: # Front right, 4
        dev.bulkWrite(0x02, POSITIVE_40, timeout=1000)
    else:
        raise Exception("Unknown serial detected: %s" % serial)
    try:
        for line in COMM_FORWARD:
            dev.bulkWrite(0x02, binascii.a2b_hex(line))
            time.sleep(.1)
    except Exception as e:
        #print("Error: %s" % str(e))
        return

def spin_left(serial, dev):
    global CURRENT_ACTION, LEFT
    dev.claimInterface(0)
    # TODO: Replace static file with one message and timestamp-packed last bytes, they shouldn't be much different
    if serial == SER_FRONT_LEFT_1: # Front left, 1
        dev.bulkWrite(0x02, POSITIVE_40, timeout=1000)
    elif serial == SER_BACK_LEFT_2: # Back left, 2
        dev.bulkWrite(0x02, POSITIVE_40, timeout=1000)
    elif serial == SER_BACK_RIGHT_3: # Back right, 3
        dev.bulkWrite(0x02, POSITIVE_40, timeout=1000)
    elif serial == SER_FRONT_RIGHT_4: # Front right, 4
        dev.bulkWrite(0x02, POSITIVE_40, timeout=1000)
    else:
        raise Exception("Unknown serial detected: %s" % serial)
    try:
        for line in COMM_FORWARD:
            dev.bulkWrite(0x02, binascii.a2b_hex(line))
            time.sleep(.1)
    except Exception as e:
        #print("Error: %s" % str(e))
        return

def spin_right(serial, dev):
    global CURRENT_ACTION, RIGHT
    dev.claimInterface(0)
    # TODO: Replace static file with one message and timestamp-packed last bytes, they shouldn't be much different
    if serial == SER_FRONT_LEFT_1: # Front left, 1
        dev.bulkWrite(0x02, NEGATIVE_40, timeout=1000)
    elif serial == SER_BACK_LEFT_2: # Back left, 2
        dev.bulkWrite(0x02, NEGATIVE_40, timeout=1000)
    elif serial == SER_BACK_RIGHT_3:  # Back right, 3
        dev.bulkWrite(0x02, NEGATIVE_40, timeout=1000)
    elif serial == SER_FRONT_RIGHT_4: # Front right, 4
        dev.bulkWrite(0x02, NEGATIVE_40, timeout=1000)
    else:
        raise Exception("Unknown serial detected: %s" % serial)
    try:
        for line in COMM_FORWARD:
            dev.bulkWrite(0x02, binascii.a2b_hex(line))
            time.sleep(.1)
    except Exception as e:
        #print("Error: %s" % str(e))
        return

def open_dev(usbcontext=None):
    if usbcontext is None:
        usbcontext = usb1.USBContext()

    for udev in usbcontext.getDeviceList(skip_on_error=True):
        vid = udev.getVendorID()
        pid = udev.getProductID()
        device = udev.getDeviceAddress()
        serial = udev.getSerialNumber()
        if ((vid, pid) == (0x0483, 0xA30E)):
            motor = udev.open()
            motor.resetDevice()
            all_motors.append((serial, motor))
    if len(all_motors) < 4:
        raise Exception("Insufficient motors detected")

def main(win):
    global CURRENT_ACTION, STOP, FORWARD
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
    win.clear()
    win.addstr("Detected key:")
    while True:
        try:
           key = win.getkey()
           win.clear()
           win.addstr("Detected key:")
           win.addstr(repr(str(key)))
           if key == "q":
              break
           elif key == "w":
               if CURRENT_ACTION == STOP:
                   CURRENT_ACTION = FORWARD
                   for motor in all_motors:
                       t=threading.Thread(target=move_forward, args=(motor[0],motor[1]))
                       t.start()
           elif key == "a":
               if CURRENT_ACTION == STOP:
                   CURRENT_ACTION = LEFT
                   for motor in all_motors:
                       t=threading.Thread(target=spin_left, args=(motor[0],motor[1]))
                       t.start()
           elif key == "s":
               if CURRENT_ACTION == STOP:
                   CURRENT_ACTION = BACKWARD
                   for motor in all_motors:
                       t=threading.Thread(target=move_backward, args=(motor[0],motor[1]))
                       t.start()
           elif key == "d":
               if CURRENT_ACTION == STOP:
                   CURRENT_ACTION = RIGHT
                   for motor in all_motors:
                       t=threading.Thread(target=spin_right, args=(motor[0],motor[1]))
                       t.start()
           else:
               pass
        except Exception as e:
           # No input
           CURRENT_ACTION = STOP
           pass

curses.wrapper(main)
