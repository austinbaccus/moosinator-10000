import serial
import time

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
        ports = serial.tools.list_ports.comports()
        print ("Total ports: {}".format(len(ports)))
        
        for port in ports:
            try:
                # Try to open each port
                print ("Listening for Arduino on port {}".format(port.device))
                ser = serial.Serial(port.device, baudrate=9600, timeout=1)
                ser.flush()
                
                # Read a line from the port
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    if "Message from the Moosinator Arduino" in line:
                        print(f"Arduino found on port: {port.device}")
                        ser.close()
                        return port.device
                    
                ser.close()
            except (OSError, serial.SerialException):
                pass
        
        print("Arduino not found on any port.")
        return None