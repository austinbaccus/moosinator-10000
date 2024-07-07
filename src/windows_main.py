import cv2
from network import MQTTClient
from windows_ai import AI_YOLOv5
from windows_targeting import Targeting
import windows_targeting as TargetAcq
import windows_image as Imaging
import time
import json

with open('settings.json', 'r') as file:
    config = json.load(file)

ai = AI_YOLOv5()
targeting = Targeting()
client = MQTTClient("windows_client", config["RaspberryPiIP"], config["RaspberryPiPort"], config["MqttTopicWindows"])
start = time.time()
global pi_instructions

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
    image = Imaging.draw_turret_status(image, json_msg.get("camera_pan_angle"), json_msg.get("camera_tilt_angle"))

    # Look at target
    target = None
    for t in targeting.targets:
        if t.label == "cup" or t.label == "vase":
            target = t
    if target is not None:
        degrees_to_move = TargetAcq.degrees_to_target((int(width/2), int(height/2)), target)
        targeting.add_targeting_instructions_to_buffer(degrees_to_move)
        #print(targeting.targeting_instructions_buffer)

    cv2.imshow('Moosinator Cam', image)
    cv2.waitKey(1)

def main():
    pi_instructions = ""
    client.client.on_message = analyze_photo_data_from_pi
    client.start()
    try:
        while True:
            time.sleep(5)
            topic = config["MqttTopicPi"]
            best_guess_targeting_instruction = targeting.get_best_targeting_instruction()
            if best_guess_targeting_instruction is not None:
                pi_instructions = f"move {best_guess_targeting_instruction}"
                client.publish(topic, pi_instructions)
                print(f"\nMessage sent on topic {topic}: {pi_instructions}\n")
                pi_instructions = ""
    except KeyboardInterrupt:
        client.disconnect()
        cv2.destroyAllWindows()

main()