# Osprey Robotics Controller Client
# TODO: Fix issue where joystick not going to zero when let go

# Imports
import struct
import threading
import asyncio
import socket

# Program global variables
current_speed_right = 0
current_speed_left = 0
ADDRESS_WHEELS = 0x01
COMMAND_WHEELS_STOP = 0
COMMAND_RIGHT_WHEELS = 1
COMMAND_LEFT_WHEELS = 2
current_action = COMMAND_WHEELS_STOP
serverAddressPort = ("192.168.1.217", 20222)
bufferSize = 5
INPUT_TYPE = 0
new_commands = []

# Controller global variables
BUTTON = 1
JOYSTICK = 2
BUTTON_A = 0
BUTTON_B = 1
BUTTON_X = 2
BUTTON_Y = 3
JOYSTICK_RT = 5
JOYSTICK_RJ_UD = 4
JOYSTICK_LT = 2
JOYSTICK_LJ_UD = 1

# Data streams
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
controller_device = open("/dev/input/js0","rb")

# Reads commands from the controller
def thread_function(name):
	global controller_device, new_commands
	while True:
		command=list(controller_device.read(8))
		#print(command) # DEBUG
		new_commands = [command] + new_commands
		#print(new_commands) # DEBUG

# Sends commands to the server
async def send_commands():
	global UDPClientSocket, serverAddressPort, current_action, current_speed_right, current_speed_left
	if abs(current_speed_right) > 0:
		print("Sending right speed: %i" % current_speed_right)
		UDPClientSocket.sendto(struct.pack('>Bhh', COMMAND_RIGHT_WHEELS, current_speed_right, current_speed_right), serverAddressPort)
	if abs(current_speed_left) > 0:
		print("Sending left speed: %i" % current_speed_left)
		UDPClientSocket.sendto(struct.pack('>Bhh', COMMAND_LEFT_WHEELS, current_speed_left, current_speed_left), serverAddressPort)
	# TODO: Excavation
	# TODO: Deposition
	# TODO: Camera movement
	if (current_speed_right == 0) and (current_speed_left == 0):
		print("Unrecognized action")
	return

# Parse commands from controller
async def parse_command(loop):
	global current_speed_right, current_speed_left, new_commands, current_action
	while True:
		if len(new_commands) > 0:
			command = new_commands.pop()
		else:
			if (abs(current_speed_right) > 0) or (abs(current_speed_left) > 0):
				await send_commands()
			await asyncio.sleep(.01)
			continue
		INPUT_TYPE = command[-2]
		INPUT_ID = command[-1]
		if INPUT_TYPE == BUTTON:
			button_pressed = command[-4] == 1
			if (INPUT_ID == BUTTON_A) and button_pressed:
				print("A BUTTON")
			elif (INPUT_ID == BUTTON_B) and button_pressed:
				print("B BUTTON")
			elif (INPUT_ID == BUTTON_X) and button_pressed:
				print("X BUTTON")
			elif (INPUT_ID == BUTTON_Y) and button_pressed:
				print("Y BUTTON")
			elif not button_pressed:
				pass
			else:
				print("OTHER BUTTON")
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
				current_action = COMMAND_WHEELS_FORWARD
			elif (INPUT_ID == JOYSTICK_LT):
				if command[5] >= 128:
					current_speed = command[5]-128
					print("JOYSTICK LT %s" % str(current_speed))
				elif command[5] <= 127:
					current_speed = command[5]+128
					print("JOYSTICK LT %s" % str(current_speed))
				else:
					print("Unhandled joystick")
				current_action = COMMAND_WHEELS_BACKWARD
			"""
			# Joysticks
			if (INPUT_ID == JOYSTICK_RJ_UD):
				if command[5] <= 127:
					current_speed_right = -command[5]
					print("JOYSTICK RJ UD %s" % str(current_speed_right))
				elif command[5] >= 128:
					current_speed_right = (command[5]-255)*-1
					print("JOYSTICK RJ UD %s" % str(current_speed_right))
				else:
					print("Unhandled joystick")
				current_action = COMMAND_RIGHT_WHEELS
			elif (INPUT_ID == JOYSTICK_LJ_UD):
				if command[5] <= 127:
					current_speed_left = -command[5]
					print("JOYSTICK LJ UD %s" % str(current_speed_left))
				elif command[5] >= 128:
					current_speed_left = (command[5]-255)*-1
					print("JOYSTICK LJ UD %s" % str(current_speed_left))
				else:
					print("Unhandled joystick")
				current_action = COMMAND_LEFT_WHEELS
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
		await asyncio.sleep(.01)

if __name__ ==  '__main__':
	# Spawn file read thread
	read_thread = threading.Thread(target=thread_function, args=(1,))
	read_thread.start()
	loop = asyncio.get_event_loop()
	try:
		loop.run_until_complete(parse_command(loop))
	finally:
		loop.run_until_complete(loop.shutdown_asyncgens())  # Python 3.6 only
		loop.close()
