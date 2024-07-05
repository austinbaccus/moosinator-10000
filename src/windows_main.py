import cv2
from network import MQTTClient
from windows_ai import AI_Facebook, AI_YOLOv5
from windows_camera import Camera
from PIL import Image
import base64
import time
import numpy as np
import json

with open('settings.json', 'r') as file:
    config = json.load(file)

ai = AI_YOLOv5()
#camera = Camera()

print(config["TargetResolution"])

client = MQTTClient("windows_client", config["RaspberryPiIP"], config["RaspberryPiPort"], config["MqttTopicWindows"])

start = time.time()
time.sleep(0.1)

def analyze_photo_data_from_pi(client, userdata, msg):
    image_data = base64.b64decode(msg.payload)
    base64_length = len(image_data)
    size_in_bytes = (base64_length * 3) // 4
    global start
    time_elapsed = time.time() - start
    print(f"Message received on topic {msg.topic} [{int(size_in_bytes/1024)} KB] [{round(1/time_elapsed,1)} FPS]")
    start = time.time()

    nparr = np.frombuffer(image_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    object_detection_results = ai.get_objects(frame)
    boxes = ai.draw_boxes(frame, object_detection_results)
    image = cv2.circle(boxes, (config["TargetResolution"][0]/2,config["TargetResolution"][1]/2), 10, (0,0,255), 2)
    
    cv2.imshow('Moosinator Cam', image)
    cv2.waitKey(1)

def analyze_photo_data_from_local_cam():
    frame = camera.read()
    image = camera.convert_to_pil(frame)

    global start
    time_elapsed = time.time() - start
    print(f"[{round(1/time_elapsed,1)} FPS]")
    start = time.time()

    object_detection_results = ai.get_objects(image)
    boxes = ai.draw_boxes(frame, object_detection_results)

    cv2.imshow("Moosinator Cam", boxes)
    cv2.waitKey(1)

def show_camera_stream():
    frame = camera.read()

    global start
    time_elapsed = time.time() - start
    print(f"[{round(1/time_elapsed,1)} FPS]")
    start = time.time()

    cv2.imshow("Moosinator Cam", frame)
    cv2.waitKey(1)

def main():
    client.client.on_message = analyze_photo_data_from_pi
    client.start()
    try:
        while True:
            time.sleep(5)
            client.publish(config["MqttTopicPi"], "Some command...")
    except KeyboardInterrupt:
        client.disconnect()
        cv2.destroyAllWindows()

def main_local():
    try:
        while True:
            #show_camera_stream()
            analyze_photo_data_from_local_cam()
    except KeyboardInterrupt:
        cv2.destroyAllWindows()

main()