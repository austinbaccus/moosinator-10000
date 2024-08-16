import serial
import time
import glob
import threading

class ArduinoSerial:
    def __init__(self, baudrate=9600):
        self.ser = None
        self.message = None  # Shared variable to store the message
        self.handshake_completed = False
        port = self.find_arduino_port()

        if port is not None:
            try:
                self.ser = serial.Serial(port, baudrate, timeout=1)
                time.sleep(2) # Wait for the connection to initialize
            except Exception as e:
                print ("Could not connect to Arduino")
                print (e)
        else:
            print ("Could not find Arduino.")
    
    def send_to_arduino(self, data):
        if self.ser is not None:
            self.ser.write((data + '\n').encode())

    def read_from_arduino(self, read_messages_from_arduino):
        buffer = ''
        while True:
            if self.ser.in_waiting > 0:
                try:
                    buffer += self.ser.read(self.ser.in_waiting).decode('utf-8')
                    if '\n' in buffer:  # Assuming Arduino ends its message with a newline
                        lines = buffer.split('\n')
                        for line in lines[:-1]:
                            self.message = line  # Store the message

                            if self.handshake_completed is False:
                                self.send_to_arduino("handshake")
                                if "Arduino recognizes handshake" in line:
                                    self.handshake_completed = True
                                    print("Arduino recognizes handshake")

                            if read_messages_from_arduino and self.handshake_completed:
                                print("Message from Arduino: ", line)
                        buffer = lines[-1]  # Keep any incomplete message
                except:
                    pass
            time.sleep(0.1)

    def start_reading_thread(self, read_messages_from_arduino = False):
        thread = threading.Thread(target=self.read_from_arduino, args=(read_messages_from_arduino,), daemon=True)
        thread.start()

    def get_message(self):
        """ Method to retrieve the latest message from the Arduino """
        return self.message

    def find_arduino_port(self):
        # List all available serial ports
        ports = glob.glob('/dev/tty[A-Za-z]*')
        print ("Total ports: {}".format(len(ports)))

        # This is at the front of the list because it's the most likely port for the Arduino to be on
        ports.insert(0,"COM6")
        ports.insert(1,"/dev/ttyACM0")

        for port in ports:
            try:
                # Try to open each port
                print ("Listening for Arduino on port {}".format(port))
                ser = serial.Serial(port, baudrate=9600, timeout=1)
                ser.flush()
                
                # Read a line from the port. Sleep for 3 seconds (before and after) to give the Arduino time to send a message.
                time.sleep(1)
                ser.write(b'\n') # Send a newline to prompt the Arduino
                time.sleep(1)

                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    if "handshake" in line:
                        print(f"Arduino found on port: {port}")
                        ser.close()
                        return port
                    
                ser.close()
            except:
                pass
        
        print("Arduino not found on any port.")
        return None

