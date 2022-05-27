# Osprey Robotics Controller Client
# Note: "Bonus speed" affects wheels on each side of the robot
#       So running the right side on 127 power will cause the left side to immediately catch up to 127 power

# Imports
import asyncio
import glob
import socket
import struct
import sys
import threading
import time
import http.client

def find_the_joule(jouleHostname):
    global routerIP
    try:
        print("Trying to reach the router (%s)" % routerIP)
        connection = http.client.HTTPConnection(routerIP)
        headers = {'Authorization': 'Basic YWRtaW46b3NwcmV5cm9ib3RpY3M='}
        connection.request('GET', '/DHCPTable.asp', headers=headers)
        response = connection.getresponse()
        print("Reached the router (%s)" % routerIP)
    except Exception:
        print("Could not reach the router")
    entry = [l for l in response.read().decode().splitlines() if jouleHostname in l]
    jouleIP = None
    try:
        jouleIP = entry[0].split("'")[3]
        print("Found Joule IP: %s" % jouleIP)
    except Exception:
        jouleIP = None
    if "--ip" in sys.argv:
        try:
            ip_argv = sys.argv.index("--ip")
            jouleIP = sys.argv[ip_argv+1]
        except Exception:
            jouleIP = None
    if jouleIP is None:
        print("Couldn't find Joule")
        sys.exit(1)
    return jouleIP

# Program global variables
current_speed_right = 0
current_speed_left = 0
current_speed_bucket_ladder = 0
COMMAND_WHEELS_STOP = 0
COMMAND_RIGHT_WHEELS = 1
COMMAND_LEFT_WHEELS = 2
COMMAND_BUTTON_PRESS = 3
COMMAND_LR_SERVO = 4
COMMAND_UD_SERVO = 5
COMMAND_BUCKET_LADDER = 6
BUTTON_A_STATE = 0 # 0 is off, 1 is on
BUTTON_B_STATE = 0 # 0 is off, 1 is on
BUTTON_LB_STATE = 0 # 0 is off, 1 is on
BUTTON_RB_STATE = 0 # 0 is off, 1 is on
jouleHostname = 'ospreyrobotics'
routerIP = '192.168.1.1'
jouleIP = find_the_joule(jouleHostname)
serverAddressPort = (jouleIP, 20222)
INPUT_TYPE = 0
new_commands = []
# Bandwidth saving threshold, 0-127
# Higher numbers equate to saving more bandwidth at the expense of less speeds
bandwidth_saving_threshold = 0
# "Bonus speed": Prevent robot from accelerating too quickly by incrementing speed from 70 if 127 is held, and keeping all other speeds 45% slower (25% slower for the bucket ladder)
speed_factor=0.55
speed_factor_bucket_ladder=0.78
bonus_speed=0
bonus_speed_bucket_ladder=0
bonus_speed_max=57

# Controller global variables
BUTTON = 1
JOYSTICK = 2
BUTTON_A_ON = 0
BUTTON_A_OFF = 100
BUTTON_B_ON = 1
BUTTON_B_OFF = 101
BUTTON_X_ON = 2
BUTTON_X_OFF = 102
BUTTON_Y_ON = 3
BUTTON_Y_OFF = 103
BUTTON_LB_ON = 4
BUTTON_LB_OFF = 104
BUTTON_RB_ON = 5
BUTTON_RB_OFF = 105
BUTTON_BACK_ON = 6
BUTTON_BACK_OFF = 106
BUTTON_START_ON = 7
BUTTON_START_OFF = 107
BUTTON_LT_CLICK_ON = 9
BUTTON_LT_CLICK_OFF = 109
BUTTON_RT_CLICK_ON = 10
BUTTON_RT_CLICK_OFF = 110
JOYSTICK_RT = 5
JOYSTICK_RJ_UD = 4
JOYSTICK_LT = 2
JOYSTICK_LJ_UD = 1
DPAD_LU = 128
DPAD_RD = 127
# DPAD registration
DPAD_LEFT = 6
DPAD_RIGHT = 6
DPAD_UP = 7
DPAD_DOWN = 7
# Psuedo-button events
DPAD_LEFT_ON = 11
DPAD_LEFT_OFF = 111
DPAD_RIGHT_ON = 12
DPAD_RIGHT_OFF = 112
DPAD_UP_ON = 13
DPAD_UP_OFF = 113
DPAD_DOWN_ON = 14
DPAD_DOWN_OFF = 114

# Data streams
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
try:
    controller_device = open(glob.glob("/dev/input/by-id/usb-Logitech_Gamepad_F310_????????-joystick")[0], "rb")
except Exception:
    print("Could not find a controller connected to this system")
    sys.exit(1)

def update_speed(wheel_side, new_speed):
        global current_speed_right, current_speed_left, current_speed_bucket_ladder
        if wheel_side == COMMAND_RIGHT_WHEELS:
                current_speed_right = new_speed
        elif wheel_side == COMMAND_LEFT_WHEELS:
                current_speed_left = new_speed
        elif wheel_side == COMMAND_BUCKET_LADDER:
                current_speed_bucket_ladder = new_speed
        else:
                print("Unrecognized motors")

def possibly_update_speed(wheel_side, new_speed):
        global current_speed_right, current_speed_left, current_speed_bucket_ladder, bandwidth_saving_threshold, speed_factor, speed_factor_bucket_ladder, bonus_speed, bonus_speed_bucket_ladder
        if wheel_side == COMMAND_BUCKET_LADDER:
            new_speed = round(new_speed*speed_factor_bucket_ladder)
        else:
            new_speed = round(new_speed*speed_factor)
        orig_speed = 0
        if ((wheel_side != COMMAND_BUCKET_LADDER) and (abs(new_speed) <= 20)) or ((wheel_side == COMMAND_BUCKET_LADDER) and (abs(new_speed) <= 40)):
                if wheel_side == COMMAND_BUCKET_LADDER:
                    bonus_speed_bucket_ladder = 0
                else:
                    bonus_speed = 0
                # Make sure joystick goes to zero
                update_speed(wheel_side, 0)
                return
        if wheel_side == COMMAND_RIGHT_WHEELS:
                orig_speed = current_speed_right
        elif wheel_side == COMMAND_LEFT_WHEELS:
                orig_speed = current_speed_left
        elif wheel_side == COMMAND_BUCKET_LADDER:
                orig_speed = current_speed_bucket_ladder
        else:
                print("Unrecognized motors")
        if ((abs(orig_speed)+bandwidth_saving_threshold) <= abs(new_speed)) or ((abs(orig_speed)-bandwidth_saving_threshold) >= abs(new_speed)):
                update_speed(wheel_side, new_speed)

# Reads commands from the controller
def thread_function(name):
        global controller_device, new_commands
        while True:
                command=list(controller_device.read(8))
                #print(command) # DEBUG
                # Prevent the buffer from getting too long
                new_commands = [command] + new_commands
                #print(new_commands) # DEBUG

# Sends commands to the server
async def send_commands(button=None):
        global UDPClientSocket, serverAddressPort, current_speed_right, current_speed_left, current_speed_bucket_ladder, bonus_speed, bonus_speed_bucket_ladder
        if button == BUTTON_START_ON:
                print("Requesting motor reset")
                UDPClientSocket.sendto(struct.pack('>Bh', COMMAND_BUTTON_PRESS, BUTTON_START_ON), serverAddressPort)
                wait_seconds = 5
                while wait_seconds >= 0:
                        print("\rPlease wait (%s)" % (str(wait_seconds).zfill(2)), end='')
                        time.sleep(1)
                        wait_seconds -= 1
                print("\rMotors should be reset, resume driving when ready")
                return
        if button == BUTTON_X_ON:
                print("Sending linear actuator reverse start")
                UDPClientSocket.sendto(struct.pack('>Bh', COMMAND_BUTTON_PRESS, BUTTON_X_ON), serverAddressPort)
                return
        if button == BUTTON_X_OFF:
                print("Sending linear actuator reverse stop")
                UDPClientSocket.sendto(struct.pack('>Bh', COMMAND_BUTTON_PRESS, BUTTON_X_OFF), serverAddressPort)
                return
        if button == BUTTON_Y_ON:
                print("Sending linear actuator forward start")
                UDPClientSocket.sendto(struct.pack('>Bh', COMMAND_BUTTON_PRESS, BUTTON_Y_ON), serverAddressPort)
                return
        if button == BUTTON_Y_OFF:
                print("Sending linear actuator forward stop")
                UDPClientSocket.sendto(struct.pack('>Bh', COMMAND_BUTTON_PRESS, BUTTON_Y_OFF), serverAddressPort)
                return
        if button == BUTTON_BACK_ON:
                print("Sending limit switch toggle")
                UDPClientSocket.sendto(struct.pack('>Bh', COMMAND_BUTTON_PRESS, BUTTON_BACK_ON), serverAddressPort)
                return
        if button == DPAD_LEFT_ON:
            print("Sending DPAD left")
            degree = 5
            UDPClientSocket.sendto(struct.pack('>Bh', COMMAND_LR_SERVO, degree), serverAddressPort)
            return
        if button == DPAD_RIGHT_ON:
            print("Sending DPAD right")
            degree = -5
            UDPClientSocket.sendto(struct.pack('>Bh', COMMAND_LR_SERVO, degree), serverAddressPort)
            return
        if button == DPAD_UP_ON:
            print("Sending DPAD up")
            degree = -5
            UDPClientSocket.sendto(struct.pack('>Bh', COMMAND_UD_SERVO, degree), serverAddressPort)
            return
        if button == DPAD_DOWN_ON:
            print("Sending DPAD down")
            degree = 5
            UDPClientSocket.sendto(struct.pack('>Bh', COMMAND_UD_SERVO, degree), serverAddressPort)
            return
        if abs(current_speed_right) > 0:
                effective_bonus_speed = bonus_speed if ((current_speed_right>0) == True) else -bonus_speed
                speed_sign = "+" if ((current_speed_right>0) == True) else "-"
                #print("\rSending right speed: %s%s (%s)" % (speed_sign, str(abs(current_speed_right)).zfill(3), str(time.time())), end = '')
                print("Sending right speed: %s%s (%s)" % (speed_sign, str(abs(current_speed_right+effective_bonus_speed)).zfill(3), str(time.time())))
                UDPClientSocket.sendto(struct.pack('>Bh', COMMAND_RIGHT_WHEELS, current_speed_right+effective_bonus_speed), serverAddressPort)
        if abs(current_speed_left) > 0:
                effective_bonus_speed = bonus_speed if ((current_speed_left>0) == True) else -bonus_speed
                speed_sign = "+" if ((current_speed_left>0) == True) else "-"
                #print("\rSending left speed:  %s%s (%s)" % (speed_sign, str(abs(current_speed_left)).zfill(3), str(time.time())), end = '')
                print("Sending left speed:  %s%s (%s)" % (speed_sign, str(abs(current_speed_left+effective_bonus_speed)).zfill(3), str(time.time())))
                UDPClientSocket.sendto(struct.pack('>Bh', COMMAND_LEFT_WHEELS, current_speed_left+effective_bonus_speed), serverAddressPort)
        if abs(current_speed_bucket_ladder) > 0:
                effective_bonus_speed = bonus_speed_bucket_ladder if ((current_speed_bucket_ladder>0) == True) else -bonus_speed_bucket_ladder
                speed_sign = "+" if ((current_speed_bucket_ladder>0) == True) else "-"
                #print("\rSending bucket ladder speed:  %s%s (%s)" % (speed_sign, str(abs(current_speed_bucket_ladder)).zfill(3), str(time.time())), end = '')
                print("Sending bucket ladder speed:  %s%s (%s)" % (speed_sign, str(abs(current_speed_bucket_ladder+effective_bonus_speed)).zfill(3), str(time.time())))
                UDPClientSocket.sendto(struct.pack('>Bh', COMMAND_BUCKET_LADDER, current_speed_bucket_ladder+effective_bonus_speed), serverAddressPort)
        if BUTTON_A_STATE == 1:
                print("Sending deposition bucket forward")
                UDPClientSocket.sendto(struct.pack('>Bh', COMMAND_BUTTON_PRESS, BUTTON_A_ON), serverAddressPort)
        if BUTTON_B_STATE == 1:
                print("Sending deposition bucket reverse")
                UDPClientSocket.sendto(struct.pack('>Bh', COMMAND_BUTTON_PRESS, BUTTON_B_ON), serverAddressPort)
        if BUTTON_LB_STATE == 1:
                print("Sending bucket ladder up")
                UDPClientSocket.sendto(struct.pack('>Bh', COMMAND_BUTTON_PRESS, BUTTON_LB_ON), serverAddressPort)
        if BUTTON_RB_STATE == 1:
                print("Sending bucket ladder down")
                UDPClientSocket.sendto(struct.pack('>Bh', COMMAND_BUTTON_PRESS, BUTTON_RB_ON), serverAddressPort)
        if (current_speed_right == 0) and (current_speed_left == 0) and (current_speed_bucket_ladder == 0) and (button is None) and (BUTTON_A_STATE == 0) and (BUTTON_B_STATE == 0) and (BUTTON_LB_STATE == 0) and (BUTTON_RB_STATE == 0):
                print("Unrecognized action")
        return

# Parse commands from controller
async def parse_command(loop):
        global current_speed_right, current_speed_left, current_speed_bucket_ladder, new_commands, bonus_speed, bonus_speed_bucket_ladder, bonus_speed_max, BUTTON_A_STATE, BUTTON_B_STATE, BUTTON_LB_STATE, BUTTON_RB_STATE
        while True:
                if len(new_commands) > 0:
                        if bonus_speed > 0:
                                bonus_speed -= 1
                        if bonus_speed_bucket_ladder > 0:
                                bonus_speed_bucket_ladder -= 1
                        command = new_commands.pop()
                else:
                        if (bonus_speed < bonus_speed_max) and ((abs(current_speed_right) >= 60) or (abs(current_speed_left) >= 60)):
                                bonus_speed += 1
                        if (bonus_speed_bucket_ladder < bonus_speed_max) and (abs(current_speed_bucket_ladder) >= 100):
                                bonus_speed_bucket_ladder += 1
                        if (abs(current_speed_right) > 0) or (abs(current_speed_left) > 0) or (abs(current_speed_bucket_ladder) > 0) or (BUTTON_A_STATE == 1) or (BUTTON_B_STATE == 1) or (BUTTON_LB_STATE == 1) or (BUTTON_RB_STATE == 1):
                                await send_commands()
                        await asyncio.sleep(.01) # DEBUG
                        continue
                INPUT_TYPE = command[-2]
                INPUT_ID = command[-1]
                if INPUT_TYPE == BUTTON:
                        button_pressed = command[-4] == 1
                        if (INPUT_ID == BUTTON_A_ON):
                                if button_pressed:
                                        #print("\nA BUTTON PRESSED")
                                        BUTTON_A_STATE = 1
                                        await send_commands(BUTTON_A_ON)
                                else:
                                        #print("\nA BUTTON RELEASED")
                                        BUTTON_A_STATE = 0
                                        await send_commands(BUTTON_A_OFF)
                        elif (INPUT_ID == BUTTON_B_ON):
                                if button_pressed:
                                        #print("\nB BUTTON PRESSED")
                                        BUTTON_B_STATE = 1
                                        await send_commands(BUTTON_B_ON)
                                else:
                                        #print("\nB BUTTON RELEASED")
                                        BUTTON_B_STATE = 0
                                        await send_commands(BUTTON_B_OFF)
                        elif (INPUT_ID == BUTTON_X_ON):
                                if button_pressed:
                                        #print("\nX BUTTON PRESSED")
                                        await send_commands(BUTTON_X_ON)
                                else:
                                        #print("\nX BUTTON RELEASED")
                                        await send_commands(BUTTON_X_OFF)
                        elif (INPUT_ID == BUTTON_Y_ON):
                                if button_pressed:
                                        #print("\nY BUTTON PRESSED")
                                        await send_commands(BUTTON_Y_ON)
                                else:
                                        #print("\nY BUTTON RELEASED")
                                        await send_commands(BUTTON_Y_OFF)
                        elif (INPUT_ID == BUTTON_LB_ON):
                                if button_pressed:
                                        #print("\nLB BUTTON PRESSED")
                                        BUTTON_LB_STATE = 1
                                        await send_commands(BUTTON_LB_ON)
                                else:
                                        #print("\nLB BUTTON RELEASED")
                                        BUTTON_LB_STATE = 0
                        elif (INPUT_ID == BUTTON_RB_ON):
                                if button_pressed:
                                        #print("\nRB BUTTON PRESSED")
                                        BUTTON_RB_STATE = 1
                                        await send_commands(BUTTON_RB_ON)
                                else:
                                        #print("\nRB BUTTON RELEASED")
                                        BUTTON_RB_STATE = 0
                        elif (INPUT_ID == BUTTON_BACK_ON) and button_pressed:
                                #print("\nBACK BUTTON PRESSED")
                                await send_commands(BUTTON_BACK_ON)
                        elif (INPUT_ID == BUTTON_START_ON) and button_pressed:
                                #print("\nSTART BUTTON")
                                await send_commands(BUTTON_START_ON)
                        #elif not button_pressed:
                        #        pass
                        else:
                                print("\nOTHER BUTTON")
                elif INPUT_TYPE == JOYSTICK:
                        if command[5] == DPAD_LU:  # D-Pad L/U
                                if command[7] == DPAD_LEFT:  # Left
                                    #print("\nLeft DPAD")
                                    await send_commands(DPAD_LEFT_ON)
                                elif command[7] == DPAD_UP:  # Right
                                    #print("\nUp DPAD")
                                    await send_commands(DPAD_UP_ON)
                                else:
                                    pass
                        elif command[5] == DPAD_RD: # D-Pad R/D
                                if command[7] == DPAD_RIGHT:  # Right
                                    #print("\nRight DPAD")
                                    await send_commands(DPAD_RIGHT_ON)
                                elif command[7] == DPAD_DOWN:  # Down
                                    #print("\nDown DPAD")
                                    await send_commands(DPAD_DOWN_ON)
                                else:
                                    pass
                        # Triggers
                        elif (INPUT_ID == JOYSTICK_RT) or (INPUT_ID == JOYSTICK_LT):
                                new_speed = None
                                if command[5] >= 128:
                                        new_speed = command[5]-128
                                elif command[5] <= 127:
                                        new_speed = command[5]+128
                                else:
                                        print("Unhandled joystick")
                                if isinstance(new_speed, int):
                                        if INPUT_ID == JOYSTICK_RT:
                                                #print("JOYSTICK RJ UD %s" % str(new_speed))
                                                possibly_update_speed(COMMAND_BUCKET_LADDER, -new_speed)
                                        elif INPUT_ID == JOYSTICK_LT:
                                                #print("JOYSTICK LJ UD %s" % str(new_speed))
                                                possibly_update_speed(COMMAND_BUCKET_LADDER, new_speed)
                                        else:
                                                print("Unhandled joystick")
                        # Joysticks
                        elif (INPUT_ID == JOYSTICK_RJ_UD) or (INPUT_ID == JOYSTICK_LJ_UD):
                                new_speed = None
                                if command[5] <= 127:
                                        new_speed = -command[5]
                                elif command[5] >= 128:
                                        new_speed = (command[5]-255)*-1
                                else:
                                        print("Unhandled joystick")
                                if isinstance(new_speed, int):
                                        if INPUT_ID == JOYSTICK_RJ_UD:
                                                #print("JOYSTICK RJ UD %s" % str(new_speed))
                                                possibly_update_speed(COMMAND_RIGHT_WHEELS, new_speed)
                                        elif INPUT_ID == JOYSTICK_LJ_UD:
                                                #print("JOYSTICK LJ UD %s" % str(new_speed))
                                                possibly_update_speed(COMMAND_LEFT_WHEELS, new_speed)
                                        else:
                                                print("Unhandled joystick")
                        else:
                                #print("OTHER JOYSTICK")
                                #print(command)
                                pass
                else:
                        #print(command)
                        pass
                if (abs(current_speed_right) > 0) or (abs(current_speed_left) > 0) or (abs(current_speed_bucket_ladder) > 0) or (BUTTON_A_STATE == 1) or (BUTTON_B_STATE == 1) or (BUTTON_LB_STATE == 1) or (BUTTON_RB_STATE == 1):
                        await send_commands()

                # Schedule to run again in .01 seconds
                #await asyncio.sleep(.01)
                await asyncio.sleep(.01)

if __name__ ==  '__main__':
        # Spawn file read thread
        read_thread = threading.Thread(target=thread_function, args=(1,))
        read_thread.daemon = True
        read_thread.start()
        loop = asyncio.get_event_loop()
        try:
                loop.run_until_complete(parse_command(loop))
        except KeyboardInterrupt:
                print("\nExiting")
                sys.exit(0)
        finally:
                loop.run_until_complete(loop.shutdown_asyncgens())  # Python 3.6 only
                loop.close()
