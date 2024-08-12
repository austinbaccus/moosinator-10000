#include <Servo.h>

const unsigned int MAX_MESSAGE_LENGTH = 32;

Servo servoPan;
Servo servoTilt;
const int servoPanPin = 6;
const int servoTiltPin = 5;

static int turretRotationInstructions[2];

void setup() 
{
  servoPan.attach(servoPanPin);
  servoTilt.attach(servoTiltPin);
  Serial.begin(9600);
  pan(90);
  tilt(90);
  turretRotationInstructions[0] = 90;
  turretRotationInstructions[1] = 90;
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

  turretRotationInstructions[0] = max(min(desiredPanDegree, 180), 0);
  turretRotationInstructions[1] = max(min(desiredTiltDegree, 180), 0);
  
  Serial.print(turretRotationInstructions[0]);
  Serial.print(",");
  Serial.println(turretRotationInstructions[1]);
}

void pan(int angle)
{
  servoPan.write(max(min(angle, 180), 0));
}

void tilt(int angle)
{
  servoTilt.write(max(min(angle, 180), 0));
}
