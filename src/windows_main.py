import cv2
from network import MQTTClient
from windows_ai import AI_YOLOv5
from windows_targeting import Targeting
import windows_image as Imaging
import time
import json

with open('settings.json', 'r') as file:
    config = json.load(file)

ai = AI_YOLOv5()
targeting = Targeting()
client = MQTTClient("windows_client", config["RaspberryPiIP"], config["RaspberryPiPort"], config["MqttTopicWindows"])
start = time.time()

def analyze_photo_data_from_pi(client, userdata, msg):
    # JSON
    json_msg = json.loads(msg.payload.decode('utf-8'))

    # FPS
    global start
    print(f"Message received on topic {msg.topic} [{round(1/(time.time() - start),1)} FPS]")
    start = time.time()

    # Changing incoming data into usable state for AI
    image = Imaging.prepare_ir_image_for_ai(json_msg.get("ir_camera_data"), config)
    
    # Get objects in image
    object_detection_results = ai.get_objects(image)

    # Update targets
    targeting.update_targets(object_detection_results, ai.model.names)

    # Draw stuff to window
    height, width = image.shape[:2]
    image = Imaging.draw_boxes(image, targeting.targets, width, config)
    image = Imaging.draw_crosshair(image, width, height)
    cv2.imshow('Moosinator Cam', image)
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

main()