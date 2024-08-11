from collections import defaultdict
import platform
import io
import base64
import json
import time
import cv2
import ai
from targeting import Targeting
import targeting as TargetAcq
import image as Imaging
from serial import ArduinoSerial
from ultralytics.utils.plotting import Annotator, colors

if platform.system() == "Linux":
    import picamera
if platform.system() == "Windows":
    from PIL import Image

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

def analyze_image_stream_pi(camera):
    global start
    stream = io.BytesIO()

    for _ in camera.capture_continuous(stream, format='jpeg', use_video_port=True):
        stream.seek(0)
        
        # FPS
        fps = round(1/(time.time() - start),1)
        fps_buffer.append(fps)
        if len(fps_buffer) > 10:
            fps_buffer.pop(0)
        smooth_fps = int(sum(fps_buffer) / len (fps_buffer))
        start = time.time()

        # Get image from camera
        image = Imaging.prepare_ir_image_for_ai(base64.b64encode(stream.read()).decode('utf-8'), config)

        # Tell the turret to do stuff and draw stuff to the camera preview
        loop(image, smooth_fps)

        stream.seek(0)
        stream.truncate()

def analyze_image_stream_windows(camera):
    global start

    # Check if the webcam is opened correctly
    if not camera.isOpened():
        raise IOError("Cannot open webcam")
    
    while True:
        # FPS
        fps = round(1/(time.time() - start),1)
        fps_buffer.append(fps)
        if len(fps_buffer) > 10:
            fps_buffer.pop(0)
        smooth_fps = int(sum(fps_buffer) / len (fps_buffer))
        start = time.time()

        # Capture frame-by-frame
        ret, frame = camera.read()
        loop(frame, smooth_fps)

        # Press 'q' to exit the loop
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

def loop(image, smooth_fps):
    # Get objects in picture
    object_detection_results = ai.track_objects(image)

    # If nothing was detected, return early
    if object_detection_results[0].boxes is None:
        return
    
    # Annotate video feed
    cv2.imshow('Moosinator Cam', annotate_image(image, smooth_fps, object_detection_results))

    # Update targeting
    update_targeting(image, object_detection_results)

    # Fire on target
    if config["Turret"]["AiTurretControl"]:
        command_turret(targeting.get_best_targeting_instruction(config))

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
    else:
        targeting.add_targeting_instructions_to_buffer((None,None))

def command_turret(best_guess_targeting_instruction):
    if best_guess_targeting_instruction is None:
        return
    global current_pan_angle
    global current_tilt_angle
    current_pan_angle = max(min(current_pan_angle + int(best_guess_targeting_instruction[1]), 150), 60)
    current_tilt_angle = max(min(current_tilt_angle + int(best_guess_targeting_instruction[0]), 180), 100)
    arduinoSerial.send("rotate ({},{})".format(int(best_guess_targeting_instruction[0]), int(best_guess_targeting_instruction[1])))

def main():
    try:
        if platform.system() == "Linux":
            #with picamera.PiCamera(resolution=(config["TargetResolution"][0], config["TargetResolution"][1])) as camera:
                #analyze_image_stream_pi(camera)
            camera = cv2.VideoCapture(0)
            analyze_image_stream_windows(camera)

        if platform.system() == "Windows":
            camera = cv2.VideoCapture(0)
            analyze_image_stream_windows(camera)
            
    except KeyboardInterrupt:
        return

main()