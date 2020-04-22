import threading
import time
import RPi.GPIO as GPIO

class Fan (threading.Thread):
    def __init__(self, name, temp, finalTemp, maxTime):
        threading.Thread.__init__(self)
        self.startTime = time.time()
        self.name = name
        self.finalTemp = finalTemp
        self.temp = temp
        self.maxTime = maxTime
    def run(self):
        #gpio pin turn on
        print('Start Fan')
        GPIO.output(6, GPIO.LOW)
        while self.temp > self.finalTemp:
            print(self.temp, self.finalTemp)
            if (round(time.time()) - round(self.startTime)) > self.maxTime:
                break
            time.sleep(1)

        #gpio pin turn of
        GPIO.output(6, GPIO.HIGH)
        print('End Fan')

    def stop(self):
        self.alive = False
        self.join()

    def setTemp(self,temp):
        self.temp = temp

    def setLogger(self, Logger):
        self.Logger = Logger
