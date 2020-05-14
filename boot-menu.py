#!/usr/bin/python
import time
import subprocess
import Adafruit_CharLCD as LCD
import socket
import fcntl
import struct
import os
import json
import mido


# BUTTONS :
# LCD.SELECT
# LCD.LEFT
# LCD.UP
# LCD.DOWN
# LCD.RIGHT

lcd = LCD.Adafruit_CharLCDPlate(initial_backlight=0)
#lcd.set_color(1.0, 0.0, 1.0)
lcd.clear()


current_function = 0


def get_ip_address(ifname='eth0'):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip = socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])
    lcd.clear()
    lcd.message(ip)

def setup_midi():
    subprocess.call(['aconnect', '-x'])
    subprocess.call(['aconnect', 'A-Series Keyboard:0', 'MIDI4x4:0'])
    lcd.clear()
    lcd.message('Connected!')

def shutdown():
    lcd.clear()
    lcd.message('Bye bye')
    subprocess.call(['sudo',  'shutdown', '-h', 'now'])



class Presets:
    current = 0
    path = '/home/pi/keys-presets'
    available = [p[: -5] for p in os.listdir(path)]
 
    def show(self):
        lcd.clear()
        lcd.message('Send Keys preset\n' + self.available[self.current])

    def send(self):
        preset = json.load(open(os.path.join(self.path, self.available[self.current] + '.json')))
	for name in mido.get_output_names():
            if name.startswith('MIDI4x4:MIDI4x4 MIDI 1'):
                break
        outputport = mido.open_output(name)
        for message in preset['messagesList']:
            outputport.send(mido.Message('control_change', control=int(message['id']), value=int(message['value']), channel=0))
            print(message['id'], message['value'])
        lcd.clear()
        lcd.message('Preset sent!')

    def inc(self):
        self.current += 1
        if self.current > len(self.available) - 1:
            self.current = 0
        self.show()

    def lower(self):
        self.current -= 1
        if self.current < 0:
            self.current = len(self.available) - 1
        self.show()

presets = Presets()

functions = [
    { 'msg': 'A49>pi keys>mf:1\nRIGHT when ready',
      'right': setup_midi },
    { 'msg': presets.show,
      'right': presets.send,
      'up': presets.inc,
      'down': presets.lower },
    { 'msg': 'Get IP',
      'right': get_ip_address },
    { 'msg': 'Shutdown',
      'right': shutdown },
]

def printState():
    lcd.clear()
    msg = functions[current_function]['msg']
    if type(msg) == str:
        lcd.message(msg)
    else:
        msg()

printState()

print('Press Ctrl-C to quit.')
while True:
    time.sleep(0.3)
    if lcd.is_pressed(LCD.SELECT):
        current_function -= 1
        if current_function < 0:
	    current_function = len(functions) - 1
	printState()
    elif lcd.is_pressed(LCD.LEFT):
        current_function += 1
        if current_function > len(functions) - 1:
	    current_function = 0
	printState()
    elif lcd.is_pressed(LCD.UP):
        if 'up' in functions[current_function]:
            functions[current_function]['up']()
    elif lcd.is_pressed(LCD.DOWN):
        if 'down' in functions[current_function]:
            functions[current_function]['down']()
    elif lcd.is_pressed(LCD.RIGHT):
	if 'right' in functions[current_function]:
            functions[current_function]['right']()
