import binascii
import time
import usb1
import time
import threading

all_motors = [] # We are appending a Serial # and device/motor ID to this array? 

def validate_read(expected, actual, msg): #------------
    return

def replay(serial, dev): #---------------
    def bulkRead(endpoint, length, timeout = None):
        return dev.bulkRead(endpoint, length, timeout = (1000 if timeout is None else timeout))

    def bulkWrite(endpoint, data, timeout = None):
        dev.bulkWrite(endpoint, data, timeout = (1000 if timeout is None else timeout)) 

    def controlRead(bRequestType, bRequest, wValue, wIndex, wLength, timeout = None):
        return

    def controlWrite(bRequestType, bRequest, wValue, wIndex, data, timeout = None):
        dev.controlWrite(bRequestType, bRequest, wValue, wIndex, data, timeout = (1000 if timeout is None else timeout))

    def interruptRead(endpoint, size, timeout = None):
        return dev.interruptRead(endpoint, size, timeout = (1000 if timeout is None else timeout))

    def interruptWrite(endpoint, data, timeout = None):
        dev.interruptWrite(endpoint, data, timeout = (1000 if timeout is None else timeout))

    # Generated by usbrply
    # Source: Windows pcap (USBPcap)
    # cmd: /usr/local/bin/usbrply --wrapper --device-hi -p neo_motor2.pcapng
    # PCapGen device hi: selected device 3
    comm = open("commtestcan").read().splitlines()
    #print(serial)
    if serial == "206B336B4E55": # Front right, 4 DONE
        #return
        #bulkWrite(0x02, binascii.a2b_hex("000000008400058208000000295c8f3e000000004f1070fb"))
        bulkWrite(0x02, binascii.a2b_hex("000000008400058208000000cdccccbe0000000032a34b88"))
    if serial == "206D33614D43": # Back right, 3
        #return
        ##bulkWrite(0x02, binascii.a2b_hex("000000008400058208000000cdccccbe0000000032a34b88"))
        ##bulkWrite(0x02, binascii.a2b_hex("000000008400058208000000cdccccbe0000000032a34b88"))
        bulkWrite(0x02, binascii.a2b_hex("000000008400058208000000cdccccbe0000000032a34b88"))
        #####bulkWrite(0x02, binascii.a2b_hex("000000008400058208000000713d8abe00000000231f0b88"))
        #bulkWrite(0x02, binascii.a2b_hex("000000008400058208000000cdcccc3e000000000bf69afd"))
        #bulkWrite(0x02, binascii.a2b_hex("000000008400058208000000cdcccc3e000000000af69afc"))
    if serial == "2061376C4243": #Back left, 2
        #return
        bulkWrite(0x02, binascii.a2b_hex("000000008400058208000000cdcccc3e000000000af69afb"))
        #bulkWrite(0x02, binascii.a2b_hex("000000008400058208000000713d8abe00000000231f0b88"))
        #000000008400058208000000b81e85be00000000d6d94087"))
        #bulkWrite(0x02, binascii.a2b_hex("000000008400058208000000cdcccc3e000000000bf69afd"))
        #bulkWrite(0x02, binascii.a2b_hex("0000000084000582080000000ad7233d000000002ce91cfb"))
    if serial == "205A336B4E55": # Front left, 1
        #return
        bulkWrite(0x02, binascii.a2b_hex("000000008400058208000000cdcccc3e000000000af69afb"))
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
    replay(dev[0], dev[1])

def open_dev(usbcontext=None):
    if usbcontext is None:
        usbcontext = usb1.USBContext()

    print('Scanning for devices...')
    for udev in usbcontext.getDeviceList(skip_on_error=True):
        vid = udev.getVendorID()
        pid = udev.getProductID()
        device = udev.getDeviceAddress()
        serial = udev.getSerialNumber()
        if ((vid, pid) == (0x0483, 0xA30E)):
            all_motors.append((serial, udev.open()))
            print("")
            print("")
            print('Found device')
            print('Bus %03i Device %03i: ID %04x:%04x' % (
                udev.getBusNumber(),
                udev.getDeviceAddress(),
                vid,
                pid))
    #if len(all_motors) < 2:
    #    raise Exception("Failed to find a device")

if __name__ == "__main__":
    #import argparse

    #parser = argparse.ArgumentParser(description='Replay captured USB packets')
    #args = parser.parse_args()

    usbcontext = usb1.USBContext()
    open_dev(usbcontext)
    print("%i motors detected" % len(all_motors))
    #print(all_motors)
    for motor in all_motors:
        t = threading.Thread(target = run_motor, args = (motor,))
        t.start()