# Osprey Robotics Demo for Proof of Life

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
SER_LADDER_LIFT = "206C395A5543"
SER_LADDER_DIG = "206A33544D43"
# TODO: Better interface for motor controller protocol, including timestamp/iterative-packed last bytes
POSITIVE_HEX = "000000008400058208000000XXXXXXXX000000000af69afb"
COMM_FORWARD = "00000000802c058208000000100000000000000095e92111"

# Variables
CURRENT_SPEED = 0.5 # 50% by default
CURRENT_ACTION = 0
RAMP_PHASE = 3
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
    global RAMP_PHASE
    is_positive = (speed >= 0)
    speed = abs(speed)
    current_time = time.time()
    calculated_speed = 0
    if should_ramp_up_motors(current_time, speed):
        RAMP_PHASE = 0
        if is_positive:
            calculated_speed = 0.1 # Ramp up should begin at 10%
        else:
            calculated_speed = -0.1 # Ramp up should begin at -10%
    elif (RAMP_PHASE < 2.6) and ((current_time-LAST_DRIVE) <= LAST_DRIVE_WAIT): # Should avoid any floating point issues
        RAMP_PHASE += .1
        if is_positive:
            calculated_speed = round((.1*(math.e**((math.log(((speed)/.1))/2.5)*RAMP_PHASE))),2)
        else:
            calculated_speed = -(round((.1*(math.e**((math.log(((speed)/.1))/2.5)*RAMP_PHASE))),2))
    else:
        if is_positive:
            calculated_speed = speed
        else:
            calculated_speed = -speed
    return binascii.a2b_hex(POSITIVE_HEX.replace("XXXXXXXX", str(binascii.hexlify(struct.pack('<f', calculated_speed)), "ascii")))


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

def move_forward(serial, dev):
    global CURRENT_ACTION, FORWARD, MOTOR_SLEEP, COMM_FORWARD, LAST_DRIVE
    dev.claimInterface(0)
    if serial == SER_FRONT_LEFT_1: # Front left, 1
        dev.bulkWrite(0x02, generate_speed(CURRENT_SPEED), timeout=1000)
    elif serial == SER_BACK_LEFT_2: # Back left, 2
        dev.bulkWrite(0x02, generate_speed(CURRENT_SPEED), timeout=1000)
    elif serial == SER_BACK_RIGHT_3: # Back right, 3
        dev.bulkWrite(0x02, generate_speed(-CURRENT_SPEED), timeout=1000)
    elif serial == SER_FRONT_RIGHT_4: # Front right, 4
        dev.bulkWrite(0x02, generate_speed(-CURRENT_SPEED), timeout=1000)
    else:
        raise Exception("Unknown serial detected: %s" % serial)
    try:
        dev.bulkWrite(0x02, binascii.a2b_hex(COMM_FORWARD))
        LAST_DRIVE = time.time()
    except Exception as e:
        #print("Error: %s" % str(e))
        return

def move_backward(serial, dev):
    global CURRENT_ACTION, BACKWARD, MOTOR_SLEEP, COMM_FORWARD, LAST_DRIVE
    dev.claimInterface(0)
    if serial == SER_FRONT_LEFT_1: # Front left, 1
        dev.bulkWrite(0x02, generate_speed(-CURRENT_SPEED), timeout=1000)
    elif serial == SER_BACK_LEFT_2: # Back left, 2
        dev.bulkWrite(0x02, generate_speed(-CURRENT_SPEED), timeout=1000)
    elif serial == SER_BACK_RIGHT_3: # Back right, 3
        dev.bulkWrite(0x02, generate_speed(CURRENT_SPEED), timeout=1000)
    elif serial == SER_FRONT_RIGHT_4: # Front right, 4
        dev.bulkWrite(0x02, generate_speed(CURRENT_SPEED), timeout=1000)
    else:
        raise Exception("Unknown serial detected: %s" % serial)
    try:
        dev.bulkWrite(0x02, binascii.a2b_hex(COMM_FORWARD))
        LAST_DRIVE = time.time()
    except Exception as e:
        #print("Error: %s" % str(e))
        return

def spin_left(serial, dev):
    global CURRENT_ACTION, LEFT, MOTOR_SLEEP, COMM_FORWARD, LAST_DRIVE
    dev.claimInterface(0)
    if serial == SER_FRONT_LEFT_1: # Front left, 1
        dev.bulkWrite(0x02, generate_speed(-CURRENT_SPEED), timeout=1000)
    elif serial == SER_BACK_LEFT_2: # Back left, 2
        dev.bulkWrite(0x02, generate_speed(-CURRENT_SPEED), timeout=1000)
    elif serial == SER_BACK_RIGHT_3: # Back right, 3
        dev.bulkWrite(0x02, generate_speed(-CURRENT_SPEED), timeout=1000)
    elif serial == SER_FRONT_RIGHT_4: # Front right, 4
        dev.bulkWrite(0x02, generate_speed(-CURRENT_SPEED), timeout=1000)
    else:
        raise Exception("Unknown serial detected: %s" % serial)
    try:
        dev.bulkWrite(0x02, binascii.a2b_hex(COMM_FORWARD))
        LAST_DRIVE = time.time()
    except Exception as e:
        #print("Error: %s" % str(e))
        return

def spin_right(serial, dev):
    global CURRENT_ACTION, RIGHT, MOTOR_SLEEP, COMM_FORWARD, LAST_DRIVE
    dev.claimInterface(0)
    if serial == SER_FRONT_LEFT_1: # Front left, 1
        dev.bulkWrite(0x02, generate_speed(CURRENT_SPEED), timeout=1000)
    elif serial == SER_BACK_LEFT_2: # Back left, 2
        dev.bulkWrite(0x02, generate_speed(CURRENT_SPEED), timeout=1000)
    elif serial == SER_BACK_RIGHT_3:  # Back right, 3
        dev.bulkWrite(0x02, generate_speed(CURRENT_SPEED), timeout=1000)
    elif serial == SER_FRONT_RIGHT_4: # Front right, 4
        dev.bulkWrite(0x02, generate_speed(CURRENT_SPEED), timeout=1000)
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
        dev.bulkWrite(0x02, generate_speed(0.1), timeout=1000) # Locked at 10%
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
        dev.bulkWrite(0x02, generate_speed(-0.1), timeout=1000) # Locked at -10%
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
        dev.bulkWrite(0x02, generate_speed(0.1), timeout=1000) # Locked at 10%
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
        serial = udev.getSerialNumber()
        if ((vid, pid) == (0x0483, 0xA30E)):
            motor = udev.open()
            motor.resetDevice()
            if serial in [SER_LADDER_DIG]:
                all_digging_motors.append((serial, motor))
            elif serial in [SER_LADDER_LIFT]:
                all_ladder_position_motors.append((serial, motor))
            elif serial in [SER_FRONT_LEFT_1, SER_BACK_LEFT_2, SER_BACK_RIGHT_3, SER_FRONT_RIGHT_4]:
                all_wheel_motors.append((serial, motor))
            else:
                raise Exception("Unable to recognize attached Spark MAX motor controller with serial number: %s" % serial)
    if len(all_digging_motors) < 1:
        raise Exception("Insufficient digging motors detected")
    #if len(all_ladder_position_motors) < 1:
    #    raise Exception("Insufficient ladder position motors detected")
    if len(all_wheel_motors) < 4:
        raise Exception("Insufficient wheel motors detected")

def main(win):
    global CURRENT_SPEED, CURRENT_ACTION, STOP, FORWARD
    win.nodelay(True)
    key=""
    win.clear()
    win.addstr("Osprey Robotics Demo\n")
    usbcontext = usb1.USBContext()
    open_dev(usbcontext)
    win.addstr("%i motors detected\n" % len(all_digging_motors+all_ladder_position_motors+all_wheel_motors))
    win.addstr("Ready, press any key to continue\n")
    while True:
        try:
            win.getkey()
            break
        except Exception as e:
            # No input
            pass
    #print(all_digging_motors+all_ladder_position_motors+all_wheel_motors)
    win.clear()
    win.addstr("Controls:\n")
    win.addstr("[q] Quit [w] Forward [a] Left [s] Backward [d] Right [x] Dig [k] Kill motors [+] Speed up [-] Slow down\n")
    win.addstr("Speed: %i%%\n" % (CURRENT_SPEED*100))
    win.addstr("Detected key: ")
    while True:
        try:
           key = win.getkey()
           if key == "q":
              break
           elif key == "w":
               if CURRENT_ACTION == STOP:
                   CURRENT_ACTION = FORWARD
                   for motor in all_wheel_motors:
                       t=threading.Thread(target=move_forward, args=(motor[0],motor[1]))
                       t.start()
                   time.sleep(MOTOR_SLEEP)
           elif key == "a":
               if CURRENT_ACTION == STOP:
                   CURRENT_ACTION = LEFT
                   for motor in all_wheel_motors:
                       t=threading.Thread(target=spin_left, args=(motor[0],motor[1]))
                       t.start()
                   time.sleep(MOTOR_SLEEP)
           elif key == "s":
               if CURRENT_ACTION == STOP:
                   CURRENT_ACTION = BACKWARD
                   for motor in all_wheel_motors:
                       t=threading.Thread(target=move_backward, args=(motor[0],motor[1]))
                       t.start()
                   time.sleep(MOTOR_SLEEP)
           elif key == "d":
               if CURRENT_ACTION == STOP:
                   CURRENT_ACTION = RIGHT
                   for motor in all_wheel_motors:
                       t=threading.Thread(target=spin_right, args=(motor[0],motor[1]))
                       t.start()
                   time.sleep(MOTOR_SLEEP)
           elif key == "k":
               if CURRENT_ACTION != STOP:
                   CURRENT_ACTION = STOP
                   for motor in all_digging_motors+all_ladder_position_motors+all_wheel_motors:
                       t=threading.Thread(target=kill, args=(motor[0],motor[1]))
                       t.start()
           elif key == "x":
               if CURRENT_ACTION != STOP:
                   CURRENT_ACTION = DIG
                   for motor in all_digging_motors:
                       t=threading.Thread(target=dig_bucket_ladder, args=(motor[0],motor[1]))
                       t.start()
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
           win.clear()
           win.addstr("Controls:\n")
           win.addstr("[q] Quit [w] Forward [a] Left [s] Backward [d] Right [x] Dig [k] Kill motors [+] Speed up [-] Slow down\n")
           win.addstr("Speed: %i%%\n" % (CURRENT_SPEED*100))
           win.addstr("Detected key: ")
           win.addstr(repr(str(key)))
        except Exception as e:
           # No input
           CURRENT_ACTION = STOP
           pass

curses.wrapper(main)
