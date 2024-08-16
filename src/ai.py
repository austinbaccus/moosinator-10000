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
        return self.model.track(image, persist=True, tracker="bytetrack.yaml", verbose=False)
    
    def get_name(self):
        return "yolov8"
    
class AI_Hailo_YOLOv8:
    def __init__(self, model_path):
        # Load the Hailo NPU model
        self.hef = HailoRT.Hef(model_path)
        self.vdevice = HailoRT.VDevice()
        self.vdevice.configure(self.hef)

        # Get the network parameters
        self.network_group = self.vdevice.get_network_group()
        self.input_vstream = self.network_group.get_input_vstream()
        self.output_vstream = self.network_group.get_output_vstream()

    def get_objects(self, image):
        # Preprocess image
        input_data = self.preprocess(image)

        # Perform inference
        self.network_group.send(input_vstream, input_data)
        output = self.network_group.receive(self.output_vstream)

        # Post-process the results
        results = self.postprocess(output)
        return results

    def preprocess(self, image):
        # Convert image to numpy array and resize it according to your model's input shape
        input_image = np.array(image.resize((640, 640))) / 255.0
        input_image = input_image.astype(np.float32)
        input_image = np.expand_dims(input_image, axis=0)  # Add batch dimension
        return input_image

    def postprocess(self, output):
        # Implement your post-processing logic to decode the NPU output into meaningful detections
        # This will vary depending on your model
        # For example, you could use non-maximum suppression (NMS) for YOLO
        detections = ...  # decode the output
        return detections

    def get_name(self):
        return "hailo_yolov8"