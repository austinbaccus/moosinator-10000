#include <Servo.h>

const unsigned int MAX_MESSAGE_LENGTH = 32;

Servo panServo;
Servo tiltServo;
const int servoPanPin = 12;
const int servoTiltPin = 10;

const int pan_min = 100;
const int pan_max = 500;
const int pan_degree_min = 0;
const int pan_degree_max = 180;

const int tilt_min = 100;
const int tilt_max = 600;
const int tilt_degree_min = 90;
const int tilt_degree_max = 195;

static int turretRotationInstructions[2];

void setup() 
{
  panServo.attach(servoPanPin, pan_min, pan_max);
  tiltServo.attach(servoTiltPin, tilt_min, tilt_max);
  Serial.begin(9600);
  pan(90);
  tilt(170);
  turretRotationInstructions[0] = 90;
  turretRotationInstructions[1] = 170;
}

void loop() 
{
  if (Serial.available() > 0) 
  {
    String incomingString = Serial.readStringUntil('\n');
    String command = incomingString.substring(0, incomingString.indexOf(' '));
    
    if (command == "rotate")
    {
      parseRotationDegrees(incomingString);
      pan(turretRotationInstructions[0]);
      tilt(turretRotationInstructions[1]);
    }
  }
}

int* parseRotationDegrees(String data)
{
  // expected format: "rotate (1,2)"
  String details = data.substring(data.indexOf('('));
  
  details.remove(0, 1);
  details.remove(details.length() - 1);
  
  int commaIndex = details.indexOf(',');
  int panDegree = details.substring(0, commaIndex).toInt();
  int tiltDegree = details.substring(commaIndex+1).toInt();

  int desiredPanDegree = turretRotationInstructions[0] + panDegree;
  int desiredTiltDegree = turretRotationInstructions[1] + tiltDegree;

  turretRotationInstructions[0] = max(min(desiredPanDegree, pan_degree_max), pan_degree_min);
  turretRotationInstructions[1] = max(min(desiredTiltDegree, tilt_degree_max), tilt_degree_min);
  Serial.print(turretRotationInstructions[0]);
  Serial.print(",");
  Serial.println(turretRotationInstructions[1]);
}

void pan(int angle)
{
  int servo_angle = map(angle,0,180,30,180);
  panServo.write(max(min(servo_angle, pan_degree_max), pan_degree_min));
}

void tilt(int angle)
{
  int servo_angle = map(angle,90,210,90,180);
  tiltServo.write(max(min(servo_angle, tilt_degree_max), tilt_degree_min));
}