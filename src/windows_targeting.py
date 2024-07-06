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

    def update_targets(self, results, labels):
        self.targets = [] # reset target list
        for det in results.xyxy[0].cpu().numpy():
            x1, y1, x2, y2, conf, cls = det
            self.targets.append(Target(conf, labels[int(cls)], [x1,y1,x2,y2]))

    def move_to_target(self):
        print()

def is_target_valid(target, config):
    if target.certainty < config["MinimumConfidence"]:
        return False
    if target.label not in config["ValidTargetLabels"]:
        return False
    return True