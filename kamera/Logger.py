import time
import datetime


class Logger:
    def __init__(self, format):
        self.fmt = format

    def log(self, comment):
        logTime = time.strftime(self.fmt, time.localtime())
        print('['+str(logTime)+'] - ' + comment)