#!/usr/bin/env python3
import sys
import io
import os
import stat
import picamera
import logging
from logging.handlers import TimedRotatingFileHandler
import datetime as dt
import time
from subprocess import Popen, PIPE
import RPi.GPIO as GPIO
import Adafruit_DHT
import threading
import json
import random
import string

from twisted.python import log
from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketServerFactory
import signal

from Parser import Parser
from Executer import Executer
from Sensors import Sensors
from TimeAnotate import TimeAnotate
from Imager import Imager
from Recording import Recording
from WebsocketProtocol import MyServerProtocol
from SendMail import sendMail
import BaseThread

from kamera import Controller, Logger

from Config import Config
import influxdb
from influxdb import InfluxDBClient


print(os.path.dirname(os.path.abspath(__file__)))

tempSensor = Adafruit_DHT.DHT22
tempPin = 4


keep_running = True
cached_img = dt.datetime.now()
b64Image = ''

logPath = os.path.dirname(os.path.abspath(__file__))+'/logs/camera.log'
logging.basicConfig(format='%(levelname)s\t%(asctime)s\t%(name)s\t%(message)s',
                    filename=logPath, level=logging.INFO)

rotateHandler = TimedRotatingFileHandler(logPath,
                                         when="d",
                                         interval=1,
                                         backupCount=3)

# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter(
    '%(asctime)s\t%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)
logging.getLogger('').addHandler(rotateHandler)


def signal_handler(signal, frame):
    global keep_running
    keep_running = False
    sensors.exit()
    imager.exit()
    anotate.exit()
#    recording.exit()
    CameraSensors.exit()
    loop.exit()

    logging.info("Received SIGINT - Shutting down")
    reactor.stop()


class AutoVivification(dict):
    """Implementation of perl's autovivification feature."""

    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value


class CameraFactory:
    def __init__(self):
        self.camera = False
        self.hi = Popen([
            'cvlc',
            'stream:///dev/stdin',
            '--sout', '#standard{access=http,mux=ts,dst=:8011}',
            ':demux=h264'
        ],
            stdin=PIPE, stdout=PIPE, stderr=io.open(os.devnull, 'wb'),
            shell=False, close_fds=True)

        self.low = Popen([
            'cvlc',
            'stream:///dev/stdin',
            '--sout', '#standard{access=http,mux=ts,dst=:8012}',
            ':demux=h264'
        ],
            stdin=PIPE, stdout=PIPE, stderr=io.open(os.devnull, 'wb'),
            shell=False, close_fds=True)

    def getCamera(self):
        return self.camera

    def createCamera(self):
        try:
            resolution = config.getValue('Global', 'resolution')
            fps = int(config.getValue('Global', 'fps'))
            sensor_mode = int(config.getValue('Global', 'sensor_mode'))
            STREAM_WIDTH_HI = int(config.getValue('Global', 'stream_width_hi'))
            STREAM_HEIGHT_HI = int(config.getValue(
                'Global', 'stream_height_hi'))
            logging.info('sensormode %s', str(sensor_mode))

            self.camera = picamera.PiCamera(
                sensor_mode=sensor_mode, resolution=resolution, framerate=fps)
            print(self.camera)
            logging.info('resolution %s', str(self.camera.resolution))
            logging.info('fps %s', str(self.camera.framerate))

            self.camera.start_recording(
                self.hi.stdin, format='h264', splitter_port=3, bitrate=3000000)
            self.camera.start_recording(self.low.stdin, format='h264', splitter_port=2, resize=(int(
                config.getValue('Global', 'WIDTH_LOW')), int(config.getValue('Global', 'HEIGHT_LOW'))), bitrate=1000000)
        except picamera.PiCameraError as e:
            logging.exception(e)
            self.camera = False
        return self.camera

    def restart(self):
        self.camera.close()
        self.createCamera()
        return self.camera


class Loop (BaseThread.BaseThread):
    def __init__(self, name, websocketFactory, camera, parser, executer, influxClient):
        BaseThread.BaseThread.__init__(self)
        self.factory = websocketFactory
        self.keepRunning = True
        self.name = name
        self.camera = camera
        self.parser = parser
        self.executer = executer
        self.influxClient = influxClient

    def randomString(self):
        digits = "".join([random.choice(string.digits) for i in range(4)])
        chars = "".join([random.choice(string.ascii_letters)
                         for i in range(4)])
        return digits + chars

    def run(self):
        logging.info('Loop started')
        print(dt.datetime.now().hour)
        self.isActive = True
        i = 0
        while self.keepRunning:
            self.parser.parseSun()
            sunrise = self.parser.getSunrise()
            sunset = self.parser.getSunset()
            # print('now hour: '+str(dt.datetime.now().hour))
            # print('sunrise: '+str(sunrise.hour))
            # print('sunset: '+ str(sunset.hour))

            if (sunrise is not 0 and sunset is not 0):
                '''
                print('now: ', str(dt.datetime.now().hour), str(dt.datetime.now().minute))
                print('sunrise: ', str(sunrise.hour), str(sunrise.minute))
                print('sunset: ', str(sunset.hour), str(sunset.minute))
                '''
                if (dt.datetime.now().hour == sunrise.hour and dt.datetime.now().minute == sunrise.minute):
                    self.executer.loadConfig('CameraDay')
                if (dt.datetime.now().hour == sunset.hour and dt.datetime.now().minute == sunset.minute):
                    self.executer.loadConfig('CameraNight')

            connections = len(self.factory.clients)
            authenticated = 0
            telemetry = factory.sensors.getTelemetry()
            for client in self.factory.clients:
                if client.authenticated is True:
                    authenticated = authenticated + 1

            for client in self.factory.clients:
                if client.authenticated is True:
                    msgToSend = {'type': 'telemetry', 'value': telemetry}
                    msgToSend['value']['camera'] = {
                        'shutter_speed': camera.shutter_speed,
                        'exposure_speed': camera.exposure_speed
                    }
                    msgToSend['value']['pins'] = {
                        '16': GPIO.input(16),
                        '13': GPIO.input(13),
                        '5': GPIO.input(5),
                        '6': GPIO.input(6),
                        '17': GPIO.input(17)
                    }
                    client.sendMessage(json.dumps(msgToSend).encode('utf-8'))

                    services = AutoVivification()
                    for item in self.factory.services:
                        services['services'][item.name] = item.isActive

                    services['users']['connected'] = connections
                    services['users']['authenticated'] = authenticated

                    msgToSend = json.dumps(
                        {'type': 'status', 'value': services})
                    client.sendMessage(msgToSend.encode('utf-8'))

            json_body = [
                {
                    "measurement": "solar",
                    "tags": {
                        "host": "siravaCam",
                    },
                    "time": time.time_ns(),
                    "fields": {
                        "tempCpu": telemetry['temp']['inside'],
                        "tempOut": telemetry['temp']['outside'],
                        "battV": telemetry['batt']['V'],
                        "battC": telemetry['batt']['C'],
                        "solarC": telemetry['solar']['C']
                    }
                }
            ]

            # print(json_body)
            # try:
            #     self.influxClient.write_points(json_body)
            # except influxdb.exceptions.InfluxDBServerError as e:
            #     print(e)

            time.sleep(1)
            i = i + 1
        self.isActive = False
        logging.info("Loop finished")


config = Config(os.path.dirname(os.path.abspath(__file__))+'/config.ini')
emailer = sendMail(config.getValue('Email', 'recipient'),
                   'SiravaCam started', 'Camera working')
emailer.send()

cameraFac = CameraFactory()
camera = cameraFac.createCamera()

# imager = Imager('imager', camera, cameraFac)


# log.startLogging(sys.stdout)

GPIO.setmode(GPIO.BCM)

imager = Imager('Imager', camera, cameraFac)
imager.start()
factory = WebSocketServerFactory(u"ws://127.0.0.1:9001")
factory.setProtocolOptions(
    autoPingInterval=3, autoPingTimeout=10, autoPingSize=20)
factory.camera = camera
factory.executer = Executer(camera, config, imager)
factory.numClients = 0
factory.clients = []
factory.authenticated = False
# factory.heartBeatValue = ''
# factory.heartBeatTimestaamp = dt.datetime.now()
# factory.isAlive = True
factory.protocol = MyServerProtocol
# factory.imager = imager
factory.services = []

if camera is not False:
    factory.executer.loadConfig('CameraDay')

# recording = Recording('recording', camera, emailer)
# factory.services.append(recording)
# if camera is not False:
#     recording.start()

CameraSensors = Controller.Controller({
    'fan': 6,
    'light': 5,
    'pir': 7,
    'maxFanTime': 60,
    'lowBatteryLightTime': 60,
    'medBatteryLightTime': 180,
    'highBatteryLightTime': 300,
    'spiMosi': 24,
    'spiMiso': 23,
    'spiClk': 18,
    'spiCs': 25,
    'battVoltageCh': 5,
    'battCurrentCh': 7,
    'solarCurrentCh': 6,
    'avgFor': 60,
    'sleepFor': 0.5
}, factory)

CameraSensors.start()

sensors = Sensors('sensors', tempSensor, tempPin, CameraSensors)
factory.services.append(sensors)

sensors.start()

factory.sensors = sensors

parser = Parser(factory.executer)
anotate = TimeAnotate('anotate', camera, sensors, factory, cameraFac, parser)
factory.services.append(anotate)
if camera is not False:
    anotate.start()

host = '88.212.32.71'
port = 8086
user = 'admin'
password = 'RLsT$2017'
dbname = 'sensors'

client = InfluxDBClient(host, port, user, password, dbname)
loop = Loop('Periodic Loop', factory, camera, parser, factory.executer, client)
factory.services.append(loop)

loop.start()

signal.signal(signal.SIGINT, signal_handler)

reactor.listenTCP(9001, factory)
reactor.run()
