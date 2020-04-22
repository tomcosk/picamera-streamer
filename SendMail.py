import smtplib
import os
from Config import Config

class sendMail():
    def __init__(self, to, subject, msg):
        self.to = to
        self.subject = subject
        self.msg = msg
        config = Config(os.path.dirname(os.path.abspath(__file__))+'/config.ini')
        self.server = config.getValue('Email', 'server')
        self.port = config.getValue('Email', 'port')
        self.username = config.getValue('Email', 'username')
        self.password = config.getValue('Email', 'password')


    def send(self, subject=None, msg=None):
        if subject is None:
            SUBJECT = self.subject
        else: 
            SUBJECT = subject
        if msg is None:
            TEXT = self.msg
        else:
            TEXT = msg
        TO = self.to

        # Gmail Sign In

        try:
            server = smtplib.SMTP_SSL(self.server, self.port)
            server.login(self.username, self.passwd)

            BODY = '\r\n'.join(['To: %s' % TO,
                            'From: %s' % username,
                            'Subject: %s' % SUBJECT,
                            '', TEXT])

            server.sendmail(username, [TO], BODY)
            server.quit()
            print ('email sent')
        except Exception as e:
            print ('error sending mail', e)

