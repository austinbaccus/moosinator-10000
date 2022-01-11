import numpy as np
import argparse
import cv2
from os.path import dirname, join
import winsound
import time
import math
from pydub import AudioSegment
from pydub.playback import play

# Constructor y sus argumentos. Confidencia seteada en 0.3 por default.
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--confidence", type=float, default=0.3,
	help="minimum probability to filter weak detections")
protoPath = join(dirname(__file__), "../MobileNetSSD_deploy.prototxt")
modelPath = join(dirname(__file__), "../MobileNetSSD_deploy.caffemodel")
args = vars(ap.parse_args())

CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
	"bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
	"dog", "horse", "motorbike", "person", "pottedplant", "sheep",
	"sofa", "train", "tvmonitor"]
COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))

time_of_last_fire = time.time() - 5

def draw_target_center(target, image):
    radius=6
    color=(0, 0, 255)
    thickness=1
    cv2.circle(image, target, radius, color, thickness)
    cv2.circle(image, target, int(radius/2), color, thickness)

def is_aimed_at_target(target, image, distance_threshold=50):
    # center is [320,240]
    crosshair = (320,240)
    cv2.circle(image, crosshair, 10, (255,0,0), 2)

    x = target[0] - crosshair[0]
    y = target[1] - crosshair[1]
    dist_to_target = int(math.sqrt(x*x + y*y))
    cv2.putText(image, str(dist_to_target), (20,50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
    return dist_to_target < distance_threshold

def can_fire(target_type):
    if target_type == 'person' or target_type == 'cat':
        delta = time.time() - time_of_last_fire
        if delta > 10:
            return True
    return False

def fire_main_cannon(image, target_type):
    # update last fire time
    global time_of_last_fire
    time_of_last_fire = time.time()

    # play firing sound
    audio = AudioSegment.from_wav(r'.\\resources\\firing_main_cannon.wav')
    play(audio)

    # save picture
    timestr = target_type + "-" + time.strftime("%Y%m%d-%H%M%S") + '.jpg' 
    filename = "shots/" + timestr
    #cv2.imwrite(filename, image)

def scan(image, net):
    (h, w) = image.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 0.007843,
            (300, 300), 127.5)
    # enviamos el blob y procesamos las detecciones. Descomentar la siguiente linea para informar el proceso.
    net.setInput(blob)
    detections = net.forward()
    for i in np.arange(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]

        #Filter detecciones por valor de confidencia seteado
        if confidence > args["confidence"]:
            #Si coincide lo marcamos en la imagen
            idx = int(detections[0, 0, i, 1])
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            #Informamos la deteccion. 
            label = "{}: {:.2f}%".format(CLASSES[idx], confidence * 100)

            #Esta linea filtra por gatos, perros o personas.
            if CLASSES[idx] == 'cat' or CLASSES[idx] == 'dog'  or CLASSES[idx] == 'person':
                print("Detected {}".format(label))
                cv2.rectangle(image, (startX, startY), (endX, endY), COLORS[idx], 2)
                
                target = (int(endX - ((endX - startX)/2)), int(endY - ((endY - startY)/2)))
                draw_target_center(target, image)

                if is_aimed_at_target(target, image, 40) and can_fire(CLASSES[idx]):
                    fire_main_cannon(image, CLASSES[idx])

                y = startY - 15 if startY - 15 > 15 else startY + 15

                cv2.putText(image, label, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[idx], 2)
                #almaceno una captura en la carpeta shots, si no se quiere guardar la imagen comentar las proximas 3 lineas
                            
def main():
    #Cargamos el modelo
    print("Beginning sentry routine")
    net = cv2.dnn.readNetFromCaffe(protoPath, modelPath)

    #Cargamos imagen, ajustamos a 300x300 y normalizamos para el modelo.

    #Levantamos la webcam de la notebook 
    cap = cv2.VideoCapture(0)

    while 1: 
        ret, img = cap.read() 
        image = img

        # scan for targets
        scan(image, net)

        # Mostramos imagen 
        cv2.imshow("Output", image)
        k = cv2.waitKey(50) & 0xff

        # Para salir presionar tecla ESC
        if k == 27: 
            break

    #Cerramos ventana y limpiamos memoria
    cap.release() 
    cv2.destroyAllWindows() 

main()