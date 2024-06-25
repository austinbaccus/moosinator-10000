import cv2
from camera import Camera
from ai import AI

def main():
    camera = Camera()
    ai = AI()

    while True:
        # image
        frame = camera.read()
        image = camera.convert_to_pil(frame)

        # depth
        #frame = ai.get_depth(image, None)

        # object detection
        object_detection_results = ai.get_objects(image)

        # boxes
        boxes = get_boxes(frame, object_detection_results, ai.object_detection_model.config.id2label)

        # print data to console
        print_data(object_detection_results, ai.object_detection_model.config.id2label)

        # draw
        cv2.imshow("Moose Cam", boxes)

        # Break the loop on 'q' key press
        if cv2.waitKey(1) == ord('q'):
            break

def get_boxes(image, object_detection_results, labels):
    for score, label, box in zip(object_detection_results["scores"], object_detection_results["labels"], object_detection_results["boxes"]):
        box = [round(i, 2) for i in box.tolist()]

        x1 = int(box[0])
        y1 = int(box[1])
        x2 = int(box[2])
        y2 = int(box[3])

        point1 = (x1, y1)
        point2 = (x2, y2)

        certainty = int((score.item())*100)

        height, width = image.shape[:2]
        text_x_pos = min(width, x1+10)
        text_y_pos = max(0, y2-10)
        text_pos = (text_x_pos, text_y_pos)

        cv2.rectangle(img=image, pt1=point1, pt2=point2, color=(255,0,0), thickness=2)
        cv2.putText(img=image, text=f"{certainty}% {labels[label.item()]}", org=text_pos, fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=(0,0,255), thickness=2)

    return image

def print_data(object_detection_results, labels):
    for score, label, box in zip(object_detection_results["scores"], object_detection_results["labels"], object_detection_results["boxes"]):
        box = [round(i, 2) for i in box.tolist()]

        print(
            f"Detected {labels[label.item()]} with confidence "
            f"{round(score.item(), 3)} at location {box}"
        )

main()