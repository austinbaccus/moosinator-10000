import serial
import time
import glob

class ArduinoSerial:
    def __init__(self, baudrate=9600):
        self.ser = None
        port = self.find_arduino_port()

        if port is not None:
            try:
                self.ser = serial.Serial(port, baudrate, timeout=1)
            except:
                print ("Could not connect to Arduino")
        else:
            print ("Could not find Arduino.")

        time.sleep(2)  # Wait for the connection to initialize
    
    def send(self, data):
        if self.ser is not None:
            self.ser.write((data + '\n').encode())

    def find_arduino_port(self):
        # List all available serial ports
        ports = glob.glob('/dev/tty[A-Za-z]*')
        print ("Total ports: {}".format(len(ports)))

        for port in ports:
            try:
                # Try to open each port
                print ("Listening for Arduino on port {}".format(port))
                ser = serial.Serial(port, baudrate=9600, timeout=1)
                ser.flush()
                
                # Read a line from the port
                ser.write(b'\n')  # Send a newline to prompt the Arduino
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    if line == "Message from the Moosinator Arduino":
                        print(f"Arduino found on port: {port}")
                        ser.close()
                        return port
                    
                ser.close()
            except:
                pass
        
        print("Arduino not found on any port.")
        return None