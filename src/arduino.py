import serial
import time
import glob
import threading

class ArduinoSerial:
    def __init__(self, baudrate=9600):
        self.ser = None
        port = self.find_arduino_port()

        if port is not None:
            try:
                self.ser = serial.arduino.Serial(port, baudrate, timeout=1)
                time.sleep(2) # Wait for the connection to initialize
            except:
                print ("Could not connect to Arduino")
        else:
            print ("Could not find Arduino.")
    
    def send(self, data):
        if self.ser is not None:
            self.ser.write((data + '\n').encode())

    def read_from_arduino(self, read_messages_from_arduino):
        while True:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8').rstrip()
                if read_messages_from_arduino:
                    print("Message from Arduino: ", line)

    # Function to run the reading in a separate thread
    def start_reading_thread(self, read_messages_from_arduino = False):
        thread = threading.Thread(target=self.read_from_arduino(read_messages_from_arduino), daemon=True)
        thread.start()

    def find_arduino_port(self):
        # List all available serial ports
        ports = glob.glob('/dev/tty[A-Za-z]*')
        print ("Total ports: {}".format(len(ports)))

        # This is at the front of the list because it's the most likely port for the Arduino to be on
        ports.insert(0,"/dev/ttyACM0") 

        for port in ports:
            try:
                # Try to open each port
                print ("Listening for Arduino on port {}".format(port))
                ser = serial.Serial(port, baudrate=9600, timeout=1)
                ser.flush()
                
                # Read a line from the port. Sleep for 3 seconds (before and after) to give the Arduino time to send a message.
                time.sleep(3)
                ser.write(b'\n') # Send a newline to prompt the Arduino
                time.sleep(3)

                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    if "Moosinator" in line or "Arduino" in line:
                        print(f"Arduino found on port: {port}")
                        ser.close()
                        return port
                    
                ser.close()
            except:
                pass
        
        print("Arduino not found on any port.")
        return None