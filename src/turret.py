# Learned most of this from: https://www.learnrobotics.org/blog/raspberry-pi-servo-motor/
# https://electronics.stackexchange.com/questions/543179/pigpio-control-of-sg90-servo-is-imprecise-on-raspberry-pi
# https://pypi.org/project/piServoCtl/
# SG90 datasheet: https://drive.google.com/file/d/1vy77kxSVM_PSUzkhrlFFGU6p4DDUlGNo/view
# https://github.com/y-tetsu/gmail_picamera/blob/master/devices/sg90.py

import time
import RPi.GPIO as GPIO
import pigpio

# Tilt
# 90 max tilt up (catapult loaded)
# 110 max comfortable tilt up
# 180 max tilt down (mid catapult swing)

# Pan
# 0 max pan forwards
# 90 max pan upwards
# 180 max pan backwards

"""
Control of SG90
 -------------------------------------------------
 Support SG90-Specification
 -------------------------------------------------
 PWM Period : 20ms(50Hz)
 Duty Cycle : 1 - 2 ms (5.0% - 10.0%)(-90° - +90°)
 -------------------------------------------------
"""

FREQUENCY = 50      # Hz
ANGLE_MARGIN = 5    # °
MIN_DUTY_CYCLE = 1  # ms
MAX_DUTY_CYCLE = 2  # ms
MIN_ANGLE = -90     # °
MAX_ANGLE = 90      # °

PWM_PERIOD = float(1.0 / FREQUENCY) * 1000.0  # ms
MIN_DUTY_RATIO = MIN_DUTY_CYCLE / PWM_PERIOD
MAX_DUTY_RATIO = MAX_DUTY_CYCLE / PWM_PERIOD

STEP_WAIT = 0.005
SWING_INTERVAL = 0.5

PERCENT = 100
MEGA = 1000000

class Sg90():
    """
    Control of SG90 by Software-PWM
      -----------------------------
      input   : duty ratio
      -----------------------------
      100.00% : 1.000
       10.00% : 0.100(2.0ms : +90°)
        5.00% : 0.050(1.0ms : -90°)
      -----------------------------
    """
    def __init__(self, gpio, min_angle=-90, max_angle=90, resolution=0.3):
        self.gpio = gpio
        self.frequency = FREQUENCY
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.center_angle = (self.min_angle + self.max_angle) // 2
        self.resolution = resolution
        self.pwm = None
        self.setup()

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, trace):
        self.cleanup()

    def setup(self):
        """
        GPIO setup
        """
        try:
            GPIO.setmode(GPIO.BCM)           # select GPIO by pin-name of Raspberry-Pi
            GPIO.setup(self.gpio, GPIO.OUT)  # set GPIO for output

            self.pwm = GPIO.PWM(self.gpio, self.frequency)  # create PWM-object
            self.pwm.start(0.0)                             # start PWM-output

        except:
            self.cleanup()

    def cleanup(self):
        """
        GPIO cleanup
        """
        GPIO.cleanup(self.gpio)

    def move(self, angle):
        """
        move to angle
        """
        self.pwm.ChangeDutyCycle(self.angle2dutyratio(angle) * PERCENT)

    def rotate(self, src_angle, dst_angle, step=1):
        """
        rotate from src_angle to dst_angle
        """
        start = int(src_angle / self.resolution)
        end = int(dst_angle / self.resolution) + 1

        for angle in range(start, end, step):
            self.pwm.ChangeDutyCycle(self.angle2dutyratio(angle * self.resolution) * PERCENT)
            time.sleep(STEP_WAIT)

    def center(self):
        """
        move to center
        """
        self.move(self.center_angle)
        time.sleep(STEP_WAIT)

    def swing(self):
        """
        swing
        """
        time.sleep(SWING_INTERVAL)
        self.rotate(self.center_angle, self.max_angle)
        time.sleep(SWING_INTERVAL)
        self.rotate(self.max_angle, self.min_angle, -1)
        time.sleep(SWING_INTERVAL)
        self.rotate(self.min_angle, self.center_angle)
        time.sleep(SWING_INTERVAL)

    def angle2dutyratio(self, angle):
        """
        convert angle to duty-ratio
        """
        if angle < self.min_angle + ANGLE_MARGIN:
            angle = self.min_angle + ANGLE_MARGIN
        elif angle > self.max_angle - ANGLE_MARGIN:
            angle = self.max_angle - ANGLE_MARGIN

        duty_ratio = (MIN_DUTY_RATIO + (MAX_DUTY_RATIO - MIN_DUTY_RATIO) * (angle + -MIN_ANGLE) / (MAX_ANGLE - MIN_ANGLE))

        return duty_ratio

class Sg90hw(Sg90):
    """
    Control of SG90 by Hardwar-PWM
      -----------------------------
      input   : duty ratio
      -----------------------------
      1000000 : 1.000
       100000 : 0.100(2.0ms : +90°)
        50000 : 0.050(1.0ms : -90°)
      -----------------------------
    """
    def setup(self):
        """
        GPIO setup
        """
        try:
            self.pwm = pigpio.pi()                       # create Hardware-PWM-object
            self.pwm.set_mode(self.gpio, pigpio.OUTPUT)  # set GPIO for output

        except:
            self.cleanup()

    def cleanup(self):
        """
        GPIO cleanup
        """
        self.pwm.set_mode(self.gpio, pigpio.INPUT)  # return GPIO to input
        self.pwm.stop()

    def move(self, angle):
        """
        move to angle
        """
        self.pwm.hardware_PWM(self.gpio, self.frequency, int(self.angle2dutyratio(angle) * MEGA))

    def rotate(self, src_angle, dst_angle, step=1):
        """
        rotate from src_angle to dst_angle
        """
        start = int(src_angle / self.resolution)
        end = int(dst_angle / self.resolution) + 1

        for angle in range(start, end, step):
            self.pwm.hardware_PWM(self.gpio, self.frequency, int(self.angle2dutyratio(angle * self.resolution) * MEGA))
            time.sleep(STEP_WAIT)

class Turret:
    def __init__(self, config):
        self.pan_pin = config["RaspberryPiPins"]["Pan"]
        self.tilt_pin = config["RaspberryPiPins"]["Tilt"]
        self.pan_bound_min = config["TurretBounds"]["TurretPanBoundNegative"]
        self.pan_bound_max = config["TurretBounds"]["TurretPanBoundPositive"]
        self.tilt_bound_min = config["TurretBounds"]["TurretTiltBoundNegative"]
        self.tilt_bound_max = config["TurretBounds"]["TurretTiltBoundPositive"]
        self.current_pan_angle = 0
        self.current_tilt_angle = 0
        
        #GPIO.cleanup()
        #GPIO.setmode(GPIO.BOARD)
        #GPIO.setup(self.pan_pin, GPIO.OUT)
        #GPIO.setup(self.tilt_pin, GPIO.OUT)

        #self.pan = GPIO.PWM(self.pan_pin, 50)
        #self.tilt = GPIO.PWM(self.tilt_pin, 50)
        #self.pan.start(0)
        #self.tilt.start(0)
    
    #def __del__(self):
        #self.pan.stop()
        #self.tilt.stop()

    #def pan_angle(self, angle):
        #angle = self.__calculate_safe_angle(angle, self.pan_bound_min, self.pan_bound_max, self.current_pan_angle)
        #print("Panning to angle: {}".format(angle))
        #duty = angle / 18 + 2
        #GPIO.output(self.pan_pin, True)
        #self.pan.ChangeDutyCycle(duty)
        #sleep(1) # Grace period for servo to finish rotating before accepting new instructions.
        #GPIO.output(self.pan_pin, False)
        #self.pan.ChangeDutyCycle(duty) # We run this twice?
        #self.current_pan_angle = self.current_pan_angle + angle
        #self.pan.stop()
    
    def tilt_angle(self, angle):
        safe_angle = self.__calculate_safe_angle(angle, self.tilt_bound_min, self.tilt_bound_max)
        print("Tilting to angle: {} [attempted {}]".format(safe_angle, angle))
        #duty = safe_angle / 18 + 2
        self.tilt_servo.write(safe_angle)
        sleep(1)
        self.tilt_servo.stop()
        self.current_tilt_angle = safe_angle

    def __calculate_safe_angle(self, angle, min_angle, max_angle):
        if angle > max_angle:
            return max_angle 
        if angle < min_angle:
            return min_angle
        return angle