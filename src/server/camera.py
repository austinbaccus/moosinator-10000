import cv2, queue, threading
from PIL import Image

class Camera:

    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.q = queue.Queue()
        t = threading.Thread(target=self._reader)
        t.daemon = True
        t.start()

    def __del__(self):
        self.camera.release()
        cv2.destroyAllWindows()

    def _reader(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            if not self.q.empty():
                try:
                    self.q.get_nowait()   # discard previous (unprocessed) frame
                except queue.Empty:
                    pass
            self.q.put(frame)

    def read(self):
        return self.q.get()
    
    def convert_to_pil(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame)