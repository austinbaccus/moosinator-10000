import serial
import time

class ArduinoSerial:
    def __init__(self, port='/dev/ttyACM0', baudrate=9600):
        self.ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)  # Wait for the connection to initialize
    
    def send(self, data):
        self.ser.write((data + '\n').encode())