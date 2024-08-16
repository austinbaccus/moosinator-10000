from collections import defaultdict
import platform
import json
import time
import cv2
import ai
from targeting import Targeting
import targeting as TargetAcq
import image as Imaging
from camera import Camera, CameraType
from arduino import ArduinoSerial

#if platform.system() == "Linux":
#    import picamera
#if platform.system() == "Windows":
#    from PIL import Image

try:
    with open('settings.json', 'r') as file:
        config = json.load(file)
except FileNotFoundError:
    with open('src/settings.json', 'r') as file:
        config = json.load(file)

arduinoSerial = ArduinoSerial()
ai = ai.AI_YOLOv8()
targeting = Targeting()
current_pan_angle = 90
current_tilt_angle = 90
fps_buffer = []
start = time.time()
track_history = defaultdict(lambda: [])
timestamp_of_last_turret_command = time.time()

def annotate_image(image, fps, object_detection_results):
    try:
        height, width = image.shape[:2]
        boxes = object_detection_results[0].boxes.xywh.cpu()
        track_ids = object_detection_results[0].boxes.id.int().cpu().tolist()
        image = object_detection_results[0].plot()
        #image = Imaging.draw_mask(image, object_detection_results) # draws an outline
        image = Imaging.draw_tracks(image, track_history, boxes, track_ids) # draws the little squiggly tracker line
        image = Imaging.draw_crosshair(image, width, height)
        image = Imaging.draw_turret_status(image, current_pan_angle, current_tilt_angle, fps, config["ObjectDetection"]["ValidTargetLabels"])
    except:
        return image
    return image

def update_targeting(image, object_detection_results):
    global track_history
    targeting.update_detected_objects(object_detection_results, ai.model.names, ai.get_name(), track_history)
    height, width = image.shape[:2]
    crosshair_coords = (int(width/2), int(height/2))
    target = targeting.get_best_target(config["ObjectDetection"]["ValidTargetLabels"], crosshair_coords)
    if target is not None:
        targeting.add_targeting_instructions_to_buffer(TargetAcq.degrees_to_target(crosshair_coords, target))
        center = target.get_center()
        print(f"target coords: {center}")
    else:
        targeting.add_targeting_instructions_to_buffer((None,None))

def command_turret(best_guess_targeting_instruction):
    # Don't send a bunch of turret commands at once
    global timestamp_of_last_turret_command
    if config["Turret"]["MinimumTimeBetweenCommands"] > time.time() - timestamp_of_last_turret_command:
        return
    timestamp_of_last_turret_command = time.time()

    if best_guess_targeting_instruction is None:
        if config["Debug"]["PrintTurretCommand"]:
            print ("turret command: None")
        return

    pan_command = int(best_guess_targeting_instruction[0])
    tilt_command = int(best_guess_targeting_instruction[1])
    turret_command = "rotate ({},{})".format(pan_command, tilt_command)
    arduinoSerial.send_to_arduino(turret_command)
    if config["Debug"]["PrintTurretCommand"]:
        print ("turret command: {}".format(turret_command))

def main():
    camera = None
    if config["Image"]["Type"] == "webcam":
        camera = Camera(CameraType.WEBCAM, config)
    elif config["Image"]["Type"] == "picamera":
        camera = Camera(CameraType.PICAMERA, config)

    # Listen to messages from the Arduino on a spearate thread
    try:
        arduinoSerial.start_reading_thread(config["Debug"]["PrintMessagesFromArduino"])
    except Exception as e:
        print (e)
    
    try:
        target_fps = 30.0
        frame_duration = 1.0 / target_fps
        elapsed_time = 0.033
        global current_pan_angle
        global current_tilt_angle

        while True:
            if arduinoSerial.handshake_completed is False:
                pass
            
            start_time = time.time()
            frame = camera.get_frame() # Get a frame from the camera
            object_detection_results = ai.track_objects(frame) # Get objects in picture

            # Get servo statuses from Arduino
            servoStatus = arduinoSerial.get_message()
            if "servo status" in servoStatus:
                start = servoStatus.find('(') + 1
                end = servoStatus.find(')')
                numbers_str = servoStatus[start:end]
                x_str, y_str = numbers_str.split(',')
                current_pan_angle = int(x_str)
                current_tilt_angle = int(y_str)

            # If something was detected...
            if object_detection_results[0].boxes is not None:
                frame = annotate_image(frame, int(1 / elapsed_time), object_detection_results) # Annotate video feed
                update_targeting(frame, object_detection_results) # Update targeting

                # Fire on target
                if config["Turret"]["AiTurretControl"]:
                    command_turret(targeting.get_best_targeting_instruction(config, current_pan_angle, current_tilt_angle))
            else:
                frame = Imaging.draw_turret_status(frame, current_pan_angle, current_tilt_angle, int(1 / elapsed_time), config["ObjectDetection"]["ValidTargetLabels"])
            
            cv2.imshow('Moosinator Cam', frame)
            k = cv2.waitKey(1)
            if k != -1:
                break

            # Sleep to maintain the target frame rate
            elapsed_time = time.time() - start_time
            time_to_sleep = max(0, frame_duration - elapsed_time)
            time.sleep(time_to_sleep)

    except KeyboardInterrupt:
        print("Interrupted by user.")
    finally:
        camera.release()

if __name__ == "__main__":
    main()