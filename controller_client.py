# Osprey Robotics Controller Client

import struct
import threading
import asyncio
import socket

current_speed = 0
ADDRESS_WHEELS = 0x01
COMMAND_WHEELS_STOP = 0
COMMAND_WHEELS_FORWARD = 1
COMMAND_WHEELS_BACKWARD = 2
COMMAND_WHEELS_SPIN_RIGHT = 3
COMMAND_WHEELS_SPIN_LEFT = 4
current_action = COMMAND_WHEELS_FORWARD
serverAddressPort = ("192.168.1.217", 20222)
bufferSize = 5
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

INPUT_TYPE = 0
BUTTON = 1
JOYSTICK = 2
BUTTON_A = 0
BUTTON_B = 1
BUTTON_X = 2
BUTTON_Y = 3
JOYSTICK_RT = 5
JOYSTICK_LT = 2

controller_device = open("/dev/input/js0","rb")
new_commands = []

def thread_function(name):
	global controller_device, new_commands
	while True:
		command=list(controller_device.read(8))
		new_commands = [command] + new_commands

async def send_data():
	global UDPClientSocket, serverAddressPort, current_action
	print("Sending speed: %i" % current_speed)
	if current_action == COMMAND_WHEELS_FORWARD:
		UDPClientSocket.sendto(struct.pack('>Bhhhh', 0x01, current_speed, current_speed, current_speed, current_speed), serverAddressPort)
	elif current_action == COMMAND_WHEELS_BACKWARD:
		UDPClientSocket.sendto(struct.pack('>Bhhhh', 0x01, -current_speed, -current_speed, -current_speed, -current_speed), serverAddressPort)
	elif current_action == COMMAND_WHEELS_SPIN_RIGHT:
		UDPClientSocket.sendto(struct.pack('>Bhhhh', 0x01, current_speed, current_speed, -current_speed, -current_speed), serverAddressPort)
	elif current_action == COMMAND_WHEELS_SPIN_LEFT:
		UDPClientSocket.sendto(struct.pack('>Bhhhh', 0x01, -current_speed, -current_speed, current_speed, current_speed), serverAddressPort)
	else:
		print("Unrecognized action")
	return

async def read_trigger(loop):
	global current_speed, new_commands, current_action
	while True:
		if len(new_commands) > 0:
			command = new_commands.pop()
		else:
			if abs(current_speed) > 0:
				await send_data()
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
			if (INPUT_ID == JOYSTICK_RT):
				if command[5] >= 128:
					current_speed = command[5]-128
					print("JOYSTICK RT %s" % str(command[5]-128))
				elif command[5] <= 127:
					current_speed = command[5]+128
					print("JOYSTICK RT %s" % str(command[5]+128))
				else:
					print("Unhandled joystick")
				current_action = COMMAND_WHEELS_FORWARD
			elif (INPUT_ID == JOYSTICK_LT):
				if command[5] >= 128:
					current_speed = command[5]-128
					print("JOYSTICK LT %s" % str(command[5]-128))
				elif command[5] <= 127:
					current_speed = command[5]+128
					print("JOYSTICK LT %s" % str(command[5]+128))
				else:
					print("Unhandled joystick")
				current_action = COMMAND_WHEELS_BACKWARD
			else:
				print("OTHER JOYSTICK")
			#print(command)
		else:
			#print(command)
			pass
		if abs(current_speed) > 0:
			await send_data()

		# Schedule to run again in .01 seconds
		await asyncio.sleep(.01)

if __name__ ==  '__main__':
	# Spawn file read thread
	read_thread = threading.Thread(target=thread_function, args=(1,))
	read_thread.start()
	loop = asyncio.get_event_loop()
	try:
		loop.run_until_complete(read_trigger(loop))
	finally:
		loop.run_until_complete(loop.shutdown_asyncgens())  # Python 3.6 only
		loop.close()
