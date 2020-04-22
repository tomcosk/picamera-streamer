#!/usr/bin/env python3
import os
# import stat
import logging
import time
import RPi.GPIO as GPIO
import Adafruit_DHT
import threading
import json
import psutil

import signal
from ina219 import INA219
from ina219 import DeviceRangeError

from SendMail import sendMail
import BaseThread


# from Config import Config
import influxdb
from influxdb import InfluxDBClient


print(os.path.dirname(os.path.abspath(__file__)))
GPIO.setmode(GPIO.BCM)
tempSensor = Adafruit_DHT.DHT22
tempPin = 4


keep_running = True

# logging.basicConfig(format='%(levelname)s\t%(asctime)s\t%(name)s\t%(message)s',
#                     filename=os.path.dirname(os.path.abspath(__file__))+'/camera.log', level=logging.INFO)


def signal_handler(signal, frame):
    global keep_running
    keep_running = False
    loop.exit()

    print("Received SIGINT - Shutting down")


signal.signal(signal.SIGINT, signal_handler)


class Loop (BaseThread.BaseThread):
    def __init__(self, name, influxClient, tempSensor, tempPin):
        BaseThread.BaseThread.__init__(self)
        self.keepRunning = True
        self.name = name
        self.influxClient = influxClient
        self.temperature = 0.0
        self.humidity = 0.0
        self.tempSensor = tempSensor
        self.tempPin = tempPin

    def getTemp(self):
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as myfile:
            return int(myfile.read().replace('\n', ''))/1000

    def sendInitData(self):
        json_body = [
            {
                "measurement": "solar",
                "tags": {
                    "host": "siravaCam",
                },
                "time": time.time_ns(),
                "fields": {
                    "tempCpu": 0.0,
                    "tempOut": 0.0,
                    "battV": 0.0,
                    "battC": 0.0,
                    "solarC": 0.0
                }
            }
        ]
        self.sendToDb(json_body)

    def run(self):
        print('Loop started')
        self.sendInitData()
        self.isActive = True
        i = 0

        SHUNT_OHMS = 0.01
        ina1 = INA219(SHUNT_OHMS, address=0x40)
        ina1.configure()

        ina2 = INA219(SHUNT_OHMS, address=0x44)
        ina2.configure()
        lastHumidity = None
        humidityError = 0

        while self.keepRunning:
            actualBattV = float(format(ina1.voltage(), '.1f'))
            # print(actualBattV)
            actualBattC = float(format(ina1.current(), '.1f'))
            actualSolarC = float(format(ina2.current(), '.1f'))
            svmem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            if i == 0 or i > 60:
                humidity, temperature = Adafruit_DHT.read_retry(
                    self.tempSensor, self.tempPin)

                # print(humidity, temperature)
                if humidity is None:
                    self.humidity = 0.0
                else:
                    if lastHumidity is None:
                        self.humidity = float(format(humidity, '.1f'))
                        lastHumidity = self.humidity
                    else:
                        if abs(lastHumidity - humidity) < 20:
                            self.humidity = float(format(humidity, '.1f'))
                            lastHumidity = self.humidity
                        else:
                            humidityError = humidityError+1
                            if humidityError > 5:
                                self.humidity = float(format(humidity, '.1f'))
                                lastHumidity = self.humidity
                                humidityError = 0

                if temperature is None:
                    self.temperature = 0.0
                else:
                    self.temperature = float(format(temperature, '.1f'))

                i = 1

            json_body = [
                {
                    "measurement": "solar",
                    "tags": {
                        "host": "siravaCam",
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "tempCpu": self.getTemp(),
                        "tempOut": self.temperature,
                        "humidity": self.humidity,
                        "battV": actualBattV,
                        "battC": actualBattC,
                        "solarC": actualSolarC,
                        "avail_mem": svmem.available,
                        "avail_swap": swap.free,
                        "cpu_load": psutil.cpu_percent()
                    }
                }
            ]
            # print(json_body)
            self.sendToDb(json_body)
            i = i+1
            time.sleep(1)
        self.isActive = False
        print("Loop finished")

    def sendToDb(self, json):
        try:
            self.influxClient.write_points(json)
        except influxdb.exceptions.InfluxDBServerError as e:
            print(e)


# config = Config(os.path.dirname(os.path.abspath(__file__))+'/config.ini')
# emailer = sendMail(config.getValue('Email', 'recipient'),
#                    'SiravaCam started', 'Camera working')
# emailer.send()

host = '88.212.32.71'
port = 8086
user = 'admin'
password = 'RLsT$2017'
dbname = 'sensors'

client = InfluxDBClient(host, port, user, password, dbname)

loop = Loop('Periodic Loop', client, tempSensor, tempPin)
loop.start()
