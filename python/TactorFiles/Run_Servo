from Adafruit_PWM_Servo_Driver import PWM
import time


pwm = PWM(0x40, debug=False)
servoChannels = [0, 1, 2, 3, 4]
servoMin = 150
servoMax = 650

pwm.setPWMFreq(60)
def startServos(angles):
    while (True):
          for i in range(0, len(channels)):
              pwm.setPWM((int(channels[i]))-1, 0, 150)
          time.sleep(1)
          for i in range(0, len(channels)):
              pwm.setPWM((int(channels[i]))-1, 0, int(getAngle(int(angles[i]))))
          time.sleep(1)
          

def getAngle(num):
    angle = (num / 180.0)*500 + servoMin 
    return angle

def setAngles(angles):
    for i in range(0, 5):
        pwm.setPWM(i, 0, int(getAngle(int(angles[i]))))

def originalPos(channels):
    for i in range(0, len(channels)):
        pwm.setPWM((int(channels[i]))-1, 0, 150)