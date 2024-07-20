import base64
import cv2
import numpy as np
import windows_targeting as Targeting

def prepare_ir_image_for_ai(ir_image_base64, config):
    ir_image_data = base64.b64decode(ir_image_base64)
    nparr = np.frombuffer(ir_image_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    frame = rotate_image(frame, config["Image"]["RotateIRImage"])
    return frame

def rotate_image(image, rotation_value):
    if rotation_value == 90:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    if rotation_value == 180:
        return cv2.rotate(image, cv2.ROTATE_180)
    if rotation_value == 270 or rotation_value == -90:
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return image

def draw_boxes(image, objects, width, config):
    for object in objects:
        if Targeting.is_target_valid(object, config):
            text_x_pos = min(width, object.x1+10)
            text_y_pos = max(0, object.y2-10)
            cv2.rectangle(img=image, pt1=(object.x1, object.y1), pt2=(object.x2, object.y2), color=(255,0,0), thickness=2)
            cv2.putText(img=image, text=f"{object.label} {object.certainty}%", org=(text_x_pos, text_y_pos), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=(0,0,255), thickness=1)
    return image

def draw_crosshair(image, width, height):
    return cv2.circle(image, (int(width/2), int(height/2)), 10, (0,0,255), 2)

def draw_turret_status(image, pan, tilt):
    cv2.putText(img=image, text=f"pan: {pan}", org=(10,15), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=(0,255,0), thickness=1)
    cv2.putText(img=image, text=f"tilt:  {tilt}", org=(10,35), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=(0,255,0), thickness=1)
    cv2.putText(img=image, text=f"looking for: cup", org=(10,55), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=(0,255,0), thickness=1)
    return image