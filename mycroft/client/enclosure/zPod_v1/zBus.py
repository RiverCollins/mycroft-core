from threading import Thread
import json
import logging
import uuid
from wsgiref import simple_server
from mycroft.util.log import LOG

import falcon

class zBus(Thread):
    def __init__(self):
        super(zBus, self).__init__(target=self.startBus)
        LOG.debug("zBus started")
        self.alive = True
        self.port = 8100
        self.app = falcon.API()
        self.start()

    def startBus(self):
        test = Routes()
        httpd = simple_server.make_server('127.0.0.1', self.port, test)
        httpd.serve_forever()

    def routes(self):
        self.app.add_route('/test', self.routes)

class Routes():
    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.body = ('\nTest works\n')
        LOG.debug("zBus Test works")