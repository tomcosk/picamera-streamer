import threading
import time
import logging
import datetime as dt
import base64
import os
from PIL import Image, ImageFilter
from BaseThread import BaseThread
##########################################
# was crashing. do not use this approach #
##########################################


class Imager (threading.Thread):
    def __init__(self, name, camera, lastCapture, blured=False):
        # print('imagerNew INIT')
        threading.Thread.__init__(self)
        self.name = name
        self.camera = camera
        self.blured = blured
        self.blurTimeOut = False
        self.b64Image = ''
        self.imageObj = {
            'cached': True,
            'image': None
        }
        self.keepRunning = True
        self.lastCapture = lastCapture
        self.logger = logging.getLogger('ImagerNew')

    def disable(self, time):
        if time is not False:
            self.blurTimeOut = dt.datetime.now() + dt.timedelta(minutes=int(time))

    def getImage(self):
        if dt.datetime.now() > self.lastCapture + dt.timedelta(seconds=3):
            # print('Getting fresh image')
            try:
                self.camera.capture(os.path.dirname(os.path.abspath(
                    __file__))+'/capture.jpg', use_video_port=False, splitter_port=0)
                bg = Image.open(os.path.dirname(
                    os.path.abspath(__file__))+'/capture.jpg', 'r')
                if self.blured is not False:
                    bg = bg.filter(ImageFilter.GaussianBlur(radius=15))
                bg_w, bg_h = bg.size

                logo = Image.open(os.path.dirname(
                    os.path.abspath(__file__))+'/logo-plavba.png', 'r')
                logo_w, logo_h = logo.size
    #            offset = (int((bg_w - logo_w)-20), int((bg_h - logo_h)-50))
                offset = (int((bg_w - logo_w)-20), 50)

                bg.paste(logo, offset, mask=logo)
                self.logger.debug('ImagerNew: Saving')
                bg.save('out.jpg')
                self.logger.debug('ImagerNew: Saved')

                with open("out.jpg", "rb") as imageFile:
                    self.logger.debug('ImagerNew: base64 encoding')
                    self.b64Image = base64.b64encode(imageFile.read())
                self.lastCapture = dt.datetime.now()
                cached = False
            except Exception as e:
                self.logger.error('cannot capture image', e)
                self.b64Image = ''
                cached = True
        else:
            cached = True
            self.b64Image = ''

        self.logger.info(
            'Image served with cached data' if cached else 'Image served with fresh data')
        if self.b64Image == '':
            image = None
        else:
            image = self.b64Image

        self.imageObj = {
            'cached': cached,
            'image': image
        }

    def run(self):
        self.logger.debug('Start')
        self.getImage()
        self.logger.debug('End')
