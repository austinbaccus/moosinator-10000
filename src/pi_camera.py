from picamera import PiCamera
from time import sleep

class Camera:
    def __init__(self):
        self.camera = PiCamera()

    def start(self):
        self.camera.start_preview()