import serial
import time

class ArduinoSerial:
    def __init__(self, port='/dev/ttyACM0', baudrate=9600):
        self.ser = None
        try:
            self.ser = serial.Serial(port, baudrate, timeout=1)
        except:
            print ("Could not find Arduino.")
        time.sleep(2)  # Wait for the connection to initialize
    
    def send(self, data):
        if self.ser is not None:
            self.ser.write((data + '\n').encode())