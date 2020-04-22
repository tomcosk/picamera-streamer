import time
import datetime as dt
import picamera
from BaseThread import BaseThread
import logging

logger = logging.getLogger('Anotation')


class TimeAnotate (BaseThread):
    def __init__(self, name, camera, sensors, factory, cameraFactory, parser):
        BaseThread.__init__(self)
        self.name = name
        self.camera = camera
        self.factory = factory
        self.sensors = sensors
        self.keepRunning = True
        self.cameraFactory = cameraFactory
        self.parser = parser

    def run(self):
        logger.info('anotation started')
        self.isActive = True
        self.camera.annotate_background = picamera.Color('black')
        self.camera.annotate_text_size = 32
        start = dt.datetime.now()
        global keep_running
        while self.keepRunning:
            self.parser.parsePovodia()
            hladina = self.parser.getHladina()

            try:
                logger.debug('trying to anotate')
                self.camera.annotate_text = dt.datetime.now().strftime('%d.%m.%Y %H:%M:%S') + ' ' + str(round(self.sensors.temperature, 1)) + \
                    'C' + ' '+str(round(self.sensors.humidity)) + '% ' + \
                    str(hladina)+' mnm' + ' #'+str(len(self.factory.clients))
            except Exception as e:
                # self.cameraFactory.camera.close()
                # self.cameraFactory.createCamera()
                # self.camera = self.cameraFactory.camera
                logger.error('Annotation failed')
                logger.error(e)
            time.sleep(1)
        self.isActive = False
        logger.info("Annotation finished")
