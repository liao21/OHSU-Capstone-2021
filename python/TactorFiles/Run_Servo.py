from Adafruit_PWM_Servo_Driver import PWM
import time

# This file is used by the UDP client to drive the servo motors.
# Revisions: 
# 11-August-2016 Franke: Initial revision

pwm = PWM(0x40, debug=False)
servoChannels = [0, 1, 2, 3, 4]
servoMin = 150
servoMax = 650

pwm.setPWMFreq(60)

# used to start servos with pauses and a return to the 0 degree position after each position change
def startServos(angles):
    while (True):
          for i in range(0, len(servoChannels)):
              pwm.setPWM((int(servoChannels[i]))-1, 0, 150)
          time.sleep(1)
          for i in range(0, len(servoChannels)):
              pwm.setPWM((int(servoChannels[i]))-1, 0, int(getAngle(int(angles[i]))))
          time.sleep(1)
          
# takes in angle value and returns value that is proportional on the scale used by the servo PWM command
def getAngle(num):
    angle = (num / 180.0)*500 + servoMin 
    return angle

# sets each servo to its respective input angle value
def setAngles(angles):
    for i in range(0, 5):
        pwm.setPWM(i, 0, int(getAngle(int(angles[i]))))

# sets all servos back to 0 degree position, usually used when Ctrl-C is entered in the terminal
def originalPos(channels):
    for i in range(0, len(channels)):
        pwm.setPWM((int(channels[i]))-1, 0, 150)