from picamera import PiCamera
from time import sleep
import io
import base64

class Camera:
    def __init__(self):
        self.camera = PiCamera()

    def start(self):
        self.camera.start_preview()

    def capture_image_base64(self):
        # Create an in-memory stream
        stream = io.BytesIO()
        self.camera.capture(stream, format='jpeg')
        # Reset stream position to the beginning
        stream.seek(0)
        # Read the stream and encode it as base64
        image_data = stream.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        return image_base64