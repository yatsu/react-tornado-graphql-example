# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import json
from tornado import web
from tornado.log import app_log
import os
import zmq
from zmq.eventloop.zmqstream import ZMQStream
from .cors import CORSRequestHandler
from .graphql import GraphQLHandler, GraphQLSubscriptionHandler
from .schema import Schema


class ExampleAPIHandler(CORSRequestHandler, GraphQLHandler):

    def initialize(self, opts):
        self.opts = opts

    @property
    def sockets(self):
        return self.opts['sockets']

    @property
    def schema(self):
        return Schema


class SubscriptionHandler(GraphQLSubscriptionHandler):

    def initialize(self, opts):
        GraphQLSubscriptionHandler.initialize(self, opts['sockets'])
        self.opts = opts

    def check_origin(self, origin):
        return True


class CommandHandler(CORSRequestHandler, web.RequestHandler):

    def initialize(self, opts):
        self.opts = opts

    @property
    def servers(self):
        return self.opts['servers']

    @property
    def index(self):
        return self.opts['index']

    @index.setter
    def index(self, index):
        self.opts['index'] = index

    @web.asynchronous
    def post(self):
        self.set_header('Content-Type', 'application/json')

        server = self.servers[self.index]
        self.index = (self.index + 1) % len(self.servers)

        context = zmq.Context.instance()
        sock = context.socket(zmq.DEALER)
        sock.linger = 1000
        sock.identity = bytes(str(os.getpid()), 'ascii')
        ip = server['ip']
        if ip == '*':
            ip = 'localhost'
        url = 'tcp://{0}:{1}'.format(ip, server['zmq_port'])
        app_log.info('connect %s', url)
        sock.connect(url)

        command = json.dumps({'command': self.get_argument('command')})
        app_log.info('command: %s', command)
        sock.send(bytes(command, 'ascii'))

        stream = ZMQStream(sock)
        stream.on_recv(self.response_handler(sock))

    def response_handler(self, stream):
        def handler(msg):
            response = msg[0]
            app_log.info('response: %s', response)
            self.write(response)
            stream.close()
            self.finish()

        return handler


class ExampleWebAPIApplication(web.Application):

    def __init__(self, settings, job_servers):
        app_log.info('job_servers: %s', [s['pid'] for s in job_servers])

        self.command_opts = {
            'servers': job_servers,
            'index': 0
        }

        self.websocket_opts = {
            'sockets': []
        }

        handlers = [
            (r'/', SubscriptionHandler, dict(opts=self.websocket_opts)),
            (r'/graphql', ExampleAPIHandler, dict(opts=self.websocket_opts)),
            (r'/command', CommandHandler, dict(opts=self.command_opts))
        ]

        super(ExampleWebAPIApplication, self).__init__(handlers, **settings)
