import time
from .Light import Light
from .Fan import Fan
import RPi.GPIO as GPIO
import json
import urllib.request
import datetime
from .SPIHelper import SPI
from ina219 import INA219
from ina219 import DeviceRangeError
import threading


class Controller(threading.Thread):
    def __init__(self, options, websocketFactory):
        threading.Thread.__init__(self)

        self.factory = websocketFactory
        self.keepRunning = True
        print(options)
        GPIO.setmode(GPIO.BCM)
        self.options = options
        self.fanPin = options['fan']
        self.lightPin = options['light']
        self.motionSensorPin = options['pir']
        self.maxFanTime = options['maxFanTime']
        self.light = 0

        self.telemetry = {}

        self.motionStatus = 1
        self.tempStatus = 20

        self.lightThread = Light('light thread', 20)
        self.lightThreadUser = Light('light thread user', 20)
        self.fanThread = Fan('fan thread', 20, 50, self.maxFanTime)

        self.i = 0
        self.SPI = SPI(
            options['spiClk'],
            options['spiMiso'],
            options['spiMosi'],
            options['spiCs']
        )

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(5, GPIO.OUT)
        GPIO.setup(6, GPIO.OUT)
        GPIO.setup(17, GPIO.OUT)
        GPIO.setup(16, GPIO.OUT)
        GPIO.setup(13, GPIO.OUT)
        GPIO.setup(21, GPIO.IN)

        GPIO.output(5, GPIO.LOW)
        GPIO.output(6, GPIO.LOW)
        time.sleep(2)
        GPIO.output(5, GPIO.HIGH)
        GPIO.output(6, GPIO.HIGH)
        GPIO.output(17, GPIO.HIGH)
        GPIO.output(16, GPIO.HIGH)
        GPIO.output(13, GPIO.HIGH)
        time.sleep(2)

    def exit(self):
        self.keepRunning = False

    def setLogger(self, Logger):
        self.Logger = Logger

    def getTemp(self):
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as myfile:
            return int(myfile.read().replace('\n', ''))/1000

    def getMotion(self):
        #        if (GPIO.input(17) == False):
        #            return 0
        #        else:
        return 1

    def getTelemetry(self):
        return self.telemetry

    def run(self):
        battVoltage = []
        battCurrent = []
        solarCurrent = []

        SHUNT_OHMS = 0.01
        ina1 = INA219(SHUNT_OHMS, address=0x40)
        ina1.configure()

        ina2 = INA219(SHUNT_OHMS, address=0x44)
        ina2.configure()

        while self.keepRunning:

            actualBattV = float(format(ina1.voltage(), '.1f'))
            # print(actualBattV)
            actualBattC = ina1.current()
            actualSolarC = ina2.current()

            battVoltage.append(actualBattV)
            battCurrent.append(actualBattC)
            solarCurrent.append(actualSolarC)
            battVoltageAvg = sum(battVoltage) / len(battVoltage)
            battCurrentAvg = sum(battCurrent) / len(battCurrent)
            solarCurrentAvg = sum(solarCurrent) / len(solarCurrent)

            hasZero = 0
            solarCurrentMax = 0
            for value in solarCurrent:
                if value < 1:
                    hasZero = 1
                    break
            if hasZero == 1:
                tmpSolarValues = []
                for value in solarCurrent:
                    if value > 100:
                        tmpSolarValues.append(value)

                if len(tmpSolarValues) > 0:
                    solarCurrentMax = sum(tmpSolarValues) / len(tmpSolarValues)
                    if solarCurrentMax > 0:
                        solarCurrentAvg = sum(
                            tmpSolarValues) / len(tmpSolarValues)

            if len(battVoltage) > self.options['avgFor'] / self.options['sleepFor']:
                battVoltage.pop(0)
                battCurrent.pop(0)
                solarCurrent.pop(0)

            if round(battVoltageAvg, 2) > 12.5:
                lightTime = self.options['highBatteryLightTime']
            elif round(battVoltageAvg, 2) <= 12.5 and round(battVoltageAvg, 2) > 12.3:
                lightTime = self.options['medBatteryLightTime']
            else:
                lightTime = self.options['lowBatteryLightTime']

            self.lightThread.setTime(lightTime)

#            self.motionStatus = self.getMotion()
            self.tempStatus = self.getTemp()

            now = datetime.datetime.now()

#            if self.motionStatus == 1 and (self.lightThread.is_alive() is False and self.lightThreadUser.is_alive() is False) and (now.hour <= 4 or now.hour >= 21):
#                self.lightThread = Light('light thread', lightTime)
#                self.lightThread.start()

            # print('light: ', GPIO.input(self.lightPin))
            # if GPIO.input(21) == 1 and (self.lightThreadUser.is_alive() is False and self.lightThread.is_alive() is False):
            #     self.lightThreadUser = Light("Thread-light-User", lightTime)
            #     self.lightThreadUser.start()

            if self.tempStatus > 60 and self.fanThread.is_alive() is False:
                print('Fan is not running and temp is as high as ' +
                      str(self.tempStatus)+' deg')
                self.fanThread = Fan(
                    'fan thread', self.tempStatus, 50, self.maxFanTime)
                self.fanThread.start()
            else:
                self.fanThread.setTemp(self.tempStatus)

            self.telemetry = {
                'batt': {
                    'V': round(actualBattV, 1),
                    'C': round(actualBattC, 1)
                },
                'solar': {
                    'C': round(actualSolarC, 1)
                },
                'temp': {
                    'inside': round(self.tempStatus, 1)
                }
            }

            time.sleep(self.options['sleepFor'])
        print('Camera Sensors finish')
