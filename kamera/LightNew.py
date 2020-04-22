import threading
import time
import datetime as dt
import RPi.GPIO as GPIO

class Light (threading.Thread):
    def __init__(self, name, seconds):
        threading.Thread.__init__(self)
        self.name = name
        self.seconds = seconds
        self.endTime = time.now()
        self.status = False
        self.keepRunning = True

    def exit(self):
        self.keepRunning = False

    def setTimeout(self, seconds):
        self.endTime = dt.datetime.now() + dt.timedelta(seconds=seconds)

    def run(self):
        print('Starting light thread')
        while self.keepRunning:
            # turn ON
            if dt.datetime.now() < self.endTime and self.status is False:
                GPIO.output(5, GPIO.LOW)
                self.status = True

            # turn OFF
            if dt.datetime.now() > self.endTime and self.status is True:
                GPIO.output(5, GPIO.HIGH)
                self.status = False

            time.sleep(1)
        print('Light thread finished')

    def setTime(self, time):
        self.seconds = time

    def setLogger(self, Logger):
        self.Logger = Logger
