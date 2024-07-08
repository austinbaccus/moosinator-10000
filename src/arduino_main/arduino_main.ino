#include <Servo.h>

const unsigned int MAX_MESSAGE_LENGTH = 32;
int deg = 0;

Servo panServo;
Servo tiltServo;
const int servoPanPin = 12;
const int servoTiltPin = 13;
const int pan_min = 550;
const int pan_max = 2000;
const int tilt_min = 20;
const int tilt_max = 1500;
const int tilt_degree_min = 100; // With a long cable it's 55, with a short cable it's 100 
const int tilt_degree_max = 180;
const int pan_degree_min = 60;
const int pan_degree_max = 150;
static int turretRotationInstructions[2];

void setup() 
{
  panServo.attach(servoPanPin, pan_min, pan_max);
  tiltServo.attach(servoTiltPin, tilt_min, tilt_max);
  Serial.begin(9600);
  panToAngle(100);
  tiltToAngle(170);
  turretRotationInstructions[0] = 100;
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
      panToAngle(turretRotationInstructions[0]);
      tiltToAngle(turretRotationInstructions[1]);
    }
  }
}

String parseCommand(String data)
{
  return data.substring(0, data.indexOf(' '));
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
}

void panToAngle(int degree)
{
  panServo.write(max(min(degree, pan_degree_max), pan_degree_min));
}

void tiltToAngle(int degree)
{
  tiltServo.write(max(min(degree, tilt_degree_max), tilt_degree_min));
}