# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from tornado import websocket
from tornado.escape import json_decode, json_encode
from tornado.log import app_log


class GraphQLSubscriptionHandler(websocket.WebSocketHandler):

    def initialize(self, sockets):
        self._sockets = sockets
        self.subscriptions = {}

    @property
    def sockets(self):
        return self._sockets

    def select_subprotocol(self, subprotocols):
        return 'graphql-subscriptions'

    def open(self):
        app_log.info('open socket %s', self)
        self.sockets.append(self)

    def on_close(self):
        app_log.info('close socket %s', self)
        self.sockets.remove(self)

    def on_message(self, message):
        data = json_decode(message)
        subid = data.get('id')
        # app_log.debug('data: %s', data)
        if data.get('type') == 'subscription_start':
            query = data.get('query')
            app_log.info('subscrption start: subid=%d query=%s', subid, query)
            self.subscriptions[subid] = subid
            app_log.info('subsciptions: %s', self.subscriptions)
            self.write_message(json_encode({
                'type': 'subscription_success',
                'id': subid
            }))
        elif data.get('type') == 'subscription_end':
            app_log.info('subscrption end: subid=%d', subid)
            del self.subscriptions[subid]
            app_log.info('subsciptions: %s', self.subscriptions)
        else:
            raise ValueError('Invalid type: {0}'.format(data.get('type')))
