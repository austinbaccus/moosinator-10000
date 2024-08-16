import base64
import cv2
import numpy as np
import targeting as Targeting
from ultralytics.utils.plotting import Annotator, colors

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
        text_x_pos = min(width, object.x1+10)
        text_y_pos = max(0, object.y2-10)
        center = object.get_center()
        if Targeting.is_target_valid(object, config):
            cv2.rectangle(img=image, pt1=(object.x1, object.y1), pt2=(object.x2, object.y2), color=(0,0,200), thickness=2)
            cv2.putText(img=image, text=f"{object.label} {object.certainty}% {center}", org=(text_x_pos, text_y_pos), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=(0,0,200), thickness=1)
        else:
            cv2.rectangle(img=image, pt1=(object.x1, object.y1), pt2=(object.x2, object.y2), color=(255,255,0), thickness=2)
            cv2.putText(img=image, text=f"{object.label} {object.certainty}% {center}", org=(text_x_pos, text_y_pos), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=(255,255,0), thickness=1)
    return image

def draw_crosshair(image, width, height):
    return cv2.circle(image, (int(width/2), int(height/2)), 10, (0,0,255), 2)

def draw_turret_status(image, pan, tilt, fps, target):
    cv2.putText(img=image, text=f"pan: {pan}", org=(10,15), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=(0,0,255), thickness=1)
    cv2.putText(img=image, text=f"tilt:  {tilt}", org=(10,35), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=(0,0,255), thickness=1)
    cv2.putText(img=image, text=f"fps:  {fps}", org=(10,55), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=(0,0,255), thickness=1)
    cv2.putText(img=image, text=f"looking for: {target}", org=(10,75), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=(0,0,255), thickness=1)
    return image

def draw_tracks(image, track_history, boxes, track_ids):
    # Plot the tracks
    for box, track_id in zip(boxes, track_ids):
        x, y, w, h = box
        track = track_history[track_id]
        track.append((float(x), float(y)))  # x, y center point
        if len(track) > 30:  # retain 90 tracks for 90 frames
            track.pop(0)

        # Draw the tracking lines
        # (blue,green,red)
        points = np.hstack(track).astype(np.int32).reshape((-1, 1, 2))
        cv2.polylines(image, [points], isClosed=False, color=(0,255,255), thickness=2)

    for track_id in track_ids:
        if len(track_history[track_id]) >= 2:
            prev_center = track_history[track_id][-2]
            curr_center = track_history[track_id][-1]
            displacement = np.sqrt((curr_center[0] - prev_center[0]) ** 2 + (curr_center[1] - prev_center[1]) ** 2)
            center = (int(curr_center[0]), int(curr_center[1]))
            cv2.circle(img=image, center=center, radius=3, color=(150,10,255), thickness=8)

    return image

def draw_mask(image, object_detection_results):
    annotator = Annotator(image, line_width=2)
    if object_detection_results[0].boxes.id is not None and object_detection_results[0].masks is not None:
        masks = object_detection_results[0].masks.xy
        track_ids = object_detection_results[0].boxes.id.int().cpu().tolist()

        for mask, track_id in zip(masks, track_ids):
            annotator.seg_bbox(mask=mask, mask_color=colors(track_id, True))#, track_label=str(track_id))
    return image