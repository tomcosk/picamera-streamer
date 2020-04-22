from autobahn.twisted.websocket import WebSocketServerProtocol
import json
from pprint import pprint
import string
import random
import os
import RPi.GPIO as GPIO
from Config import Config
import logging

logger = logging.getLogger('WebSocket')


class MyServerProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        logger.info("Client connecting: {0}".format(request.peer))
        self.factory.clients.append(self)
        self.authenticated = False
        self.factory.numClients = self.factory.numClients + 1
        self.userId = self.id_generator(size=10)
        self.name = None
        config = Config(os.path.dirname(
            os.path.abspath(__file__))+'/config.ini')
        self.wsPassword = config.getValue('Global', 'websocket_password')

    def onOpen(self):
        pass
#        print("WebSocket connection open.")

    def id_generator(self, size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def onMessage(self, payload, isBinary):
        global cached_img
        if isBinary:
            logger.info(
                "Binary message received: {0} bytes".format(len(payload)))
        else:
            logger.info("Text message received: {0}".format(
                payload.decode('utf8')))

            obj = json.loads(payload.decode('utf8'))
            logger.info(obj['type'])
            msgToSend = ''
            if obj['value'] == 'True':
                obj['value'] = True
            if obj['value'] == 'False':
                obj['value'] = False

            if obj['type'] == 'GET_IMG':
                func = getattr(self.factory.executer, 'getImage')
                imageObj = func()
                data = ''
                if imageObj['image'] is not None:
                    data = imageObj['image'].decode('utf-8')
                msgToSend = json.dumps(
                    {'meta': {'cached': imageObj['cached']}, 'data': data})
                # b64 = func()
                # msgToSend = json.dumps({'meta': {'cached': False}, 'data':b64.decode('utf-8')})
                self.sendMessage(msgToSend.encode('utf-8'))

            elif obj['type'] == 'AUTH':
                logger.info(self.wsPassword)
                if obj['value'] == self.wsPassword:
                    self.authenticated = True
                    logger.info('authenticated')
                else:
                    logger.info('bad password')
                    self.sendClose()

            elif obj['type'] == 'INTRODUCE':
                self.name = obj['value']
                msg = {
                    'type': 'USER_JOIN_STATUS',
                    'value': {'status': 'OK', 'user': {'id': self.userId, 'name': self.name, 'authenticated': self.authenticated}}
                }
                msgToSend = json.dumps(msg)
                self.sendMessage(msgToSend.encode('utf-8'))

                msg = {
                    'type': 'USERJOIN',
                    'value': {'user': {'id': self.userId, 'name': self.name, 'authenticated': self.authenticated}}
                }
                msgToSend = json.dumps(msg)
                for client in self.factory.clients:
                    client.sendMessage(msgToSend.encode('utf-8'))

            elif obj['type'] == 'TOGGLE':
                if self.authenticated is True:
                    if obj['set'] == 'PIN':
                        func = getattr(self.factory.executer, 'setPin')
                        func(obj['pinNum'], obj['value'])
                        # time.sleep(0.5)
                        msgToSend = {'type': 'pinset', 'pinNum': int(
                            obj['pinNum']), 'value': GPIO.input(int(obj['pinNum']))}
                        self.sendMessage(json.dumps(msgToSend).encode('utf-8'))

            elif obj['type'] == 'STATUS':
                services = {}
                for item in self.factory.services:
                    services[item.name] = item.isActive
                msgToSend = json.dumps(services)
                self.sendMessage(msgToSend.encode('utf-8'))

            elif obj['type'] == 'BUTTON':
                if self.authenticated is True:
                    if obj['set'] == 'LOAD_CONFIG':
                        func = getattr(self.factory.executer, 'loadConfig')
                        func(obj['value'])
                        func = getattr(self.factory.executer, 'init')
                        msgToSend = func()
                        self.sendMessage(msgToSend.encode('utf-8'))
                    if obj['set'] == 'CAPTURE':
                        self.factory.executer.blurImage(obj['value'])

                else:
                    self.sendClose()

            elif obj['type'] == 'INIT':
                func = getattr(self.factory.executer, 'init')
                msgToSend = func()
                logger.info(msgToSend)
                self.sendMessage(msgToSend.encode('utf-8'))

            else:
                if self.authenticated is True:
                    func = getattr(self.factory.executer, 'do')
                    func(obj['id'], obj['value'])
                else:
                    self.sendClose()

    def onClose(self, wasClean, code, reason):
        logger.info("WebSocket connection closed: {0}".format(reason))

    def connectionLost(self, reason):
        logger.info('connection lost: '+reason.getErrorMessage())
        self.factory.numClients = self.factory.numClients - 1
        self.factory.clients.remove(self)
        msg = {
            'type': 'USER_LEFT',
            'value': self.userId
        }
        msgToSend = json.dumps(msg)
        for client in self.factory.clients:
            if self.name is not None:
                client.sendMessage(msgToSend.encode('utf-8'))
