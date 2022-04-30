import socket
import binascii
import curses
import struct
import time
import threading
import usb1
import math

# Constants
STOP = 0
FORWARD = 1
LEFT = 2
RIGHT = 3
BACKWARD = 4
UP = 5
DOWN = 6
DIG = 7
MOTOR_SLEEP = 0.05 #0.4
LAST_DRIVE_WAIT = 1.0
SER_FRONT_LEFT_1 = "205A336B4E55"
SER_BACK_LEFT_2 = "2061376C4243"
SER_BACK_RIGHT_3 = "206D33614D43"
SER_FRONT_RIGHT_4 = "206B336B4E55"
SER_LADDER_DIG = "206C395A5543"
SER_LADDER_LIFT = "206A33544D43"

# TODO: Better interface for motor controller protocol, including timestamp/iterative-packed last bytes
POSITIVE_HEX = "000000008400058208000000XXXXXXXX000000000af69afb"
COMM_FORWARD = "00000000802c058208000000100000000000000095e92111"

# Variables
CURRENT_SPEED = 0.5 # 50% by default
CURRENT_ACTION = 0
LAST_DRIVE = 0
all_wheel_motors = []
all_ladder_position_motors = []
all_digging_motors = []

def should_ramp_up_motors(current_time, speed):
    # Only ramp up if speed is greater than 20% and we haven't already ramped up
    if ((current_time-LAST_DRIVE) > LAST_DRIVE_WAIT) and (speed > 0.2):
        return True
    else:
        return False

def generate_speed(speed):
    return binascii.a2b_hex(POSITIVE_HEX.replace("XXXXXXXX", str(binascii.hexlify(struct.pack('<f', speed)), "ascii")))

def kill(serial, dev):
    global CURRENT_ACTION, STOP, MOTOR_SLEEP, COMM_FORWARD, LAST_DRIVE
    dev.claimInterface(0)
    if serial == SER_FRONT_LEFT_1: # Front left, 1
        dev.bulkWrite(0x02, generate_speed(0), timeout=1000)
    elif serial == SER_BACK_LEFT_2: # Back left, 2
        dev.bulkWrite(0x02, generate_speed(0), timeout=1000)
    elif serial == SER_BACK_RIGHT_3: # Back right, 3
        dev.bulkWrite(0x02, generate_speed(-0), timeout=1000)
    elif serial == SER_FRONT_RIGHT_4: # Front right, 4
        dev.bulkWrite(0x02, generate_speed(-0), timeout=1000)
    else:
        raise Exception("Unknown serial detected: %s" % serial)
    try:
        dev.bulkWrite(0x02, binascii.a2b_hex(COMM_FORWARD))
        # Force ramp up
        LAST_DRIVE = 0
    except Exception as e:
        #print("Error: %s" % str(e))
        return

def drive(serial, dev, WHEEL_SPEEDS):
    global CURRENT_ACTION, FORWARD, MOTOR_SLEEP, COMM_FORWARD, LAST_DRIVE
    dev.claimInterface(0)
    if serial == SER_FRONT_LEFT_1: # Front left, 1
        dev.bulkWrite(0x02, generate_speed(WHEEL_SPEEDS[0]), timeout=1000)
    elif serial == SER_BACK_LEFT_2: # Back left, 2
        dev.bulkWrite(0x02, generate_speed(WHEEL_SPEEDS[1]), timeout=1000)
    elif serial == SER_BACK_RIGHT_3: # Back right, 3
        dev.bulkWrite(0x02, generate_speed(WHEEL_SPEEDS[2]), timeout=1000)
    elif serial == SER_FRONT_RIGHT_4: # Front right, 4
        dev.bulkWrite(0x02, generate_speed(WHEEL_SPEEDS[3]), timeout=1000)
    else:
        raise Exception("Unknown serial detected: %s" % serial)
    try:
        dev.bulkWrite(0x02, binascii.a2b_hex(COMM_FORWARD))
        LAST_DRIVE = time.time()
    except Exception as e:
        #print("Error: %s" % str(e))
        return

def lower_bucket_ladder(serial, dev):
    global CURRENT_ACTION, DOWN, MOTOR_SLEEP, COMM_FORWARD, LAST_DRIVE
    dev.claimInterface(0)
    if serial == SER_LADDER_LIFT:
        dev.bulkWrite(0x02, generate_speed(0.15), timeout=1000) # Locked at 15%
    else:
        raise Exception("Unknown serial detected: %s" % serial)
    try:
        dev.bulkWrite(0x02, binascii.a2b_hex(COMM_FORWARD))
        LAST_DRIVE = time.time()
    except Exception as e:
        #print("Error: %s" % str(e))
        return

def raise_bucket_ladder(serial, dev):
    global CURRENT_ACTION, UP, MOTOR_SLEEP, COMM_FORWARD, LAST_DRIVE
    dev.claimInterface(0)
    if serial == SER_LADDER_LIFT:
        dev.bulkWrite(0x02, generate_speed(-0.15), timeout=1000) # Locked at -15%
    else:
        raise Exception("Unknown serial detected: %s" % serial)
    try:
        dev.bulkWrite(0x02, binascii.a2b_hex(COMM_FORWARD))
        LAST_DRIVE = time.time()
    except Exception as e:
        #print("Error: %s" % str(e))
        return

def dig_bucket_ladder(serial, dev):
    global CURRENT_ACTION, DIG, MOTOR_SLEEP, COMM_FORWARD, LAST_DRIVE
    dev.claimInterface(0)
    if serial == SER_LADDER_DIG:
        dev.bulkWrite(0x02, generate_speed(0.15), timeout=1000) # Locked at 15%
    else:
        raise Exception("Unknown serial detected: %s" % serial)
    try:
        dev.bulkWrite(0x02, binascii.a2b_hex(COMM_FORWARD))
        LAST_DRIVE = time.time()
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
        try:
            serial = udev.getSerialNumber()
        except Exception:
            # TODO: Handle this better
            serial = ""
        if ((vid, pid) == (0x0483, 0xA30E)):
            motor = udev.open()
            motor.resetDevice()
            all_wheel_motors.append((serial, motor))
            """
            if serial in [SER_LADDER_DIG]:
                all_digging_motors.append((serial, motor))
            elif serial in [SER_LADDER_LIFT]:
                all_ladder_position_motors.append((serial, motor))
            elif serial in [SER_FRONT_LEFT_1, SER_BACK_LEFT_2, SER_BACK_RIGHT_3, SER_FRONT_RIGHT_4]:
                all_wheel_motors.append((serial, motor))
            else:
                raise Exception("Unable to recognize attached Spark MAX motor controller with serial number: %s" % serial)
            """
    #if len(all_digging_motors) < 1:
    #    raise Exception("Insufficient digging motors detected")
    #if len(all_ladder_position_motors) < 1:
    #    raise Exception("Insufficient ladder position motors detected")
    #if len(all_wheel_motors) < 4:
    #    raise Exception("Insufficient wheel motors detected")

def main():
    global CURRENT_SPEED, CURRENT_ACTION, STOP, FORWARD
    print("Osprey Robotics Demo Server")
    usbcontext = usb1.USBContext()
    open_dev(usbcontext)
    print("%i motors detected\n" % len(all_digging_motors+all_ladder_position_motors+all_wheel_motors))
    #command = b""
    localIP     = "0.0.0.0"
    localPort   = 20222
    bufferSize  = 9 #1024
    # Create a datagram socket
    UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    # Bind to address and ip
    UDPServerSocket.bind((localIP, localPort))
    print("UDP server up and listening")

    # Listen for incoming datagrams
    while(True):
        bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
        message = bytesAddressPair[0]
        #address = bytesAddressPair[1]
        #clientIP  = "Client IP Address:{}".format(address)
        #print(list(message))
        command = struct.unpack('>Bhhhh', message)
        # 1: Drive
        if command[0] == 1:
            WHEEL_SPEEDS = [round(float(speed*.8)/float(256),2) for speed in [command[1], command[2], command[3], command[4]]]
            print("Sending wheel speeds: %s" % str(WHEEL_SPEEDS))
            for motor in all_wheel_motors:
                t=threading.Thread(target=move_forward, args=(motor[0], motor[1], WHEEL_SPEEDS))
                t.start()
        else:
            pass
    """
           elif key == "k":
               if CURRENT_ACTION != STOP:
                   CURRENT_ACTION = STOP
                   for motor in all_digging_motors+all_ladder_position_motors+all_wheel_motors:
                       t=threading.Thread(target=kill, args=(motor[0],motor[1]))
                       t.start()
           elif key == "x":
               if CURRENT_ACTION == STOP:
                   CURRENT_ACTION = DIG
                   for motor in all_digging_motors:
                       t=threading.Thread(target=dig_bucket_ladder, args=(motor[0],motor[1]))
                       t.start()
                   time.sleep(MOTOR_SLEEP)
           elif key == "+":
               if ("%.2f" % CURRENT_SPEED) == ("%.2f" % 1.0):
                   pass
               else:
                   CURRENT_SPEED += .05
           elif key == "-":
               if ("%.2f" % CURRENT_SPEED) == ("%.2f" % -1.0):
                   pass
               else:
                   CURRENT_SPEED -= .05
           else:
               pass
        except Exception as e:
           # No input
           CURRENT_ACTION = STOP
           pass

curses.wrapper(main)
"""

main()
