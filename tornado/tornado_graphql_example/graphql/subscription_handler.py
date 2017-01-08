# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

from graphql import parse as graphql_parse
from graphql.utils.get_operation_ast import get_operation_ast
from tornado import websocket
from tornado.escape import json_decode, json_encode
from tornado.log import app_log


class GraphQLSubscriptionHandler(websocket.WebSocketHandler):

    @property
    def schema(self):
        raise NotImplementedError('schema must be provided')

    @property
    def sockets(self):
        raise NotImplementedError('sockets() must be implemented')

    @property
    def subscriptions(self):
        raise NotImplementedError('subscriptions() must be implemented')

    @subscriptions.setter
    def subscriptions(self, subscriptions):
        raise NotImplementedError('subscriptions() must be implemented')

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
        if data.get('type') == 'subscription_start':
            self.on_subscribe(subid, data)
        elif data.get('type') == 'subscription_end':
            self.on_unsubscribe(subid, data)
        else:
            raise ValueError('Invalid type: {0}'.format(data.get('type')))

    def on_subscribe(self, subid, data):
        query = data.get('query')
        op_name = self._get_op_name(query)
        app_log.info('subscrption start: subid=%s query=%s op_name=%s',
                     subid, query, op_name)
        if op_name in self.subscriptions:
            del self.subscriptions[op_name]
        self.subscriptions[op_name] = subid
        app_log.debug('subscriptions: %s', self.subscriptions)
        self.write_message(json_encode({
            'type': 'subscription_success',
            'id': subid
        }))

    def on_unsubscribe(self, subid, data):
        app_log.info('subscrption end: subid=%s', subid)
        self.subscriptions = {n: s for n, s in self.subscriptions.items()
                              if s != subid}
        app_log.debug('subscriptions: %s', self.subscriptions)

    def _get_op_name(self, query):
        ast = get_operation_ast(graphql_parse(query))
        return ast.name.value
