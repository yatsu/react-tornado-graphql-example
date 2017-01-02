# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from tornado import websocket
from tornado.escape import json_decode, json_encode
from tornado.log import app_log


class GraphQLSubscriptionHandler(websocket.WebSocketHandler):

    def initialize(self, sockets, subscriptions):
        self._sockets = sockets
        self._subscriptions = subscriptions

    @property
    def sockets(self):
        return self._sockets

    @property
    def subscriptions(self):
        return self._subscriptions.get(self, {})

    @subscriptions.setter
    def subscriptions(self, subscriptions):
        self._subscriptions[self] = subscriptions

    def select_subprotocol(self, subprotocols):
        return 'graphql-subscriptions'

    def open(self):
        app_log.info('open socket %s', self)
        self.sockets.append(self)
        self.subscriptions = {}

    def on_close(self):
        app_log.info('close socket %s', self)
        self.sockets.remove(self)
        self.subscriptions = {}

    def on_message(self, message):
        data = json_decode(message)
        subid = data.get('id')
        # app_log.debug('data: %s', data)

        if data.get('type') == 'subscription_start':
            self.on_subscribe(subid, data)
        elif data.get('type') == 'subscription_end':
            self.on_unsubscribe(subid, data)
        else:
            raise ValueError('Invalid type: {0}'.format(data.get('type')))

    def on_subscribe(self, subid, data):
        query = data.get('query')
        app_log.info('subscrption start: subid=%s query=%s', subid, query)
        if 'todos' in self.subscriptions:
            del self.subscriptions['todos']
        self.subscriptions['todos'] = subid
        app_log.info('subsciptions: %s', self.subscriptions)
        self.write_message(json_encode({
            'type': 'subscription_success',
            'id': subid
        }))

    def on_unsubscribe(self, subid, data):
        app_log.info('subscrption end: subid=%s', subid)
        if 'todos' in self.subscriptions:
            del self.subscriptions['todos']
        app_log.info('subsciptions: %s', self.subscriptions)
