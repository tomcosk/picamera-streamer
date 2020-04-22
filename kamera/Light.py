import threading
import time
import RPi.GPIO as GPIO

class Light (threading.Thread):
    def __init__(self, name, seconds):
        threading.Thread.__init__(self)
        self.name = name
        self.seconds = seconds
    def run(self):
        print('Start light '+self.name)
        GPIO.output(5, GPIO.LOW)
        time.sleep(self.seconds)
        GPIO.output(5, GPIO.HIGH)

        t = time.strftime('%d.%m.%Y %H:%M:%S', time.localtime())
        print(t+' End light '+self.name)

    def setTime(self, time):
        self.seconds = time

    def setLogger(self, Logger):
        self.Logger = Logger
