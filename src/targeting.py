import math
import numpy as np

class Target:
    def __init__(self, score, label, box):
        self.x1 = int(box[0])
        self.y1 = int(box[1])
        self.x2 = int(box[2])
        self.y2 = int(box[3])
        self.certainty = int(score*100)
        self.label = label

class TrackedTarget:
    def __init__(self, label, id, confidence, box, target_track_history):
        self.label = label
        self.id = id
        self.confidence = confidence

        self.x1 = int(box[0])
        self.y1 = int(box[1])
        self.x2 = int(box[2])
        self.y2 = int(box[3])

        self._target_track_history = target_track_history
    
    @property
    def target_track_history(self):
        # Making this read-only because this any change made here will carry over to main's tracking history.
        return self._target_track_history

    def get_displacement(self):
        """
        Get's the distance the target has moved since the last frame.
        """
        if len(self.target_track_history) >= 2:
            prev_center = self.target_track_history[-2]
            curr_center = self.target_track_history[-1]
            return np.sqrt((curr_center[0] - prev_center[0]) ** 2 + (curr_center[1] - prev_center[1]) ** 2)
        else:
            return -1
    
    def get_center(self):
        """
        Get's the target's center coordinates.
        """
        if len(self.target_track_history) >= 1:
            center = self.target_track_history[-1]
            return (int(center[0]), int(center[1]))
        else:
            return None

class Targeting:
    def __init__(self):
        self.detected_objects = []
        self.targeting_instructions_buffer = []

    def update_detected_objects(self, results, labels, ai_name, track_history = None):
        self.detected_objects = []

        if ai_name == "yolov5":
            for det in results:
                x1, y1, x2, y2, conf, cls = det
                self.detected_objects.append(Target(conf, labels[int(cls)], [x1,y1,x2,y2]))

        if ai_name == "yolov8":
            try:
                boxes = results[0].boxes.xyxy.cpu()
                clss = results[0].boxes.cls.cpu().tolist()
                track_ids = results[0].boxes.id.int().cpu().tolist()
                confs = results[0].boxes.conf.float().cpu().tolist()

                for box, cls, track_id, conf in zip(boxes, clss, track_ids, confs):
                    label = labels[int(cls)]
                    confidence = conf
                    x1, y1, x2, y2 = box
                    id = track_id
                    
                    # Store tracking history
                    track = track_history[track_id]
                    track.append((int((box[0] + box[2]) / 2), int((box[1] + box[3]) / 2)))
                    if len(track) > 30:
                        track.pop(0)
                        
                    self.detected_objects.append(TrackedTarget(label, id, confidence, box, track_history[track_id]))
            except:
                return

    def add_targeting_instructions_to_buffer(self, targeting_instructions):
        self.targeting_instructions_buffer.append(targeting_instructions)
        if len(self.targeting_instructions_buffer) > 5:
            self.targeting_instructions_buffer.pop(0)

    def get_best_targeting_instruction(self, config, current_pan_angle, current_tilt_angle):
        # This method returns the best-guess horizontal and vertical degrees the turret needs to rotate in order to be on target.
        # Why not just return the last set of targeting instructions? Good question. Because sometimes the AI
        # object detection gets it really, really wrong and the coordinates are way off from where you actually want the turret to look at. 
        # Here's an example of a buffer with an outlier targeting instruction: [(3, 24), (3, 24), (3, 24), (3, 24), (3, 24), (3, 24), (3, 24), (3, 24), (-47, 11), (3, 24)]
        # If the turret rotated for each instruction, it would (infrequently) encounter those outliers and be all herky-jerky.
        # So with that in mind, this method's job is to remove targeting instruction outliers from the buffer, and return the average of the remaining instruction tuples.

        # If no targets are found, reset turret to (90, 90)
        default_value = ((90 - current_pan_angle, 90 - current_tilt_angle))

        if config["Debug"]["PrintTargetingBuffer"]:
            print(self.targeting_instructions_buffer)

        if len(self.targeting_instructions_buffer) == 0:
            return None
        
        valid_tuples = [
            (x, y) for (x, y) in self.targeting_instructions_buffer
            if x is not None and y is not None
        ]

        if config["Debug"]["PrintFilteredTargetingBuffer"]:
            print(valid_tuples)

        if len(valid_tuples) < 3:
            return default_value
        
        first_values = [x[0] for x in valid_tuples]
        second_values = [x[1] for x in valid_tuples]

        def calculate_iqr(data):
            Q1 = np.percentile(data, 25)
            Q3 = np.percentile(data, 75)
            IQR = Q3 - Q1
            return Q1, Q3, IQR

        Q1_first, Q3_first, IQR_first = calculate_iqr(first_values)
        Q1_second, Q3_second, IQR_second = calculate_iqr(second_values)

        lower_bound_first = Q1_first - 1.5 * IQR_first
        upper_bound_first = Q3_first + 1.5 * IQR_first
        lower_bound_second = Q1_second - 1.5 * IQR_second
        upper_bound_second = Q3_second + 1.5 * IQR_second

        filtered_tuples = [
            (x, y) for (x, y) in valid_tuples
            if lower_bound_first <= x <= upper_bound_first and lower_bound_second <= y <= upper_bound_second
        ]
        
        first_values = [x[0] for x in filtered_tuples]
        second_values = [x[1] for x in filtered_tuples]
        return (int(np.mean(first_values)/config["Turret"]["TurretDampeningFactor"]), int(np.mean(second_values)/config["Turret"]["TurretDampeningFactor"]))
    
    def get_best_target(self, valid_target_labels, crosshair_coords):
        potential_targets = []

        # get valid targets
        for o in self.detected_objects:
            if o.label in valid_target_labels:
                potential_targets.append(o)

        # find closest target
        target = None
        if len(potential_targets) > 0:
            target = potential_targets[0]
            for p in potential_targets:
                if self.__get_aiming_proximity_to_detected_object(crosshair_coords, p) < self.__get_aiming_proximity_to_detected_object(crosshair_coords, target):
                    target = p
        
        return target
    
    def __get_aiming_proximity_to_detected_object(self, crosshair_coords, detected_object):
        delta_x = math.pow(crosshair_coords[0] - ((detected_object.x1 + detected_object.x2) / 2), 2)
        delta_y = math.pow(crosshair_coords[1] - ((detected_object.y1 + detected_object.y2) / 2), 2)
        return int(math.sqrt(delta_x + delta_y))

def degrees_to_target(crosshair_coords, target):
    # https://www.raspberrypi.com/documentation/accessories/camera.html
    # RPi Noir v2 Camera specs:
    # Horizontal FOV: 62.2 degrees
    # Vertical FOV:   48.8 degrees

    camera_horizontal_fov = 62.2
    camera_vertical_fov = 48.8

    screen_width = crosshair_coords[0] * 2
    screen_height = crosshair_coords[1] * 2

    target_center_mass_x = (target.x1+target.x2)/2
    target_center_mass_y = (target.y1+target.y2)/2

    horizontal_diff = target_center_mass_x - crosshair_coords[0]
    vertical_diff = crosshair_coords[1] - target_center_mass_y

    degrees_to_pan = int((horizontal_diff/(screen_width/2)) * camera_horizontal_fov)
    degrees_to_tilt = int((vertical_diff/(screen_height/2)) * camera_vertical_fov)
    
    return (int(-degrees_to_pan), -int(degrees_to_tilt))

def is_target_valid(target, config):
    if target.certainty < config["ObjectDetection"]["MinimumConfidence"]:
        return False
    if target.label not in config["ObjectDetection"]["ValidTargetLabels"] and len(config["ObjectDetection"]["ValidTargetLabels"]) > 0:
        return False
    return True