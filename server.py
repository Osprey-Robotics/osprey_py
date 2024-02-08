#  Copyright 2024 Osprey Robotics - UNF
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#

import serial as ser
import socket
import binascii
import struct
import time
import threading
import usb1
import math
import os
import RPi.GPIO as GPIO

# Constants
STOP = 0
FORWARD = 1
LEFT = 2
RIGHT = 3
BACKWARD = 4
UP = 5
DOWN = 6
DIG = 7
BUTTON_A_ON = 0
BUTTON_A_OFF = 100
BUTTON_B_ON = 1
BUTTON_B_OFF = 101
BUTTON_X_ON = 2
BUTTON_X_OFF = 102
BUTTON_Y_ON = 3
BUTTON_Y_OFF = 103
BUTTON_LB_ON = 4
BUTTON_RB_ON = 5
BUTTON_BACK_ON = 6
BUTTON_BACK_OFF = 106
BUTTON_START_ON = 7
BUTTON_START_OFF = 107
BUTTON_LT_CLICK_ON = 9
BUTTON_LT_CLICK_OFF = 109
BUTTON_RT_CLICK_ON = 10
BUTTON_RT_CLICK_OFF = 110
MOTOR_SLEEP = 0.05 #0.4
LIMIT_SWITCH_WAIT = 1
RIGHT_SIDE = 1
LEFT_SIDE = 2
LAST_DRIVE_WAIT = 1.0
SER_FRONT_LEFT_1 = "206D33614D43"
SER_BACK_LEFT_2 = "2061376C4243"
SER_FRONT_RIGHT_3 = "206B336B4E55"
SER_BACK_RIGHT_4 = "205A336B4E55"
SER_LADDER_DIG = "206A33544D43"
SER_LADDER_LIFT = "206C395A5543"
SER_DEPOSITION = "205D39515543"
RELAY_1 = 26
RELAY_2 = 20
LIMIT_BUCKET_LADDER_TOP = 9
LIMIT_BUCKET_LADDER_BOTTOM = 10
LIMIT_DEPOSITION_FORWARD = 5
LIMIT_ACTUATOR_EXTENDED = 12
LIMIT_DEPOSITION_BACK = 13

# TODO: Better interface for motor controller protocol, including timestamp/iterative-packed last bytes
POSITIVE_HEX = "000000008400058208000000XXXXXXXX000000000af69afb"
COMM_FORWARD = "00000000802c058208000000100000000000000095e92111"

# Variables
CURRENT_ACTION = 0
LAST_DRIVE = 0
RAMP_PHASE = 0
all_right_wheel_motors = []
all_left_wheel_motors = []
all_ladder_position_motors = []
all_digging_motors = []
all_deposition_motors = []
position_servo_pitch = 0
position_servo_yaw = 0
limit_switch_debounce_timer = 1
ignore_limit_switches = False

def is_limit_switch_pressed(limit_switch_id):
    global LIMIT_SWITCH_WAIT, ignore_limit_switches
    if ignore_limit_switches == True:
        return False
    return GPIO.input(limit_switch_id, GPIO.HIGH)
    # return ((time.time()-GPIO.input(limit_switch_id, GPIO.HIGH)) <= LIMIT_SWITCH_WAIT)

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
    if speed == 0:
        calculated_speed = 0
    elif should_ramp_up_motors(current_time, speed):
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
    elif serial == SER_FRONT_RIGHT_3: # Front right, 3
        dev.bulkWrite(0x02, generate_speed(-0), timeout=1000)
    elif serial == SER_BACK_RIGHT_4: # Back right, 4
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

def drive(serial, dev, SIDE_OF_ROBOT, WHEEL_SPEEDS):
    global CURRENT_ACTION, FORWARD, MOTOR_SLEEP, COMM_FORWARD, LAST_DRIVE, RIGHT_SIDE, LEFT_SIDE
    dev.claimInterface(0)
    if SIDE_OF_ROBOT == RIGHT_SIDE:
        if serial == SER_FRONT_RIGHT_3: # Front right, 3
            dev.bulkWrite(0x02, generate_speed(-WHEEL_SPEEDS[0]), timeout=1000)
        elif serial == SER_BACK_RIGHT_4: # Back right, 4
            dev.bulkWrite(0x02, generate_speed(-WHEEL_SPEEDS[0]), timeout=1000)
        else:
            # Don't address
            pass
    elif SIDE_OF_ROBOT == LEFT_SIDE:
        if serial == SER_FRONT_LEFT_1: # Front left, 1
            dev.bulkWrite(0x02, generate_speed(WHEEL_SPEEDS[0]), timeout=1000)
        elif serial == SER_BACK_LEFT_2: # Back left, 2
            dev.bulkWrite(0x02, generate_speed(WHEEL_SPEEDS[0]), timeout=1000)
        else:
            # Don't address
            pass
    else:
        raise Exception("Unknown serial detected: %s" % serial)
    try:
        dev.bulkWrite(0x02, binascii.a2b_hex(COMM_FORWARD))
        LAST_DRIVE = time.time()
    except Exception as e:
        #print("Error: %s" % str(e))
        return

def actuate_motor(serialA, serialB, dev, speed):
    """
    Run a motor at a given speed based on the serial numbers

    :param serialA          the serial to be matched the variable
    :param serialD          the constant serial to match the variable against
    :param dev              usb device handle
    :param speed            the speed to run the motor at
    """
    global CURRENT_ACTION, DIG, MOTOR_SLEEP, COMM_FORWARD, LAST_DRIVE
    dev.claimInterface(0)
    if serialA == serialB:
        dev.bulkWrite(0x02, generate_speed(speed), timeout=1000)
    else:
        raise Exception("Unknown serial detected: %s" % serialA)
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
            if serial in [SER_FRONT_LEFT_1, SER_BACK_LEFT_2]:
                all_left_wheel_motors.append((serial, motor))
            elif serial in [SER_FRONT_RIGHT_3, SER_BACK_RIGHT_4]:
                all_right_wheel_motors.append((serial, motor))
            elif serial in [SER_LADDER_LIFT]:
                all_ladder_position_motors.append((serial, motor))
            elif serial in [SER_LADDER_DIG]:
                all_digging_motors.append((serial, motor))
            elif serial in [SER_DEPOSITION]:
                all_deposition_motors.append((serial, motor))
            else:
                #raise Exception("Unable to recognize attached Spark MAX motor controller with serial number: %s" % serial)
                pass
    # TODO: Recursively attempt to detect motors until the target number of motors have been reached or an exception has been raised (e.g. max attempts)
    if len(all_deposition_motors) < 1:
        raise Exception("Insufficient deposition motors detected")
    if len(all_digging_motors) < 1:
        raise Exception("Insufficient digging motors detected")
    if len(all_ladder_position_motors) < 1:
        raise Exception("Insufficient ladder position motors detected")
    if len(all_left_wheel_motors+all_right_wheel_motors) < 4:
        raise Exception("Insufficient wheel motors detected")

def main():
    global CURRENT_ACTION, STOP, FORWARD, RIGHT_SIDE, LEFT_SIDE, BUTTON_START_ON, all_digging_motors, all_ladder_position_motors, all_right_wheel_motors, all_left_wheel_motors, all_deposition_motors, position_servo_pitch, position_servo_yaw, ignore_limit_switches
    print("Osprey Robotics Control Server")
    usbcontext = usb1.USBContext()
    open_dev(usbcontext)
    print("%i motors detected (expect 7)\n" % len(all_digging_motors+all_ladder_position_motors+all_deposition_motors+all_right_wheel_motors+all_left_wheel_motors))
    #command = b""
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RELAY_1, GPIO.OUT)
    GPIO.setup(RELAY_2, GPIO.OUT)

    # prepare limit switches
    GPIO.setup(LIMIT_BUCKET_LADDER_TOP, GPIO.IN)
    GPIO.setup(LIMIT_BUCKET_LADDER_BOTTOM, GPIO.IN)
    GPIO.setup(LIMIT_DEPOSITION_FORWARD, GPIO.IN)
    GPIO.setup(LIMIT_ACTUATOR_EXTENDED, GPIO.IN)
    GPIO.setup(LIMIT_DEPOSITION_BACK, GPIO.IN)

    localIP     = "0.0.0.0"
    localPort   = 20222
    bufferSize  = 7 #1024
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
        command = struct.unpack('>Bh', message)
        #print(command) # DEBUG
        # 0: Brake
        # 1: Drive right side
        if command[0] == 1:
            #WHEEL_SPEEDS = [round(float(speed*.8)/float(128),2) for speed in [command[1], command[2]]]
            WHEEL_SPEEDS = [round(float(speed*.8)/float(128),2) for speed in [command[1]]]
            print("Sending right wheel speeds: %s" % str(WHEEL_SPEEDS))
            for motor in all_right_wheel_motors:
                t=threading.Thread(target=drive, args=(motor[0], motor[1], RIGHT_SIDE, WHEEL_SPEEDS))
                t.start()
        # 2: Drive left side
        elif command[0] == 2:
            #WHEEL_SPEEDS = [round(float(speed*.8)/float(128),2) for speed in [command[1], command[2]]]
            WHEEL_SPEEDS = [round(float(speed*.8)/float(128),2) for speed in [command[1]]]
            print("Sending left wheel speeds: %s" % str(WHEEL_SPEEDS))
            for motor in all_left_wheel_motors:
                t=threading.Thread(target=drive, args=(motor[0], motor[1], LEFT_SIDE, WHEEL_SPEEDS))
                t.start()
        # 3: Button press event
        elif command[0] == 3:
            #WHEEL_SPEEDS = [round(float(speed*.8)/float(128),2) for speed in [command[1], command[2]]]
            if command[1] == BUTTON_START_ON:
                print("Motor reset requested")
                for motor in all_left_wheel_motors+all_right_wheel_motors+all_ladder_position_motors+all_digging_motors+all_deposition_motors:
                    try:
                        motor[1].close()
                    except Exception as e:
                        print("Could not cleanly close motor controller with serial number %s: %s" % (motor[0], e))
                all_left_wheel_motors=[]
                all_right_wheel_motors=[]
                usbcontext = usb1.USBContext()
                open_dev(usbcontext)
                print("Motor reset complete")
            elif (command[1] == BUTTON_A_ON) and \
                 (not is_limit_switch_pressed(LIMIT_DEPOSITION_FORWARD)):
                # Deposition bucket forward
                print("Deposition forward")
                t=threading.Thread(target=actuate_motor,
                                   args=(all_deposition_motors[0][0],
                                         SER_DEPOSITION,
                                         all_deposition_motors[0][1],
                                         -0.30)) # Locked at -30%
                t.start()
            elif (command[1] == BUTTON_B_ON) and \
                 (not is_limit_switch_pressed(LIMIT_DEPOSITION_BACK)):
                # Deposition bucket reverse
                print("Deposition reverse")
                t=threading.Thread(target=actuate_motor,
                                   args=(all_deposition_motors[0][0],
                                         SER_DEPOSITION,
                                         all_deposition_motors[0][1],
                                         0.30)) # Locked at 30%
                t.start()
            elif (command[1] == BUTTON_A_OFF) or (command[1] == BUTTON_B_OFF):
                print("Deposition stop")
                t=threading.Thread(target=actuate_motor,
                                   args=(all_deposition_motors[0][0],
                                         SER_DEPOSITION,
                                         all_deposition_motors[0][1],
                                         0))
                t.start()
            elif command[1] == BUTTON_Y_ON:
                # Linear actuator forward
                print("Actuator forward")
                GPIO.output(RELAY_1, GPIO.HIGH)
            elif command[1] == BUTTON_X_ON:
                # Linear actuator reverse
                print("Actuator reverse")
                GPIO.output(RELAY_2, GPIO.HIGH)
            elif (command[1] == BUTTON_X_OFF) or (command[1] == BUTTON_Y_OFF):
                print("Actuator stop")
                GPIO.output(RELAY_1, GPIO.LOW)
                GPIO.output(RELAY_2, GPIO.LOW)
            elif command[1] == BUTTON_BACK_ON:
                # Toggle limit switches
                print("Toggling limit switches")
                ignore_limit_switches = not ignore_limit_switches
            elif (command[1] == BUTTON_LB_ON) and \
                 (not is_limit_switch_pressed(LIMIT_BUCKET_LADDER_TOP)):
                # Bucket ladder up
                t=threading.Thread(target=actuate_motor,
                                   args=(all_ladder_position_motors[0][0],
                                         SER_LADDER_LIFT,
                                         all_ladder_position_motors[0][1],
                                         0.30)) # Locked at 30%
                t.start()
            elif (command[1] == BUTTON_RB_ON) and \
                 (not is_limit_switch_pressed(LIMIT_BUCKET_LADDER_BOTTOM)):
                # Bucket ladder down
                t=threading.Thread(target=actuate_motor,
                                   args=(all_ladder_position_motors[0][0],
                                         SER_LADDER_LIFT,
                                         all_ladder_position_motors[0][1],
                                         -0.30)) # Locked at -30%
                t.start()
            else:
                #print("Received button event: %i" % command[1])
                pass
        elif command[0] == 4:
            degree = command[1]
            position_servo_pitch += degree
            if position_servo_pitch < 0:
                position_servo_pitch = 0
            elif position_servo_pitch > 180:
                position_servo_pitch = 180
            print("Servo 2: %i" % (position_servo_pitch))
        elif command[0] == 5:
            degree = command[1]
            position_servo_yaw += degree
            if position_servo_yaw < 0:
                position_servo_yaw = 0
            elif position_servo_yaw > 180:
                position_servo_yaw = 180
            print("Servo 1: %i" % (position_servo_yaw))
        elif command[0] == 6:
            speed = round(float(command[1]*1.0)/float(255),2)
            print("Bucket ladder speed: %s" % (str(speed)))
            t=threading.Thread(target=actuate_motor,
                                args=(all_digging_motors[0][0],
                                      SER_LADDER_DIG,
                                      all_digging_motors[0][1],
                                      speed))
            t.start()
        else:
            pass
    """
           elif key == "k":
               if CURRENT_ACTION != STOP:
                   CURRENT_ACTION = STOP
                   for motor in all_digging_motors+all_ladder_position_motors+all_right_wheel_motors+all_left_wheel_motors:
                       t=threading.Thread(target=kill, args=(motor[0],motor[1]))
                       t.start()
        except Exception as e:
           # No input
           CURRENT_ACTION = STOP
           pass
"""

main()
