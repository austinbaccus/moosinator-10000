import serial
import time

class ArduinoSerial:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600, timeout=1):
        self.ser = serial.Serial(port, baudrate, timeout)
        time.sleep(2)  # Wait for the connection to initialize
    
    def send(self, data):
        self.ser.write(b'hello\n')