# Learned most of this from: https://www.learnrobotics.org/blog/raspberry-pi-servo-motor/

import RPi.GPIO as GPIO
from time import sleep

# Tilt
# 90 max tilt up (catapult loaded)
# 110 max comfortable tilt up
# 180 max tilt down (mid catapult swing)

# Pan
# 0 max pan forwards
# 90 max pan upwards
# 180 max pan backwards

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
        
        GPIO.cleanup()
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pan_pin, GPIO.OUT)
        GPIO.setup(self.tilt_pin, GPIO.OUT)

        self.pan = GPIO.PWM(self.pan_pin, 50)
        self.tilt = GPIO.PWM(self.tilt_pin, 50)
        self.pan.start(0)
        self.tilt.start(0)
    
    def __del__(self):
        self.pan.stop()
        self.tilt.stop()
        GPIO.cleanup()

    def pan_angle(self, angle):
        angle = self.__calculate_safe_angle(angle, self.pan_bound_min, self.pan_bound_max, self.current_pan_angle)
        print("Panning to angle: {}".format(angle))
        duty = angle / 18 + 2
        GPIO.output(self.pan_pin, True)
        self.pan.ChangeDutyCycle(duty)
        sleep(1) # Grace period for servo to finish rotating before accepting new instructions.
        GPIO.output(self.pan_pin, False)
        self.pan.ChangeDutyCycle(duty) # We run this twice?
        self.current_pan_angle = self.current_pan_angle + angle
        self.pan.stop()
    
    def tilt_angle(self, angle):
        safe_angle = self.__calculate_safe_angle(angle, self.tilt_bound_min, self.tilt_bound_max)
        print("Tilting to angle: {} [attempted {}]".format(safe_angle, angle))
        duty = safe_angle / 18 + 2
        GPIO.setup(self.tilt_pin, GPIO.OUT)
        GPIO.output(self.tilt_pin, True)
        self.tilt.ChangeDutyCycle(duty)
        #sleep(1)
        #GPIO.output(self.tilt_pin, False)
        #GPIO.setup(self.tilt_pin, GPIO.IN)
        self.current_tilt_angle = safe_angle

    def __calculate_safe_angle(self, angle, min_angle, max_angle):
        if angle > max_angle:
            return max_angle 
        if angle < min_angle:
            return min_angle
        return angle