import numpy as np

class Target:
    def __init__(self, score, label, box):
        self.x1 = int(box[0])
        self.y1 = int(box[1])
        self.x2 = int(box[2])
        self.y2 = int(box[3])
        self.certainty = int(score*100)
        self.label = label

class Targeting:
    def __init__(self):
        self.targets = []
        self.targeting_instructions_buffer = []

    def update_targets(self, results, labels):
        self.targets = []
        for det in results.xyxy[0].cpu().numpy():
            x1, y1, x2, y2, conf, cls = det
            self.targets.append(Target(conf, labels[int(cls)], [x1,y1,x2,y2]))

    def add_targeting_instructions_to_buffer(self, targeting_instructions):
        self.targeting_instructions_buffer.append(targeting_instructions)
        if len(self.targeting_instructions_buffer) > 10:
            self.targeting_instructions_buffer.pop(0)

    def get_best_targeting_instruction(self):
        # This method returns the best-guess horizontal and vertical degrees the turret needs to rotate in order to be on target.
        # Why not just return the last set of targeting instructions? Good question. Because sometimes the AI
        # object detection gets it really, really wrong and the coordinates are way off from where you actually want the turret to look at. 
        # Here's an example of a buffer with an outlier targeting instruction: [(3, 24), (3, 24), (3, 24), (3, 24), (3, 24), (3, 24), (3, 24), (3, 24), (-47, 11), (3, 24)]
        # If the turret rotated for each instruction, it would (infrequently) encounter those outliers and be all herky-jerky.
        # So with that in mind, this method's job is to remove targeting instruction outliers from the buffer, and return the average of the remaining instruction tuples.

        if len(self.targeting_instructions_buffer) == 0:
            return None
        
        first_values = [x[0] for x in self.targeting_instructions_buffer]
        second_values = [x[1] for x in self.targeting_instructions_buffer]

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
            (x, y) for (x, y) in self.targeting_instructions_buffer
            if lower_bound_first <= x <= upper_bound_first and lower_bound_second <= y <= upper_bound_second
        ]
        
        first_values = [x[0] for x in filtered_tuples]
        second_values = [x[1] for x in filtered_tuples]
        return (int(np.mean(first_values)), int(np.mean(second_values)))

def degrees_to_target(crosshair_coords, target):
    # https://www.raspberrypi.com/documentation/accessories/camera.html
    # RPi Noir v2 Camera specs:
    # Horizontal FOV: 62.2 degrees
    # Vertical FOV:   48.8 degrees

    # These values are reversed from the spec because the camera is (currently) orientated vertically
    camera_horizontal_fov = 48.8
    camera_vertical_fov = 62.2

    screen_width = crosshair_coords[0] * 2
    screen_height = crosshair_coords[1] * 2

    target_center_mass_x = (target.x1+target.x2)/2
    target_center_mass_y = (target.y1+target.y2)/2

    horizontal_diff = target_center_mass_x - crosshair_coords[0]
    vertical_diff = crosshair_coords[1] - target_center_mass_y

    degrees_to_pan = int((horizontal_diff/(screen_width/2)) * camera_horizontal_fov)
    degrees_to_tilt = int((vertical_diff/(screen_height/2)) * camera_vertical_fov)
    
    return (degrees_to_pan, degrees_to_tilt)

def is_target_valid(target, config):
    if target.certainty < config["MinimumConfidence"]:
        return False
    if target.label not in config["ValidTargetLabels"] and len(config["ValidTargetLabels"]) > 0:
        return False
    return True