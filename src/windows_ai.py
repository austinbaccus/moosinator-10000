import cv2
import numpy as np
from transformers import AutoImageProcessor, DeformableDetrForObjectDetection, GLPNImageProcessor, GLPNForDepthEstimation
import torch
from PIL import Image

class AI:
    def __init__(self):
        print(f"Is CUDA supported by this system? {torch.cuda.is_available()}")
        print(f"CUDA version: {torch.version.cuda}")
        cuda_id = torch.cuda.current_device()
        print(f"ID of current CUDA device: {torch.cuda.current_device()}")
        print(f"Name of current CUDA device: {torch.cuda.get_device_name(cuda_id)}")
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        self.init_object_detection()
        self.init_depth()

        # color
    
    def init_object_detection(self):
        self.object_detection_processor = AutoImageProcessor.from_pretrained("SenseTime/deformable-detr-with-box-refine")
        self.object_detection_model = DeformableDetrForObjectDetection.from_pretrained("SenseTime/deformable-detr-with-box-refine")
        self.object_detection_model.to(self.device)

    def init_depth(self):
        self.depth_processor = GLPNImageProcessor.from_pretrained("vinvino02/glpn-kitti")
        self.depth_model = GLPNForDepthEstimation.from_pretrained("vinvino02/glpn-kitti")
        self.depth_model.to(self.device)

    def get_objects(self, image):
        inputs = self.object_detection_processor(images=image, return_tensors="pt")
        inputs = inputs.to(self.device)  # Move inputs to GPU or CPU device
        outputs = self.object_detection_model(**inputs)

        # convert outputs (bounding boxes and class logits) to COCO API
        # let's only keep detections with score > 0.7
        target_sizes = torch.tensor([image.size[::-1]]).to(self.device)
        results = self.object_detection_processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=0.7)[0]

        return results
    
    def get_depth(self, image, color):
        inputs = self.depth_processor(images=image, return_tensors="pt")
        inputs = inputs.to(self.device)  # Move inputs to GPU or CPU device

        with torch.no_grad():
            outputs = self.depth_model(**inputs)
            predicted_depth = outputs.predicted_depth

        # interpolate to original size
        prediction = torch.nn.functional.interpolate(
            predicted_depth.unsqueeze(1),
            size=image.size[::-1],
            mode="bicubic",
            align_corners=False,
        ).to(self.device)

        # visualize the prediction
        output = prediction.squeeze().cpu().numpy() # cpu
        formatted = (output * 255 / np.max(output)).astype("uint8")
        depth = Image.fromarray(formatted)

        if (color == None):
            return formatted
        if (color == "gray"):
            depth_array = np.array(depth)
            depth_bgr = cv2.cvtColor(depth_array, cv2.COLORMAP_RAINBOW)
            return depth_bgr
        if (color == "rainbow"):
            depth_array = np.array(depth)
            depth_normalized = depth_array.astype(np.float32) / 255.0
            depth_colored = cv2.applyColorMap((depth_normalized * 255).astype(np.uint8), cv2.COLORMAP_JET)
            return depth_colored

        return depth