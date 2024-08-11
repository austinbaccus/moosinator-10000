from transformers import DetrImageProcessor, DetrForObjectDetection
import torch
from ultralytics import YOLO

class AI_Facebook:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50", revision="no_timm")
        self.model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50", revision="no_timm")
        self.model.to(self.device)
    
    def get_objects(self, image):
        inputs = self.processor(images=image, return_tensors="pt")
        inputs = inputs.to(self.device)
        outputs = self.model(**inputs)
        target_sizes = torch.tensor([image.size[::-1]]).to(self.device)
        results = self.processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=0.7)[0]
        return results
    
    def get_name(self):
        return "detr-resnet-50"

class AI_YOLOv5:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s').to(self.device)

    def get_objects(self, image):
        return self.model(image).results.xyxy[0].cpu().numpy()
    
    def get_name(self):
        return "yolov5"
    
class AI_YOLOv8:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = YOLO("yolov8n-seg.pt").to(self.device)

    def get_objects(self, image):
        return self.model(image)
    
    def track_objects(self, image):
        return self.model.track(image, persist=True, tracker="bytetrack.yaml")
    
    def get_name(self):
        return "yolov8"