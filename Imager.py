from pprint import pprint
import threading
import time
import datetime as dt
import base64
from PIL import Image, ImageFilter
from BaseThread import BaseThread
import logging

logger = logging.getLogger('Imager')


class Imager (BaseThread):
    def __init__(self, name, camera, cameraFactory, seconds=5):
        BaseThread.__init__(self)
        self.name = name
        self.camera = camera
        self.blurTimeOut = False
        self.b64Image = None
        self.keepRunning = True
        self.lastCapture = dt.datetime.now()
        self.cameraFactory = cameraFactory
        self.seconds = seconds
        self.imageObj = {
            'cached': True,
            'image': None
        }
        self.needImg = True

    def getImage(self):
        self.needImg = True

        logger.info(
            'Image served with cached data' if self.imageObj['cached'] else 'Image served with fresh data')
        return self.imageObj

    def disable(self, time):
        self.blurTimeOut = dt.datetime.now() + dt.timedelta(minutes=int(time))
        print(self.blurTimeOut)

    def CaptureImage(self):
        if dt.datetime.now() > self.lastCapture + dt.timedelta(seconds=self.seconds):
            try:
                self.camera.capture(
                    'capture.jpg', use_video_port=True, splitter_port=0)
                bg = Image.open('capture.jpg', 'r')
                if self.blurTimeOut is not False:
                    if dt.datetime.now() < self.blurTimeOut:
                        logger.info('bluring image')
                        bg = bg.filter(ImageFilter.GaussianBlur(radius=15))
                    else:
                        self.blurTimeOut = False
                bg_w, bg_h = bg.size

                logo = Image.open('logo-plavba.png', 'r')
                logo_w, logo_h = logo.size
    #            offset = (int((bg_w - logo_w)-20), int((bg_h - logo_h)-50))
                offset = (int((bg_w - logo_w)-20), 50)

                bg.paste(logo, offset, mask=logo)
                bg.save('out.jpg')

                with open("out.jpg", "rb") as imageFile:
                    self.b64Image = base64.b64encode(imageFile.read())
                self.lastCapture = dt.datetime.now()
                cached = False
            except Exception as e:
                logger.error('cannot capture image')
                logger.error(e)
                cached = True
        else:
            cached = True

        self.imageObj = {
            'cached': cached,
            'image': self.b64Image
        }
        self.needImg = False

    def run(self):
        logger.info('Image processing started')
        self.isActive = True
        while self.keepRunning:
            if self.needImg:
                self.CaptureImage()
            time.sleep(1)
        self.isActive = False
        logger.info("Image processing finished")
