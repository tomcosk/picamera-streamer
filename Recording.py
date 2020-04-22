import threading
import logging
import time
import os
import datetime as dt
from BaseThread import BaseThread

class Recording (BaseThread):
    def __init__(self, name, camera, emailer, segmentSize = 300, minDiskSpace = 1500):
        BaseThread.__init__(self)
        self.name = name
        self.camera = camera
        self.segmentSize = segmentSize
        self.minDiskSpace = minDiskSpace
        self.emailer = emailer
        self.isActive = False;

    def run(self):
        self.camera.start_recording(os.path.dirname(os.path.abspath(__file__))+'/1.h264', bitrate=1500000, resize=(1920,1080))
        logging.info('Recording Started')
        self.isActive = True
        s = 0
        numError = 0
        while self.keepRunning:
            if s > self.segmentSize and os.path.isdir("/mnt/automount/tplink"):
                freeSpace = self.checkSpace() / 1000
                filename = '%s.h264' % dt.datetime.now().strftime('%y-%m-%d-%H-%M-%S')
                if freeSpace > self.minDiskSpace:
                    logging.info('Trying to create file: %s' % filename)
                    try:
                        self.camera.split_recording('/mnt/automount/tplink/'+filename)
                        if self.isActive is False:
                            self.emailer.send(
                                'SiravaCam: Recording video is back to normal',
                                ''
                            )
                            self.isActive = True

#                        self.camera.split_recording('./xxx/mnt/automount/tplink/'+filename)
                    except Exception as e:
                        self.isRecording = False
                        self.isActive = False
                        if numError > 11:
                            numError = 0
                        if numError == 0:
                            self.emailer.send(
                                'SiravaCam: Cannot write segment video file',
                                'File was not created. Check if autofs service is running and if it is probably mounted on TPLink router '
                            )
                            logging.exception(dt.datetime.now().strftime('%y-%m-%d-%H-%M-%S')+': cannot create file')
                            numError = numError + 1
                        else:
                            print('cannot create file - email not sent. #'+str(numError))
                            numError = numError + 1

                        self.camera.stop_recording()
                        logging.warning("stopped recording")
                        time.sleep(2)
                        self.camera.start_recording(os.path.dirname(os.path.abspath(__file__))+'/1.h264', bitrate=1500000)
                        logging.warning("started recording again")
                    else:
                        logging.info('Created file: %s' % filename)
                        self.isActive = True
                else:
                    print('Could not create file: %s !! Not enough disk space!!' % filename)

                s = 0
            s = s+1
            time.sleep(1)
        self.camera.stop_recording()
        logging.info("Recording finished")

    def checkSpace(self):
        stat = os.statvfs('/')
        return (stat.f_bsize * stat.f_bavail) / 1024

