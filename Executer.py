import RPi.GPIO as GPIO
import os
import json
import base64
from ImagerNew import Imager as ImagerNew
from PIL import Image, ImageFilter
import datetime as dt
import logging
import threading

try:
    import queue
except ImportError:
    import Queue as queue

logger = logging.getLogger('Executer')


class Executer():
    def __init__(self, camera, config, imager):
        global b64Image
        self.camera = camera
        self.imager = imager
        self.lastCapture = dt.datetime.now()
        self.blurTimeOut = False
        self.base64 = ''
        self.config = config
        self.intList = [
            'brightness',
            'saturation',
            'contrast',
            'shutter_speed',
            'sharpness',
            'iso',
            'awb_gains'
        ]

        self.strList = [
            'image_effect',
            'exposure_mode',
            'meter_mode',
            'awb_mode'
        ]

        self.imageObj = {
            'cached': True,
            'image': None
        }

        self.threads = []

    def setPin(self, pinNum, value):
        logger.info('setting pin '+str(pinNum)+' to '+str(value))
        GPIO.setup(int(pinNum), GPIO.OUT)
        GPIO.output(int(pinNum), bool(value))

    def do(self, command, value):
        if command in self.intList:
            value = int(value)
        setattr(self.camera, command, value)

    def blurImage(self, time):
        self.blurTimeOut = dt.datetime.now() + dt.timedelta(minutes=int(time))

    # def getImage(self):
    #     blured = False
    #     if self.blurTimeOut is not False and dt.datetime.now() < self.blurTimeOut:
    #         blured = True
    #     # print('Getting image')
    #     t1 = ImagerNew('imager', self.camera, self.lastCapture, blured=blured)
    #     t1.start()
    #     logger.debug('getImage joining')
    #     t1.join()
    #     logger.debug('getImage joined')

    #     if t1.imageObj['cached'] is False:
    #         self.lastCapture = dt.datetime.now()
    #     return t1.imageObj
    #     # return {
    #     #     'cached': True,
    #     #     'image': None
    #     #     }

    def getImage(self):
        # blured = False
        # if self.blurTimeOut is not False and dt.datetime.now() < self.blurTimeOut:
        #     blured = True

        # myqueue = queue.Queue()
        # logger.info('creating thread')
        # t = threading.Thread(target=self.captureImage, args=[myqueue])
        # self.threads.append(t)
        # logger.info('starting thread')
        # t.start()
        # for t in self.threads:
        #     logger.info('joining thread')
        #     t.join()

        # # for th in self.threads:
        # #     if not th.isAlive():
        # #         self.threads.remove(th)

        # logger.info('NUM THREADS: '+str(len(self.threads)))
        # # logger.info('joined thread')
        # # try:
        # #     imgobj = myqueue.get(block=False)
        # #     self.imageObj = imgobj
        # #     print('have img')
        # # except queue.Empty:  # Queue here refers to the  module, not a class
        # #     print('dont have img')
        # # # logging.info(imgobj)
        # # th.join()
        # return self.imageObj
        return self.imager.getImage()
        # print('Getting image')
        # return {
        #     'cached': True,
        #     'image': None
        #     }

    def captureImage(self, outqueue):
        blured = False
        if self.blurTimeOut is not False and dt.datetime.now() < self.blurTimeOut:
            blured = True
        if dt.datetime.now() > self.lastCapture + dt.timedelta(seconds=3):
            # print('Getting fresh image')
            logger.info('capturing FRESH image')
            try:
                self.camera.capture(os.path.dirname(os.path.abspath(
                    __file__))+'/capture.jpg', use_video_port=False, splitter_port=0)
                bg = Image.open(os.path.dirname(
                    os.path.abspath(__file__))+'/capture.jpg', 'r')
                if blured is not False:
                    bg = bg.filter(ImageFilter.GaussianBlur(radius=15))
                bg_w, bg_h = bg.size

                logo = Image.open(os.path.dirname(
                    os.path.abspath(__file__))+'/logo-plavba.png', 'r')
                logo_w, logo_h = logo.size
    #            offset = (int((bg_w - logo_w)-20), int((bg_h - logo_h)-50))
                offset = (int((bg_w - logo_w)-20), 50)

                bg.paste(logo, offset, mask=logo)
                logger.info('ImagerNew: Saving')
                bg.save('out.jpg')
                logger.info('ImagerNew: Saved')

                with open("out.jpg", "rb") as imageFile:
                    logger.info('ImagerNew: base64 encoding')
                    self.b64Image = base64.b64encode(imageFile.read())
                self.lastCapture = dt.datetime.now()
                cached = False
            except Exception as e:
                logger.error('cannot capture image')
                self.b64Image = ''
                cached = True
        else:
            logger.info('serving CACHED image')
            cached = True
            self.b64Image = ''

        logger.info(
            'Image served with cached data' if cached else 'Image served with fresh data')
        if self.b64Image == '':
            image = None
        else:
            image = self.b64Image

        self.imageObj = {
            'cached': cached,
            'image': image
        }

        # return {
        #     'cached': cached,
        #     'image': image
        # }

    def loadConfig(self, section):
        print(section)
        if self.camera is not False:
            for key in self.config.config[section]:
                if key in self.intList:
                    setattr(self.camera, key, int(
                        self.config.getValue(section, key)))
                else:
                    setattr(self.camera, key, str(
                        self.config.getValue(section, key)))
        else:
            logger.info('camera is not working')

    def init(self):
        values = []
        GPIO.setup(16, GPIO.OUT)
        GPIO.setup(13, GPIO.OUT)
        GPIO.setup(5, GPIO.OUT)
        GPIO.setup(6, GPIO.OUT)
        GPIO.setup(17, GPIO.OUT)
        pins = {
            '16': GPIO.input(16),
            '13': GPIO.input(13),
            '5': GPIO.input(5),
            '6': GPIO.input(6),
            '17': GPIO.input(17)
        }
        if self.camera is not False:
            for key in self.intList:
                values.append(
                    {'key': key, 'value': str(getattr(self.camera, key))})

            for key in self.strList:
                values.append(
                    {'key': key, 'value': str(getattr(self.camera, key))})

            return json.dumps({
                'type': 'init',
                'status': {
                        'code': 200,
                        'text': 'OK'
                },
                'values': values,
                'pins': pins
            })
        else:
            return json.dumps({
                'type': 'init',
                'status': {
                        'code': 500,
                        'text': 'Camera not working'
                },
                'values': values,
                'pins': pins
            })
