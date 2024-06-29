from transformers import DetrImageProcessor, DetrForObjectDetection
import torch
import cv2

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
    
    def draw_boxes(self, image, results):
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            box = [round(i, 2) for i in box.tolist()]
            x1 = int(box[0])
            y1 = int(box[1])
            x2 = int(box[2])
            y2 = int(box[3])
            certainty = int((score.item())*100)
            height, width = image.shape[:2]
            text_x_pos = min(width, x1+10)
            text_y_pos = max(0, y2-10)
            text_pos = (text_x_pos, text_y_pos)
            cv2.rectangle(img=image, pt1=(x1, y1), pt2=(x2, y2), color=(255,0,0), thickness=2)
            cv2.putText(img=image, text=f"{certainty}% {self.ai.object_detection_model.config.id2label[label.item()]}", org=text_pos, fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(0,0,255), thickness=2)
        return image
    
class AI_YOLOv5:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s').to(self.device)

    def get_objects(self, image):
        return self.model(image)
    
    def draw_boxes(self, image, results):
        for det in results.xyxy[0].cpu().numpy():
            x1, y1, x2, y2, conf, cls = det
            label = f'{self.model.names[int(cls)]} {conf:.2f}'
            color = (0, 255, 0)
            cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            cv2.putText(image, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        return image