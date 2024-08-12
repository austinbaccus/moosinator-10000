import io
import base64
import cv2
#import picamera
import image as Imaging
from enum import Enum

class CameraType(Enum):
    PICAMERA = 1
    WEBCAM = 2

class Camera:
    def __init__(self, camera_type, config):
        self.camera_type = camera_type
        self.config = config

        # Initialize the appropriate camera based on the camera type
        if self.camera_type == CameraType.PICAMERA:
            self.camera = picamera.PiCamera(resolution=tuple(config["TargetResolution"]))
            self.stream = io.BytesIO()
        elif self.camera_type == CameraType.WEBCAM:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                raise IOError("Cannot open webcam")
        else:
            raise ValueError("Unsupported camera type")

    def get_frame(self):
        """Gets a single frame from the camera."""
        if self.camera_type == CameraType.PICAMERA:
            self.camera.capture(self.stream, format='jpeg', use_video_port=True)
            self.stream.seek(0)
            image_data = self.stream.read()
            self.stream.seek(0)
            self.stream.truncate()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            return Imaging.prepare_ir_image_for_ai(image_base64, self.config)
        elif self.camera_type == CameraType.WEBCAM:
            ret, frame = self.camera.read()
            if not ret:
                raise RuntimeError("Failed to capture frame from webcam")
            return frame

    def release(self):
        """Releases camera resources."""
        if self.camera_type == CameraType.WEBCAM:
            self.camera.release()
            cv2.destroyAllWindows()
        elif self.camera_type == CameraType.PICAMERA:
            self.camera.close()