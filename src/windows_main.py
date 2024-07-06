import cv2
from network import MQTTClient
from windows_ai import AI_YOLOv5
from windows_targeting import Targeting
import base64
import time
import numpy as np
import json

with open('settings.json', 'r') as file:
    config = json.load(file)

ai = AI_YOLOv5()
targeting = Targeting()

client = MQTTClient("windows_client", config["RaspberryPiIP"], config["RaspberryPiPort"], config["MqttTopicWindows"])

start = time.time()
time.sleep(0.1)

def analyze_photo_data_from_pi(client, userdata, msg):

    message_payload = msg.payload.decode('utf-8')
    json_msg = json.loads(message_payload)
    image_base64 = json_msg.get("ir_camera_data")
    image_data = base64.b64decode(image_base64) #msg.payload)
    
    base64_length = len(image_data)
    size_in_bytes = (base64_length * 3) // 4
    global start
    time_elapsed = time.time() - start
    print(f"Message received on topic {msg.topic} [{int(size_in_bytes/1024)} KB] [{round(1/time_elapsed,1)} FPS]")
    start = time.time()

    nparr = np.frombuffer(image_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    object_detection_results = ai.get_objects(frame)
    targeting.update_targets(object_detection_results, ai.model.names)
    height, width = frame.shape[:2]
    boxes = draw_boxes(frame, targeting.targets, width)
    image = cv2.circle(boxes, (int(width/2), int(height/2)), 10, (0,0,255), 2)
    
    cv2.imshow('Moosinator Cam', image)
    cv2.waitKey(1)

def draw_boxes(image, objects, width):
    for object in objects:
        if targeting.is_target_valid(object, config):
            text_x_pos = min(width, object.x1+10)
            text_y_pos = max(0, object.y2-10)
            text_pos = (text_x_pos, text_y_pos)
            cv2.rectangle(img=image, pt1=(object.x1, object.y1), pt2=(object.x2, object.y2), color=(255,0,0), thickness=2)
            cv2.putText(img=image, text=f"{object.label} {object.certainty}%", org=text_pos, fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=(0,0,255), thickness=1)
    return image

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

main()