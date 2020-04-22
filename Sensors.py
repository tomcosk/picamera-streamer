import Adafruit_DHT
import threading
import time
from pprint import pprint
from BaseThread import BaseThread
import logging

logger = logging.getLogger('Sensors')


class Sensors (BaseThread):
    def __init__(self, name, tempSensor, tempPin, cameraSensors):
        BaseThread.__init__(self)
        self.name = name
        self.temperature = 0
        self.humidity = 0
        self.keepRunning = True
        self.tempPin = tempPin
        self.tempSensor = tempSensor
        self.cameraSensors = cameraSensors
        self.telemetry = {
            'batt': {
                'V': 0.0,
                'C': 0.0
            },
            'solar': {
                'C': 0.0
            },
            'temp': {
                'inside': 0.0,
                'outside': 0.0
            },
            'humidity': 0
        }

    def getTelemetry(self):
        return self.telemetry

    def run(self):
        logger.info('Sensors started')
        self.isActive = True
        i = 0
        time.sleep(5)
        while self.keepRunning:
            self.telemetry = self.cameraSensors.getTelemetry()
            self.telemetry['temp']['outside'] = float(
                format(self.temperature, '.1f'))
            self.telemetry['humidity'] = self.humidity
            if i == 0 or i > 60:
                logger.debug('reading sensor data')
                humidity, temperature = Adafruit_DHT.read_retry(
                    self.tempSensor, self.tempPin)
                if humidity is None:
                    self.humidity = 0
                else:
                    self.humidity = humidity
                if temperature is None:
                    self.temperature = 0
                else:
                    self.temperature = temperature

                i = 1
            time.sleep(1)
            i = i+1
        self.isActive = False
        logger.info("Sensors finished")
