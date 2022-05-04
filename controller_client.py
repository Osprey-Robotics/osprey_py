# Osprey Robotics Controller Client
# Note: "Bonus speed" affects wheels on each side of the robot
#       So running the right side on 127 power will cause the left side to immediately catch up to 127 power

# Imports
import asyncio
import socket
import struct
import sys
import threading
import time

# Program global variables
current_speed_right = 0
current_speed_left = 0
COMMAND_WHEELS_STOP = 0
COMMAND_RIGHT_WHEELS = 1
COMMAND_LEFT_WHEELS = 2
COMMAND_BUTTON_PRESS = 3
serverAddressPort = ("192.168.1.217", 20222)
INPUT_TYPE = 0
new_commands = []
# Bandwidth saving threshold, 0-127
# Higher numbers equate to saving more bandwidth at the expense of less speeds
bandwidth_saving_threshold = 0
# "Bonus speed": Prevent robot from accelerating too quickly by incrementing speed from 70 if 127 is held, and keeping all other speeds 55% slower
speed_factor=0.55
bonus_speed=0
bonus_speed_max=57

# Controller global variables
BUTTON = 1
JOYSTICK = 2
BUTTON_A = 0
BUTTON_B = 1
BUTTON_X = 2
BUTTON_Y = 3
BUTTON_BACK = 6
BUTTON_START = 7
BUTTON_LT_CLICK=9
BUTTON_RT_CLICK=10
JOYSTICK_RT = 5
JOYSTICK_RJ_UD = 4
JOYSTICK_LT = 2
JOYSTICK_LJ_UD = 1

# Data streams
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
controller_device = open("/dev/input/js0","rb")

def update_speed(wheel_side, new_speed):
        global current_speed_right, current_speed_left
        if wheel_side == COMMAND_RIGHT_WHEELS:
                current_speed_right = new_speed
        elif wheel_side == COMMAND_LEFT_WHEELS:
                current_speed_left = new_speed
        else:
                print("Unrecognized motors")

def possibly_update_speed(wheel_side, new_speed):
        global current_speed_right, current_speed_left, bandwidth_saving_threshold, speed_factor, bonus_speed
        new_speed = round(new_speed*speed_factor)
        orig_speed = 0
        if new_speed == 0:
                bonus_speed = 0
                update_speed(wheel_side, new_speed)
                return
        if abs(new_speed) <= 20:
                bonus_speed = 0
                # Make sure joystick goes to zero
                update_speed(wheel_side, 0)
                return
        if wheel_side == COMMAND_RIGHT_WHEELS:
                orig_speed = current_speed_right
        elif wheel_side == COMMAND_LEFT_WHEELS:
                orig_speed = current_speed_left
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
        global UDPClientSocket, serverAddressPort, current_speed_right, current_speed_left, bonus_speed
        if button == BUTTON_START:
                print("Requesting motor reset")
                UDPClientSocket.sendto(struct.pack('>Bh', COMMAND_BUTTON_PRESS, BUTTON_START), serverAddressPort)
                wait_seconds = 5
                while wait_seconds >= 0:
                        print("\rPlease wait (%s)" % (str(wait_seconds).zfill(2)), end='')
                        time.sleep(1)
                        wait_seconds -= 1
                print("\rMotors should be reset, resume driving when ready")
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
        # TODO: Excavation
        # TODO: Deposition
        # TODO: Camera movement
        if (current_speed_right == 0) and (current_speed_left == 0) and (button is None):
                print("Unrecognized action")
        return

# Parse commands from controller
async def parse_command(loop):
        global current_speed_right, current_speed_left, new_commands, bonus_speed, bonus_speed_max
        while True:
                if len(new_commands) > 0:
                        if bonus_speed > 0:
                                bonus_speed -= 1
                        command = new_commands.pop()
                else:
                        if (bonus_speed < bonus_speed_max) and ((abs(current_speed_right) >= 60) or (abs(current_speed_left) >= 60)):
                                bonus_speed += 1
                        if (abs(current_speed_right) > 0) or (abs(current_speed_left) > 0):
                                await send_commands()
                        await asyncio.sleep(.01)
                        continue
                INPUT_TYPE = command[-2]
                INPUT_ID = command[-1]
                if INPUT_TYPE == BUTTON:
                        button_pressed = command[-4] == 1
                        if (INPUT_ID == BUTTON_A) and button_pressed:
                                print("\nA BUTTON")
                        elif (INPUT_ID == BUTTON_B) and button_pressed:
                                print("\nB BUTTON")
                        elif (INPUT_ID == BUTTON_X) and button_pressed:
                                print("\nX BUTTON")
                        elif (INPUT_ID == BUTTON_Y) and button_pressed:
                                print("\nY BUTTON")
                        elif (INPUT_ID == BUTTON_START) and button_pressed:
                                #print("\nSTART BUTTON")
                                await send_commands(BUTTON_START)
                        elif (INPUT_ID == BUTTON_BACK) and button_pressed:
                                print("\nBACK BUTTON")
                        elif not button_pressed:
                                pass
                        else:
                                print("\nOTHER BUTTON")
                elif INPUT_TYPE == JOYSTICK:
                        # TODO: Camera control
                        """
                        if command[5]=='\x80': # D-Pad L/U
                                if command[7]=='\x06': # Left
                                        (..)
                                elif command[7]=='\x07': # Up
                                        (..)
                        elif command[5]=='\x7F': # D-Pad R/D
                                if command[7]=='\x06': # Right
                                        (..)
                                elif command[7]=='\x07': # Down
                                        (..)

                        """
                        # TODO: Excavation
                        """
                        # Triggers
                        if (INPUT_ID == JOYSTICK_RT):
                                if command[5] >= 128:
                                        current_speed = command[5]-128
                                        print("JOYSTICK RT %s" % str(current_speed))
                                elif command[5] <= 127:
                                        current_speed = command[5]+128
                                        print("JOYSTICK RT %s" % str(current_speed))
                                else:
                                        print("Unhandled joystick")
                        elif (INPUT_ID == JOYSTICK_LT):
                                if command[5] >= 128:
                                        current_speed = command[5]-128
                                        print("JOYSTICK LT %s" % str(current_speed))
                                elif command[5] <= 127:
                                        current_speed = command[5]+128
                                        print("JOYSTICK LT %s" % str(current_speed))
                                else:
                                        print("Unhandled joystick")
                        """
                        # Joysticks
                        if (INPUT_ID == JOYSTICK_RJ_UD) or (INPUT_ID == JOYSTICK_LJ_UD):
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
                if (abs(current_speed_right) > 0) or (abs(current_speed_left) > 0):
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
